"""Lab result model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class LabResult(Base):
    """Laboratory test result model"""
    __tablename__ = "lab_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="SET NULL"), index=True)
    test_name = Column(String(200), nullable=False)
    test_code = Column(String(50), index=True)
    result_value = Column(String(100), nullable=False)
    unit = Column(String(50))
    reference_range = Column(String(100))
    flag = Column(String(20), index=True)
    result_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("flag IN ('normal', 'high', 'low', 'critical') OR flag IS NULL", name="chk_lab_flag"),
    )

    # Relationships
    patient = relationship("Patient", back_populates="lab_results")
    encounter = relationship("Encounter", back_populates="lab_results")
