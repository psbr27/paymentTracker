from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.exchange_rate import ExchangeRate
from app.schemas.settings import UserSettingsResponse, UserSettingsUpdate, ExchangeRateUpdate
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user settings including exchange rates."""
    exchange_rates = db.query(ExchangeRate).all()

    return {
        "default_currency": current_user.default_currency,
        "exchange_rates": exchange_rates
    }


@router.put("")
async def update_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user settings."""
    if settings_update.default_currency:
        if settings_update.default_currency not in ["USD", "INR"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Currency must be USD or INR"
            )
        current_user.default_currency = settings_update.default_currency
        db.commit()

    return {"message": "Settings updated successfully"}


@router.put("/exchange-rate/{from_currency}/{to_currency}")
async def update_exchange_rate(
    from_currency: str,
    to_currency: str,
    rate_update: ExchangeRateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an exchange rate."""
    if from_currency not in ["USD", "INR"] or to_currency not in ["USD", "INR"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currency must be USD or INR"
        )

    exchange_rate = db.query(ExchangeRate).filter(
        ExchangeRate.from_currency == from_currency,
        ExchangeRate.to_currency == to_currency
    ).first()

    if not exchange_rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange rate not found"
        )

    exchange_rate.rate = rate_update.rate
    db.commit()

    return {"message": "Exchange rate updated successfully"}
