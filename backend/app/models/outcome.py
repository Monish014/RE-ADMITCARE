"""Outcome model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Boolean, Integer, DateTime, ForeignKey, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Outcome(Base):
    """Patient outcome tracking model"""
    __tablename__ = "outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False, index=True)
    readmitted = Column(Boolean, nullable=False, index=True)
    readmission_date = Column(DateTime)
    readmission_encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="SET NULL"))
    days_to_readmission = Column(Integer)
    readmission_reason = Column(Text)
    outcome_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "(readmitted = false AND readmission_date IS NULL AND days_to_readmission IS NULL) OR "
            "(readmitted = true AND readmission_date IS NOT NULL AND days_to_readmission IS NOT NULL)",
            name="chk_readmission_consistency"
        ),
        UniqueConstraint("encounter_id", name="idx_outcomes_encounter_unique"),
    )

    # Relationships
    patient = relationship("Patient", back_populates="outcomes")
    encounter = relationship("Encounter", back_populates="outcomes", foreign_keys=[encounter_id])
    readmission_encounter = relationship("Encounter", foreign_keys=[readmission_encounter_id])
