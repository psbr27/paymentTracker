import csv
import io
from datetime import date
from calendar import monthrange
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.payment import Payment
from app.utils.auth import get_current_user
from app.services.recurrence import payment_occurs_on_date

router = APIRouter()


@router.get("")
async def export_payments(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export payments as CSV."""
    # Build base query
    query = db.query(Payment).filter(Payment.user_id == current_user.id)

    # Filter by category if specified
    if category:
        query = query.filter(Payment.category == category)

    payments = query.all()

    # Determine date range
    if year and month:
        _, num_days = monthrange(year, month)
        start = date(year, month, 1)
        end = date(year, month, num_days)
    elif start_date and end_date:
        start = start_date
        end = end_date
    else:
        # Default to current month
        today = date.today()
        _, num_days = monthrange(today.year, today.month)
        start = date(today.year, today.month, 1)
        end = date(today.year, today.month, num_days)

    # Generate CSV data
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "Date", "Payment Name", "Amount", "Currency", "Category", "Recurrence", "Notes"
    ])

    # Generate rows for each day in range
    current = start
    while current <= end:
        for payment in payments:
            if payment_occurs_on_date(payment, current):
                writer.writerow([
                    current.isoformat(),
                    payment.name,
                    float(payment.amount),
                    payment.currency,
                    payment.category,
                    payment.recurrence,
                    payment.notes or ""
                ])
        current = date.fromordinal(current.toordinal() + 1)

    output.seek(0)

    # Return as downloadable CSV
    filename = f"payments_{start.isoformat()}_to_{end.isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
