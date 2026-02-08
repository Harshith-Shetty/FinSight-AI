"""
SQLAlchemy ORM models for FinSight AI.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, Integer, Index, Boolean
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


class ProcessingStatus(enum.Enum):
    """Document processing status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChatMode(enum.Enum):
    """Chat mode enum."""
    HYBRID = "hybrid"  # Uses system KB + user documents
    PRIVATE = "private"  # Uses only user documents


class MessageRole(enum.Enum):
    """Message role enum."""
    USER = "user"
    ASSISTANT = "assistant"


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    api_key_hash = Column(String(255), nullable=True)  # Optional API key for programmatic access
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    tasks = relationship("AnalysisTask", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Document(Base):
    """Document model for user-uploaded files."""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(50), nullable=True)
    is_system_doc = Column(Boolean, default=False, nullable=False)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_docs', 'user_id', 'is_system_doc'),
        Index('idx_processing_status', 'processing_status'),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, user_id={self.user_id})>"


class Chat(Base):
    """Chat session model."""
    __tablename__ = "chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    mode = Column(Enum(ChatMode), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_chats', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Chat(id={self.id}, mode={self.mode}, user_id={self.user_id})>"


class Message(Base):
    """Chat message model."""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSONB, nullable=True)  # Store sources, citations, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index('idx_chat_messages', 'chat_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, chat_id={self.chat_id})>"


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
