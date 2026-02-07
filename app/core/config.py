"""
Application configuration using Pydantic Settings.
Supports environment-based configuration for easy provider switching.
"""

from pydantic_settings import BaseSettings
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
    API_KEY_HASH_ALGORITHM: str = "HS256"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
