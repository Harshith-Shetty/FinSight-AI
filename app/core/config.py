"""
Application configuration using Pydantic Settings.
Supports environment-based configuration for easy provider switching.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional


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
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def clean_database_url(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            return v
        
        # 1. Convert postgres:// or postgresql:// to postgresql+asyncpg:// for SQLAlchemy
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            
        # 2. Convert sslmode=... to ssl=true for asyncpg compatibility
        from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
        parsed = urlparse(v)
        query = parse_qs(parsed.query)
        
        if "sslmode" in query:
            val = query.pop("sslmode")[0]
            if val != "disable":
                query["ssl"] = ["require"]
            else:
                query["ssl"] = ["disable"]
                
        new_query = urlencode(query, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
