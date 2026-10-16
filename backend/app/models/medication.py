"""Medication model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Medication(Base):
    """Patient medication model"""
    __tablename__ = "medications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="SET NULL"), index=True)
    name = Column(String(200), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    route = Column(String(50))
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, index=True)
    prescribing_provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("route IN ('oral', 'IV', 'topical', 'injection', 'inhalation', 'other')", name="chk_medication_route"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="chk_end_after_start"),
    )

    # Relationships
    patient = relationship("Patient", back_populates="medications")
    encounter = relationship("Encounter", back_populates="medications")
    prescribing_provider = relationship("User", back_populates="medications_prescribed", foreign_keys=[prescribing_provider_id])
