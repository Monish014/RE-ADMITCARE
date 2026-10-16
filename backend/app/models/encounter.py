"""Encounter model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Encounter(Base):
    """Patient encounter (admission) model"""
    __tablename__ = "encounters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_type = Column(String(50), nullable=False, index=True)
    admission_date = Column(DateTime, nullable=False, index=True)
    discharge_date = Column(DateTime, index=True)
    admitting_provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    discharging_provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    discharge_disposition = Column(String(100))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("encounter_type IN ('inpatient', 'outpatient', 'emergency', 'observation')", name="chk_encounter_type"),
        CheckConstraint("discharge_date IS NULL OR discharge_date >= admission_date", name="chk_discharge_after_admission"),
    )

    # Relationships
    patient = relationship("Patient", back_populates="encounters")
    admitting_provider = relationship("User", back_populates="encounters_as_admitting", foreign_keys=[admitting_provider_id])
    discharging_provider = relationship("User", back_populates="encounters_as_discharging", foreign_keys=[discharging_provider_id])
    diagnoses = relationship("Diagnosis", back_populates="encounter", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="encounter")
    lab_results = relationship("LabResult", back_populates="encounter")
    social_screenings = relationship("SocialScreening", back_populates="encounter")
    risk_predictions = relationship("RiskPrediction", back_populates="encounter", cascade="all, delete-orphan")
    interventions = relationship("Intervention", back_populates="encounter")
    follow_up_contacts = relationship("FollowUpContact", back_populates="encounter")
    outcomes = relationship("Outcome", back_populates="encounter", foreign_keys="[Outcome.encounter_id]", cascade="all, delete-orphan")
