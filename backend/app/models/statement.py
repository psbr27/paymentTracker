import uuid
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Statement(Base):
    __tablename__ = "statements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Statement metadata
    bank_name = Column(String(100), nullable=False)
    account_number_masked = Column(String(20), nullable=True)  # Last 4 digits only
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # File info
    original_filename = Column(String(255), nullable=True)

    # Analysis results stored as JSON
    analysis = Column(JSONB, nullable=False)

    # AI usage tracking
    ai_model = Column(String(100), nullable=True)
    ai_tokens_used = Column(Integer, nullable=True)
    ai_cost_estimate = Column(String(20), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="statements")
