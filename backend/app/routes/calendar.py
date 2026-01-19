from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user
from app.services.calendar_service import get_calendar_data

router = APIRouter()


@router.get("/{year}/{month}")
async def get_calendar(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get calendar data for a specific month."""
    if not (1 <= month <= 12):
        return {"error": "Month must be between 1 and 12"}
    if not (1900 <= year <= 2100):
        return {"error": "Year must be between 1900 and 2100"}

    return get_calendar_data(db, current_user.id, year, month)
