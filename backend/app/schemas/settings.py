from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class ExchangeRateResponse(BaseModel):
    from_currency: str
    to_currency: str
    rate: Decimal

    class Config:
        from_attributes = True


class ExchangeRateUpdate(BaseModel):
    rate: Decimal


class UserSettingsResponse(BaseModel):
    default_currency: str
    exchange_rates: list[ExchangeRateResponse]


class UserSettingsUpdate(BaseModel):
    default_currency: Optional[str] = None
