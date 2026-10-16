"""Patient model"""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Patient(Base):
    """Patient model"""
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mrn = Column(String(50), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False, index=True)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20))
    phone = Column(String(20))
    email = Column(String(255))
    address = Column(Text)
    current_ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="SET NULL"), index=True)
    primary_provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("gender IN ('male', 'female', 'other', 'unknown')", name="chk_patient_gender"),
        CheckConstraint("date_of_birth < CURRENT_DATE", name="chk_dob_past"),
    )

    # Relationships
    current_ward = relationship("Ward", back_populates="patients", foreign_keys=[current_ward_id])
    primary_provider = relationship("User", back_populates="patients_as_provider", foreign_keys=[primary_provider_id])
    encounters = relationship("Encounter", back_populates="patient", cascade="all, delete-orphan")
    diagnoses = relationship("Diagnosis", back_populates="patient", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    lab_results = relationship("LabResult", back_populates="patient", cascade="all, delete-orphan")
    social_screenings = relationship("SocialScreening", back_populates="patient", cascade="all, delete-orphan")
    risk_predictions = relationship("RiskPrediction", back_populates="patient", cascade="all, delete-orphan")
    interventions = relationship("Intervention", back_populates="patient", cascade="all, delete-orphan")
    follow_up_contacts = relationship("FollowUpContact", back_populates="patient", cascade="all, delete-orphan")
    outcomes = relationship("Outcome", back_populates="patient", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="patient", cascade="all, delete-orphan")
