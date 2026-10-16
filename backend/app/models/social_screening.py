"""Social screening model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class SocialScreening(Base):
    """Social determinants of health screening model"""
    __tablename__ = "social_screenings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="SET NULL"), index=True)
    housing_stability_score = Column(Integer)
    food_security_score = Column(Integer)
    transportation_access_score = Column(Integer)
    social_support_score = Column(Integer)
    notes = Column(Text)
    screened_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    screened_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("housing_stability_score BETWEEN 1 AND 5 OR housing_stability_score IS NULL", name="chk_housing_score"),
        CheckConstraint("food_security_score BETWEEN 1 AND 5 OR food_security_score IS NULL", name="chk_food_score"),
        CheckConstraint("transportation_access_score BETWEEN 1 AND 5 OR transportation_access_score IS NULL", name="chk_transport_score"),
        CheckConstraint("social_support_score BETWEEN 1 AND 5 OR social_support_score IS NULL", name="chk_social_score"),
    )

    # Relationships
    patient = relationship("Patient", back_populates="social_screenings")
    encounter = relationship("Encounter", back_populates="social_screenings")
    screened_by = relationship("User", back_populates="social_screenings", foreign_keys=[screened_by_id])
