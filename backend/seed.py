"""Seed database with test data"""
import asyncio
from uuid import uuid4
from datetime import date
from sqlalchemy import select
from app.database import Base, engine, AsyncSessionLocal
from app.models.user import User
from app.models.ward import Ward
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.risk_prediction import RiskPrediction
from app.models.model_version import ModelVersion
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as db:
        check = await db.execute(select(User).limit(1))
        if check.scalar_one_or_none():
            print("Already seeded")
            return
        
        w1 = Ward(id=uuid4(), name="Ward A", location="Building 1", capacity=30)
        w2 = Ward(id=uuid4(), name="Ward B", location="Building 2", capacity=40)
        db.add_all([w1, w2])
        await db.flush()
        
        users = [
            User(id=uuid4(), email="nurse1@hospital.org", password_hash=pwd.hash("demo123"), first_name="Jane", last_name="Nurse", role="nurse", is_active=True, ward_id=w1.id),
            User(id=uuid4(), email="doctor1@hospital.org", password_hash=pwd.hash("demo123"), first_name="John", last_name="Doctor", role="doctor", is_active=True, ward_id=w1.id),
            User(id=uuid4(), email="admin@hospital.org", password_hash=pwd.hash("demo123"), first_name="Admin", last_name="User", role="admin", is_active=True),
        ]
        db.add_all(users)
        
        mv = ModelVersion(id=uuid4(), version_name="v1.0", model_type="xgboost", is_active=True)
        db.add(mv)
        await db.flush()
        
        for i in range(50):
            p = Patient(
                id=uuid4(), mrn=f"MRN{str(i).zfill(6)}",
                first_name=f"Patient{i}", last_name=f"Test{i}",
                date_of_birth=date(1960 + (i % 40), (i % 12) + 1, (i % 28) + 1),
                gender="male" if i % 2 == 0 else "female",
                phone=f"555-{str(i).zfill(4)}",
                current_ward_id=w1.id if i % 2 == 0 else w2.id
            )
            db.add(p)
            await db.flush()
            
            if i < 30:
                e = Encounter(id=uuid4(), patient_id=p.id, encounter_type="inpatient")
                db.add(e)
                await db.flush()
                
                risk_score = 30 + (i * 1.5)
                band = "high" if risk_score >= 60 else ("medium" if risk_score >= 40 else "low")
                rp = RiskPrediction(
                    id=uuid4(), patient_id=p.id, encounter_id=e.id,
                    risk_score=risk_score, risk_band=band,
                    confidence_lower=max(0, risk_score-10),
                    confidence_upper=min(100, risk_score+10),
                    model_version_id=mv.id
                )
                db.add(rp)
        
        await db.commit()
        print("✅ Seeded: 3 users, 2 wards, 50 patients, 30 encounters")
        print("Login: nurse1@hospital.org / demo123")

if __name__ == "__main__":
    asyncio.run(seed())
