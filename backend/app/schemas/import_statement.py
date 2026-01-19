from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
from decimal import Decimal


class ParsedTransaction(BaseModel):
    """Single transaction parsed from CSV"""
    date: date
    description: str
    amount: Decimal
    original_description: str


class DateRange(BaseModel):
    """Date range for transaction occurrences"""
    first: date
    last: date


class AnalyzedTransaction(BaseModel):
    """Transaction analyzed by LLM with suggestions"""
    id: str = Field(..., description="Temporary ID for tracking during import")
    original_descriptions: List[str] = Field(..., description="Raw descriptions from CSV")
    suggested_name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(default="OTHER", pattern="^(LOAN|SUBSCRIPTION|INVESTMENT|INSURANCE|UTILITY|OTHER)$")
    recurrence: str = Field(default="MONTHLY", pattern="^(MONTHLY|WEEKLY|BIWEEKLY|QUARTERLY|ANNUAL|ONETIME)$")
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    average_amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^(USD|INR)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    occurrence_count: int = Field(..., ge=1)
    date_range: DateRange


class AIUsage(BaseModel):
    """AI API usage statistics"""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_estimate: float = Field(default=0.0, description="Estimated cost in USD")


class ImportPreviewResponse(BaseModel):
    """Response from upload endpoint with analyzed transactions"""
    success: bool
    total_transactions: int
    analyzed_bills: List[AnalyzedTransaction]
    parsing_warnings: List[str] = []
    used_fallback: bool = Field(default=False, description="True if LLM was unavailable")
    ai_usage: Optional[AIUsage] = Field(default=None, description="AI token usage if LLM was used")


class TransactionToImport(BaseModel):
    """User-confirmed transaction to import as payment"""
    id: str = Field(..., description="Temporary ID from preview")
    name: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^(USD|INR)$")
    category: str = Field(default="OTHER", pattern="^(LOAN|SUBSCRIPTION|INVESTMENT|INSURANCE|UTILITY|OTHER)$")
    recurrence: str = Field(default="MONTHLY", pattern="^(MONTHLY|WEEKLY|BIWEEKLY|QUARTERLY|ANNUAL|ONETIME)$")
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_date: date
    notes: Optional[str] = None


class ImportConfirmRequest(BaseModel):
    """Request to confirm and create payments from selected transactions"""
    transactions: List[TransactionToImport]


class CreatedPayment(BaseModel):
    """Summary of a created payment"""
    id: str
    name: str
    amount: Decimal


class ImportConfirmResponse(BaseModel):
    """Response from confirm endpoint"""
    success: bool
    imported_count: int
    created_payments: List[CreatedPayment]
    errors: List[str] = []
