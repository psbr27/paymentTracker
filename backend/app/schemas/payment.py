from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date
from typing import Optional
from decimal import Decimal


class PaymentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^(USD|INR)$")
    category: str = Field(default="OTHER", pattern="^(LOAN|SUBSCRIPTION|INVESTMENT|INSURANCE|UTILITY|OTHER)$")
    recurrence: str = Field(default="MONTHLY", pattern="^(MONTHLY|WEEKLY|BIWEEKLY|QUARTERLY|ANNUAL|ONETIME)$")
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, pattern="^(USD|INR)$")
    category: Optional[str] = Field(None, pattern="^(LOAN|SUBSCRIPTION|INVESTMENT|INSURANCE|UTILITY|OTHER)$")
    recurrence: Optional[str] = Field(None, pattern="^(MONTHLY|WEEKLY|BIWEEKLY|QUARTERLY|ANNUAL|ONETIME)$")
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None


class PaymentResponse(PaymentBase):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True
