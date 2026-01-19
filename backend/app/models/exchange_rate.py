import uuid
from sqlalchemy import Column, Numeric, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_currency = Column(Enum("USD", "INR", name="currency_type"), nullable=False)
    to_currency = Column(Enum("USD", "INR", name="currency_type"), nullable=False)
    rate = Column(Numeric(10, 4), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
