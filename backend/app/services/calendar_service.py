from datetime import date
from calendar import monthrange
from typing import Dict, List, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.payment import Payment
from app.services.recurrence import get_payments_for_date


def get_calendar_data(
    db: Session,
    user_id: str,
    year: int,
    month: int
) -> Dict[str, Any]:
    """Generate calendar data for a specific month."""
    # Get all user payments
    payments = db.query(Payment).filter(Payment.user_id == user_id).all()

    # Get number of days in the month
    _, num_days = monthrange(year, month)

    days_data = {}
    monthly_total = Decimal("0")
    weekly_totals = {"week1": Decimal("0"), "week2": Decimal("0"), "week3": Decimal("0"), "week4": Decimal("0")}

    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        day_payments = get_payments_for_date(payments, current_date)

        day_total = sum(Decimal(str(p.amount)) for p in day_payments)
        categories = list(set(p.category for p in day_payments))

        days_data[str(day)] = {
            "total": float(day_total),
            "payments": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "amount": float(p.amount),
                    "currency": p.currency,
                    "category": p.category,
                    "recurrence": p.recurrence,
                    "notes": p.notes
                }
                for p in day_payments
            ],
            "categories": categories
        }

        monthly_total += day_total

        # Calculate weekly totals
        if 1 <= day <= 7:
            weekly_totals["week1"] += day_total
        elif 8 <= day <= 14:
            weekly_totals["week2"] += day_total
        elif 15 <= day <= 21:
            weekly_totals["week3"] += day_total
        else:
            weekly_totals["week4"] += day_total

    return {
        "year": year,
        "month": month,
        "days": days_data,
        "weekly_totals": {k: float(v) for k, v in weekly_totals.items()},
        "monthly_total": float(monthly_total)
    }
