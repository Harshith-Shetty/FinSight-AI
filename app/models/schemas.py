"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field, field_validator, EmailStr
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


class ProcessingStatusEnum(str, Enum):
    """Document processing status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChatModeEnum(str, Enum):
    """Chat mode enum."""
    HYBRID = "HYBRID"
    PRIVATE = "PRIVATE"


class MessageRoleEnum(str, Enum):
    """Message role enum."""
    USER = "user"
    ASSISTANT = "assistant"


class UserRoleEnum(str, Enum):
    """User role enum."""
    ADMIN   = "admin"
    PREMIUM = "premium"
    NORMAL  = "normal"
    GUEST   = "guest"


# ============ Authentication Schemas ============

class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    """Response after user registration."""
    email: str
    email_verification_required: bool = True
    message: str


class VerifyEmailRequest(BaseModel):
    """Email verification request."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class ResendOTPRequest(BaseModel):
    """Resend OTP request."""
    email: EmailStr
    purpose: str = Field("email_verification", description="OTP purpose: email_verification or password_reset")


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


class UserResponse(BaseModel):
    """User info response."""
    id: UUID
    email: str
    role: UserRoleEnum
    is_verified: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# ============ Token Usage Schemas ============

class TokenUsageResponse(BaseModel):
    """Token usage for current month."""
    tokens_used: int
    limit: Optional[int]          # None = unlimited (Admin)
    remaining: Optional[int]      # None = unlimited
    month: str                    # ISO date string e.g. "2026-05-01"
    is_over_limit: bool


# ============ Admin Schemas ============

class UserAdminResponse(BaseModel):
    """User info for admin listing."""
    id: UUID
    email: str
    role: UserRoleEnum
    created_at: datetime
    last_login: Optional[datetime] = None
    tokens_used_this_month: int = 0

    model_config = {"from_attributes": True}


class UpdateUserRoleRequest(BaseModel):
    """Request to change a user's role."""
    role: UserRoleEnum


# ============ Document Schemas ============

class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    id: UUID
    filename: str
    file_size: Optional[int]
    processing_status: ProcessingStatusEnum
    upload_date: datetime
    is_system_doc: bool = False
    
    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Document list item."""
    id: UUID
    filename: str
    file_size: Optional[int]
    file_type: Optional[str]
    processing_status: ProcessingStatusEnum
    upload_date: datetime
    is_system_doc: bool = False
    
    model_config = {"from_attributes": True}


# ============ Chat Schemas ============

class ChatCreate(BaseModel):
    """Create new chat request."""
    title: Optional[str] = None
    mode: ChatModeEnum


class ChatResponse(BaseModel):
    """Chat info response."""
    id: UUID
    title: Optional[str]
    mode: ChatModeEnum
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ChatListResponse(BaseModel):
    """Chat list response."""
    chats: List[ChatResponse]


# ============ Message Schemas ============

class MessageCreate(BaseModel):
    """Send message request."""
    content: str = Field(..., min_length=1, description="Message content")


class MessageResponse(BaseModel):
    """Message response."""
    id: UUID
    role: MessageRoleEnum
    content: str
    metadata: Optional[dict] = Field(None, validation_alias="message_metadata")
    created_at: datetime
    
    model_config = {"from_attributes": True, "populate_by_name": True}


class ChatHistoryResponse(BaseModel):
    """Chat history response."""
    chat_id: UUID
    messages: List[MessageResponse]


# ============ Existing Analysis Schemas ============

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
