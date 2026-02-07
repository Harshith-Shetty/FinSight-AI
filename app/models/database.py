"""
SQLAlchemy ORM models for FinSight AI.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class TaskStatus(enum.Enum):
    """Task status enum."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class User(Base):
    """User model for API authentication."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    api_key_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    tasks = relationship("AnalysisTask", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class AnalysisTask(Base):
    """Analysis task model tracking the lifecycle of financial analysis requests."""
    __tablename__ = "analysis_tasks"
    
    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    ticker_symbol = Column(String(10), nullable=False, index=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    result_json = Column(JSONB, nullable=True)
    error_log = Column(Text, nullable=True)
    focus_area = Column(String(100), nullable=True)
    filing_year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_ticker_year', 'ticker_symbol', 'filing_year'),
    )
    
    def __repr__(self):
        return f"<AnalysisTask(task_id={self.task_id}, ticker={self.ticker_symbol}, status={self.status})>"
