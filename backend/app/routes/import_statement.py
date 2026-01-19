from typing import List, Tuple

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.payment import Payment
from app.schemas.import_statement import (
    ImportPreviewResponse,
    ImportConfirmRequest,
    ImportConfirmResponse,
    CreatedPayment,
    ParsedTransaction
)
from app.services.csv_parser import parse_csv, CSVParseError
from app.services.pdf_parser import parse_pdf, PDFParseError
from app.services.transaction_analyzer import analyze_transactions
from app.utils.auth import get_current_user

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def process_pdf_file(content: bytes) -> Tuple[List[ParsedTransaction], List[str]]:
    """Process PDF using pdfplumber with LLM fallback for extraction"""
    return await parse_pdf(content)


@router.post("/upload", response_model=ImportPreviewResponse)
async def upload_statement(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a CSV or PDF bank statement and analyze transactions.

    Returns a preview of detected recurring bills with LLM-suggested
    categorization and recurrence patterns.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    filename_lower = file.filename.lower()
    is_csv = filename_lower.endswith('.csv')
    is_pdf = filename_lower.endswith('.pdf')

    if not is_csv and not is_pdf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and PDF files are supported"
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )

    # Parse based on file type
    try:
        if is_csv:
            transactions, warnings = parse_csv(content)
        else:
            transactions, warnings = await process_pdf_file(content)
    except CSVParseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PDFParseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Get user's default currency
    currency = current_user.default_currency or "USD"

    # Analyze transactions with LLM (or fallback)
    analyzed, used_fallback = await analyze_transactions(transactions, currency)

    if not analyzed:
        return ImportPreviewResponse(
            success=True,
            total_transactions=len(transactions),
            analyzed_bills=[],
            parsing_warnings=warnings + ["No recurring bills detected in this statement."],
            used_fallback=used_fallback
        )

    return ImportPreviewResponse(
        success=True,
        total_transactions=len(transactions),
        analyzed_bills=analyzed,
        parsing_warnings=warnings,
        used_fallback=used_fallback
    )


@router.post("/confirm", response_model=ImportConfirmResponse)
async def confirm_import(
    request: ImportConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm and import selected transactions as recurring payments.

    Creates Payment records for each selected transaction.
    """
    if not request.transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transactions selected for import"
        )

    created_payments = []
    errors = []

    for tx in request.transactions:
        try:
            # Create payment record
            payment = Payment(
                user_id=current_user.id,
                name=tx.name,
                amount=tx.amount,
                currency=tx.currency,
                category=tx.category,
                recurrence=tx.recurrence,
                day_of_month=tx.day_of_month,
                day_of_week=tx.day_of_week,
                start_date=tx.start_date,
                end_date=None,
                notes=tx.notes or f"Imported from bank statement"
            )
            db.add(payment)
            db.flush()  # Get the ID without committing

            created_payments.append(CreatedPayment(
                id=str(payment.id),
                name=payment.name,
                amount=payment.amount
            ))
        except Exception as e:
            errors.append(f"Failed to import '{tx.name}': {str(e)}")

    if created_payments:
        db.commit()

    return ImportConfirmResponse(
        success=len(errors) == 0,
        imported_count=len(created_payments),
        created_payments=created_payments,
        errors=errors
    )
