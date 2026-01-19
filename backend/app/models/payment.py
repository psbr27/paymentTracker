import uuid
from sqlalchemy import Column, String, Numeric, Integer, Date, Text, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(Enum("USD", "INR", name="currency_type"), nullable=False, default="USD")
    category = Column(
        Enum("LOAN", "SUBSCRIPTION", "INVESTMENT", "INSURANCE", "UTILITY", "OTHER", name="category_type"),
        nullable=False,
        default="OTHER"
    )
    recurrence = Column(
        Enum("MONTHLY", "WEEKLY", "BIWEEKLY", "QUARTERLY", "ANNUAL", "ONETIME", name="recurrence_type"),
        nullable=False,
        default="MONTHLY"
    )
    day_of_month = Column(Integer, nullable=True)  # 1-31 for monthly/quarterly/annual
    day_of_week = Column(Integer, nullable=True)   # 0-6 for weekly/biweekly
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="payments")
