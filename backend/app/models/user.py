"""User model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, index=True)
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="SET NULL"), index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("role IN ('nurse', 'doctor', 'social_worker', 'admin')", name="chk_user_role"),
    )

    # Relationships
    ward = relationship("Ward", back_populates="users", foreign_keys=[ward_id])
    patients_as_provider = relationship("Patient", back_populates="primary_provider", foreign_keys="[Patient.primary_provider_id]")
    encounters_as_admitting = relationship("Encounter", back_populates="admitting_provider", foreign_keys="[Encounter.admitting_provider_id]")
    encounters_as_discharging = relationship("Encounter", back_populates="discharging_provider", foreign_keys="[Encounter.discharging_provider_id]")
    medications_prescribed = relationship("Medication", back_populates="prescribing_provider", foreign_keys="[Medication.prescribing_provider_id]")
    social_screenings = relationship("SocialScreening", back_populates="screened_by", foreign_keys="[SocialScreening.screened_by_id]")
    interventions_assigned = relationship("Intervention", back_populates="assigned_to", foreign_keys="[Intervention.assigned_to_id]")
    follow_up_contacts = relationship("FollowUpContact", back_populates="contacted_by", foreign_keys="[FollowUpContact.contacted_by_id]")
    notifications = relationship("Notification", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
