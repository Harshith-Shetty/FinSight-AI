"""
Application configuration using Pydantic Settings.
Supports environment-based configuration for easy provider switching.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Supports both Groq and Ollama LLM providers with simple config switching.
    """
    
    # Application
    APP_NAME: str = "FinSight AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    DATABASE_SSL: bool = False
    
    # Redis
    REDIS_URL: str
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # Qdrant Vector Database
    QDRANT_URL: str
    QDRANT_API_KEY: Optional[str] = None
    
    # LLM Provider Selection - THIS IS THE KEY TO PROVIDER SWITCHING
    LLM_PROVIDER: str = "groq"  # "groq" or "ollama"
    
    # Groq Configuration (Development)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # Ollama Configuration (Production on AWS)
    OLLAMA_BASE_URL: Optional[str] = None
    OLLAMA_MODEL: str = "llama3.2:3b"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    API_KEY_HASH_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200
    
    # Frontend URL (used in emails and CORS)
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Postmark Email Configuration (SMTP)
    POSTMARK_SMTP_HOST: str = "smtp.postmarkapp.com"
    POSTMARK_SMTP_PORT: int = 587
    POSTMARK_SERVER_TOKEN: Optional[str] = None
    POSTMARK_FROM_EMAIL: str = "FinSight AI <noreply@harshithshetty.dev>"
    POSTMARK_MESSAGE_STREAM: str = "finsightai"
    
    # OTP Settings
    OTP_EXPIRY_MINUTES: int = 10
    OTP_RESEND_COOLDOWN_SECONDS: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"

    # RAG Pipeline Tuning
    RAG_MIN_RETRIEVAL_K: int = 20       # minimum candidates fetched before reranking
    RAG_MIN_RERANK_SCORE: float = -1.0  # cross-encoder logit threshold below which a chunk is dropped
    RAG_MIN_CONTEXT_CHUNKS: int = 1     # if fewer chunks pass the threshold, treat as "no context"
    RAG_QUERY_REWRITE_ENABLED: bool = True
    RAG_QUERY_REWRITE_MIN_HISTORY: int = 1  # min prior messages before rewriting kicks in
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def clean_database_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("REDIS_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def configure_redis_tls(cls, value: str) -> str:
        """Require certificate validation for secure Redis connections."""
        if not isinstance(value, str) or not value.lower().startswith("rediss://"):
            return value

        parsed = urlsplit(value)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query.setdefault("ssl_cert_reqs", "required")
        return urlunsplit(parsed._replace(query=urlencode(query)))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
