"""Intervention model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Intervention(Base):
    """Care intervention/task model"""
    __tablename__ = "interventions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="SET NULL"), index=True)
    intervention_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, index=True)
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    due_date = Column(DateTime, index=True)
    completed_at = Column(DateTime)
    outcome_notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'cancelled')", name="chk_intervention_status"),
    )

    # Relationships
    patient = relationship("Patient", back_populates="interventions")
    encounter = relationship("Encounter", back_populates="interventions")
    assigned_to = relationship("User", back_populates="interventions_assigned", foreign_keys=[assigned_to_id])
