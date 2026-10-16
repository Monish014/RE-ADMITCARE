"""Model version model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class ModelVersion(Base):
    """ML model version tracking"""
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_name = Column(String(50), nullable=False, unique=True)
    model_type = Column(String(50), nullable=False)
    hyperparameters = Column(JSON)
    metrics = Column(JSON)
    trained_at = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    risk_predictions = relationship("RiskPrediction", back_populates="model_version")

