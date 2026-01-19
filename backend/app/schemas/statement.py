from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List, Any, Dict
from decimal import Decimal


class StatementListItem(BaseModel):
    """Summary item for statement list view"""
    id: str
    bank_name: str
    period_start: date
    period_end: date
    total_credits: Optional[float] = None
    total_debits: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StatementListResponse(BaseModel):
    """Response for listing statements"""
    statements: List[StatementListItem]
    total: int


class AIUsageInfo(BaseModel):
    """AI usage information"""
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_estimate: Optional[str] = None


class StatementDetail(BaseModel):
    """Full statement detail with analysis"""
    id: str
    bank_name: str
    account_number_masked: Optional[str] = None
    period_start: date
    period_end: date
    original_filename: Optional[str] = None
    analysis: Dict[str, Any]
    ai_usage: Optional[AIUsageInfo] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalyzeStatementRequest(BaseModel):
    """Request body for analyzing a statement (optional metadata override)"""
    bank_name: Optional[str] = None


class AnalyzeStatementResponse(BaseModel):
    """Response from statement analysis"""
    success: bool
    statement_id: str
    bank_name: str
    period_start: date
    period_end: date
    analysis: Dict[str, Any]
    ai_usage: Optional[AIUsageInfo] = None
    message: Optional[str] = None


class DeleteStatementResponse(BaseModel):
    """Response from deleting a statement"""
    success: bool
    message: str
