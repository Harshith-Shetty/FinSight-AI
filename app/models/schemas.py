"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class TaskStatusEnum(str, Enum):
    """Task status enum for API responses."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Request Schemas
class AnalysisRequest(BaseModel):
    """Request schema for POST /api/v1/analyze."""
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    focus_area: Optional[str] = Field("general", description="Analysis focus area (e.g., risk_factors, financials)")
    filing_year: int = Field(..., ge=2000, le=2030, description="SEC filing year")
    
    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        """Convert ticker to uppercase."""
        return v.upper()
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "AAPL",
                    "focus_area": "risk_factors",
                    "filing_year": 2024
                }
            ]
        }
    }


# Response Schemas
class TaskResponse(BaseModel):
    """Response schema for task creation."""
    task_id: UUID
    status: TaskStatusEnum
    message: str
    
    model_config = {"from_attributes": True}


class Citation(BaseModel):
    """Citation from SEC filing."""
    text: str
    page: Optional[int] = None
    section: str


class AnalysisResult(BaseModel):
    """Structured analysis result from LLM."""
    ticker: str
    summary: str
    citations: List[Citation]
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score from -1 (negative) to 1 (positive)")
    key_risks: List[str]


class TaskStatusResponse(BaseModel):
    """Response schema for task status queries."""
    task_id: UUID
    status: TaskStatusEnum
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
