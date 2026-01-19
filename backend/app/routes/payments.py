from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("", response_model=List[PaymentResponse])
async def list_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all payments for the current user."""
    payments = db.query(Payment).filter(Payment.user_id == current_user.id).all()
    return payments


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new payment."""
    db_payment = Payment(
        user_id=current_user.id,
        name=payment.name,
        amount=payment.amount,
        currency=payment.currency,
        category=payment.category,
        recurrence=payment.recurrence,
        day_of_month=payment.day_of_month,
        day_of_week=payment.day_of_week,
        start_date=payment.start_date,
        end_date=payment.end_date,
        notes=payment.notes
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single payment by ID."""
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user.id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return payment


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: UUID,
    payment_update: PaymentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing payment."""
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user.id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    update_data = payment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)

    db.commit()
    db.refresh(payment)
    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a payment."""
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user.id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    db.delete(payment)
    db.commit()
    return None
