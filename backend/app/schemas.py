"""Pydantic schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str
    last_name: str
    role: str = "nurse"

class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class PatientCreate(BaseModel):
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str

class PatientResponse(BaseModel):
    id: UUID
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class PatientWithRisk(PatientResponse):
    current_risk_score: Optional[float] = None
    risk_band: Optional[str] = None

class PatientList(BaseModel):
    items: List[PatientWithRisk]
    total: int
    page: int
    limit: int

class DashboardStats(BaseModel):
    total_patients: int
    active_encounters: int
    high_risk_count: int
    avg_risk_score: float
