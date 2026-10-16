"""API routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from datetime import datetime, timedelta
from uuid import uuid4
import random
from .database import get_db
from .auth import get_current_user, verify_password, get_password_hash, create_access_token
from .models.user import User
from .models.patient import Patient
from .models.encounter import Encounter
from .models.risk_prediction import RiskPrediction
from . import schemas

router = APIRouter(prefix="/api")

@router.post("/auth/register", response_model=schemas.Token)
async def register(user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email exists")
    user = User(
        id=uuid4(),
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": user}

@router.post("/auth/login", response_model=schemas.Token)
async def login(creds: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == creds.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(creds.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": user}

@router.get("/auth/me", response_model=schemas.UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user

@router.get("/patients", response_model=schemas.PatientList)
async def list_patients(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    query = select(Patient)
    if search:
        query = query.where(
            (Patient.first_name.ilike(f"%{search}%")) |
            (Patient.last_name.ilike(f"%{search}%")) |
            (Patient.mrn.ilike(f"%{search}%"))
        )
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    patients = result.scalars().all()
    patients_with_risk = []
    for p in patients:
        risk_q = select(RiskPrediction).where(RiskPrediction.patient_id == p.id).order_by(desc(RiskPrediction.predicted_at)).limit(1)
        risk_r = await db.execute(risk_q)
        risk = risk_r.scalar_one_or_none()
        patients_with_risk.append({
            **p.__dict__,
            "current_risk_score": float(risk.risk_score) if risk else None,
            "risk_band": risk.risk_band if risk else None
        })
    return {"items": patients_with_risk, "total": total, "page": page, "limit": limit}

@router.post("/patients", response_model=schemas.PatientResponse, status_code=201)
async def create_patient(data: schemas.PatientCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Patient).where(Patient.mrn == data.mrn))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="MRN exists")
    p = Patient(id=uuid4(), **data.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p

@router.get("/patients/{patient_id}", response_model=schemas.PatientResponse)
async def get_patient(patient_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    return p

@router.get("/dashboard/stats", response_model=schemas.DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    total_p = await db.execute(select(func.count(Patient.id)))
    active_e = await db.execute(select(func.count(Encounter.id)).where(Encounter.discharge_date.is_(None)))
    high_r = await db.execute(select(func.count(RiskPrediction.id)).where(RiskPrediction.risk_band == "high"))
    avg_r = await db.execute(select(func.avg(RiskPrediction.risk_score)))
    return {
        "total_patients": total_p.scalar() or 0,
        "active_encounters": active_e.scalar() or 0,
        "high_risk_count": high_r.scalar() or 0,
        "avg_risk_score": round(float(avg_r.scalar() or 0), 1)
    }

@router.get("/health")
async def health():
    return {"status": "healthy"}
