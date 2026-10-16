"""Follow-up contact model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class FollowUpContact(Base):
    """Patient follow-up contact tracking model"""
    __tablename__ = "follow_up_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="SET NULL"), index=True)
    contact_method = Column(String(50), nullable=False)
    contact_outcome = Column(String(100), nullable=False)
    notes = Column(Text)
    contacted_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    contact_date = Column(DateTime, nullable=False, index=True)
    next_contact_date = Column(DateTime, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("contact_method IN ('phone', 'email', 'sms', 'in_person', 'video')", name="chk_contact_method"),
        CheckConstraint("contact_outcome IN ('successful', 'no_answer', 'left_message', 'wrong_number', 'refused')", name="chk_contact_outcome"),
    )

    # Relationships
    patient = relationship("Patient", back_populates="follow_up_contacts")
    encounter = relationship("Encounter", back_populates="follow_up_contacts")
    contacted_by = relationship("User", back_populates="follow_up_contacts", foreign_keys=[contacted_by_id])
