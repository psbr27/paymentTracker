from datetime import date
from calendar import monthrange
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.payment import Payment
from app.utils.auth import get_current_user
from app.services.recurrence import get_payments_for_date

router = APIRouter()


@router.get("/{year}")
async def get_year_summary(
    year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get year summary with monthly totals."""
    if not (1900 <= year <= 2100):
        return {"error": "Year must be between 1900 and 2100"}

    payments = db.query(Payment).filter(Payment.user_id == current_user.id).all()

    months_data = []
    annual_total = Decimal("0")
    max_monthly = Decimal("0")

    for month in range(1, 13):
        _, num_days = monthrange(year, month)
        monthly_total = Decimal("0")

        for day in range(1, num_days + 1):
            current_date = date(year, month, day)
            day_payments = get_payments_for_date(payments, current_date)
            monthly_total += sum(Decimal(str(p.amount)) for p in day_payments)

        if monthly_total > max_monthly:
            max_monthly = monthly_total

        months_data.append({
            "month": month,
            "total": float(monthly_total)
        })
        annual_total += monthly_total

    # Calculate intensity (0-1 scale relative to max month)
    for month_data in months_data:
        if max_monthly > 0:
            month_data["intensity"] = round(Decimal(str(month_data["total"])) / max_monthly, 2)
        else:
            month_data["intensity"] = 0

    return {
        "year": year,
        "annual_total": float(annual_total),
        "months": months_data
    }
