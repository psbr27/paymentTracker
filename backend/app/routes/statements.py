from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.statement import Statement
from app.schemas.statement import (
    StatementListItem,
    StatementListResponse,
    StatementDetail,
    AnalyzeStatementRequest,
    AnalyzeStatementResponse,
    DeleteStatementResponse,
    AIUsageInfo
)
from app.services.pdf_parser import extract_all_text_from_pdf, PDFParseError
from app.services.claude_service import (
    analyze_statement_comprehensive,
    ClaudeError,
    ClaudeUnavailableError
)
from app.utils.auth import get_current_user

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.get("", response_model=StatementListResponse)
async def list_statements(
    bank_name: Optional[str] = Query(None, description="Filter by bank name"),
    year: Optional[int] = Query(None, description="Filter by year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all analyzed statements for the current user."""
    query = db.query(Statement).filter(Statement.user_id == current_user.id)

    if bank_name:
        query = query.filter(Statement.bank_name.ilike(f"%{bank_name}%"))

    if year:
        query = query.filter(
            db.extract('year', Statement.period_start) == year
        )

    query = query.order_by(Statement.period_start.desc())
    statements = query.all()

    items = []
    for stmt in statements:
        # Extract totals from analysis if available
        total_credits = None
        total_debits = None
        if stmt.analysis and isinstance(stmt.analysis, dict):
            summary = stmt.analysis.get('summary', {})
            total_credits = summary.get('totalCredits')
            total_debits = summary.get('totalDebits')

        items.append(StatementListItem(
            id=str(stmt.id),
            bank_name=stmt.bank_name,
            period_start=stmt.period_start,
            period_end=stmt.period_end,
            total_credits=total_credits,
            total_debits=total_debits,
            created_at=stmt.created_at
        ))

    return StatementListResponse(statements=items, total=len(items))


@router.get("/{statement_id}", response_model=StatementDetail)
async def get_statement(
    statement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific statement with full analysis."""
    statement = db.query(Statement).filter(
        Statement.id == statement_id,
        Statement.user_id == current_user.id
    ).first()

    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )

    ai_usage = None
    if statement.ai_model:
        ai_usage = AIUsageInfo(
            model=statement.ai_model,
            tokens_used=statement.ai_tokens_used,
            cost_estimate=statement.ai_cost_estimate
        )

    return StatementDetail(
        id=str(statement.id),
        bank_name=statement.bank_name,
        account_number_masked=statement.account_number_masked,
        period_start=statement.period_start,
        period_end=statement.period_end,
        original_filename=statement.original_filename,
        analysis=statement.analysis,
        ai_usage=ai_usage,
        created_at=statement.created_at,
        updated_at=statement.updated_at
    )


@router.post("/analyze", response_model=AnalyzeStatementResponse)
async def analyze_statement(
    file: UploadFile = File(...),
    bank_name: Optional[str] = Query(None, description="Override detected bank name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and analyze a bank statement PDF."""
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    filename_lower = file.filename.lower()
    if not filename_lower.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported for statement analysis"
        )

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 10MB)"
        )

    # Extract text from PDF
    try:
        statement_text = extract_all_text_from_pdf(content)
    except PDFParseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not statement_text or len(statement_text.strip()) < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract sufficient text from PDF"
        )

    # Analyze with Claude
    try:
        analysis, usage = await analyze_statement_comprehensive(statement_text)
    except ClaudeUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}"
        )
    except ClaudeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(e)}"
        )

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse AI response"
        )

    # Extract metadata from analysis
    metadata = analysis.get('metadata', {})
    period = metadata.get('statementPeriod', {})

    # Parse dates
    try:
        period_start = datetime.strptime(period.get('start', ''), '%Y-%m-%d').date()
        period_end = datetime.strptime(period.get('end', ''), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        # Fallback to current month
        from datetime import date
        today = date.today()
        period_start = today.replace(day=1)
        period_end = today

    # Determine bank name
    detected_bank = metadata.get('bankName', '')
    final_bank_name = bank_name or detected_bank or "Unknown Bank"

    # Mask account number (keep last 4 digits)
    account_num = metadata.get('accountNumber', '')
    masked_account = None
    if account_num and len(account_num) >= 4:
        masked_account = f"****{account_num[-4:]}"

    # Create statement record
    statement = Statement(
        user_id=current_user.id,
        bank_name=final_bank_name,
        account_number_masked=masked_account,
        period_start=period_start,
        period_end=period_end,
        original_filename=file.filename,
        analysis=analysis,
        ai_model=usage.model if usage else None,
        ai_tokens_used=usage.total_tokens if usage else None,
        ai_cost_estimate=f"${usage.cost_estimate:.4f}" if usage else None
    )

    db.add(statement)
    db.commit()
    db.refresh(statement)

    ai_usage_info = None
    if usage:
        ai_usage_info = AIUsageInfo(
            model=usage.model,
            tokens_used=usage.total_tokens,
            cost_estimate=f"${usage.cost_estimate:.4f}"
        )

    return AnalyzeStatementResponse(
        success=True,
        statement_id=str(statement.id),
        bank_name=final_bank_name,
        period_start=period_start,
        period_end=period_end,
        analysis=analysis,
        ai_usage=ai_usage_info,
        message="Statement analyzed successfully"
    )


@router.delete("/{statement_id}", response_model=DeleteStatementResponse)
async def delete_statement(
    statement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a statement."""
    statement = db.query(Statement).filter(
        Statement.id == statement_id,
        Statement.user_id == current_user.id
    ).first()

    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )

    db.delete(statement)
    db.commit()

    return DeleteStatementResponse(
        success=True,
        message="Statement deleted successfully"
    )
