"""Risk prediction model"""

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, CheckConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class RiskPrediction(Base):
    """Patient readmission risk prediction model"""
    __tablename__ = "risk_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_score = Column(Numeric(5, 2), nullable=False)
    confidence_lower = Column(Numeric(5, 2))
    confidence_upper = Column(Numeric(5, 2))
    risk_band = Column(String(20), nullable=False, index=True)
    feature_contributions = Column(JSON)
    model_version_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    predicted_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="chk_risk_score_range"),
        CheckConstraint("confidence_lower BETWEEN 0 AND 100 OR confidence_lower IS NULL", name="chk_confidence_lower_range"),
        CheckConstraint("confidence_upper BETWEEN 0 AND 100 OR confidence_upper IS NULL", name="chk_confidence_upper_range"),
        CheckConstraint("risk_band IN ('low', 'medium', 'high')", name="chk_risk_band"),
    )

    # Relationships
    patient = relationship("Patient", back_populates="risk_predictions")
    encounter = relationship("Encounter", back_populates="risk_predictions")
    model_version = relationship("ModelVersion", back_populates="risk_predictions")

