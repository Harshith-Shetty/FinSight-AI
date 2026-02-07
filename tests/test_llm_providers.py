"""
Test LLM provider abstraction and switching.
"""

import pytest
from app.services.llm.factory import LLMProviderFactory
from app.services.llm.groq_provider import GroqProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.core.config import Settings


def test_groq_provider_creation():
    """Test Groq provider is created correctly."""
    config = Settings(
        LLM_PROVIDER="groq",
        GROQ_API_KEY="test_key",
        DATABASE_URL="sqlite:///:memory:",
        REDIS_URL="redis://localhost",
        CELERY_BROKER_URL="redis://localhost",
        CELERY_RESULT_BACKEND="redis://localhost",
        QDRANT_URL="http://localhost:6333",
        SECRET_KEY="test_secret"
    )
    
    provider = LLMProviderFactory.create_provider(config)
    
    assert isinstance(provider, GroqProvider)
    assert provider.get_model_name() == "llama-3.3-70b-versatile"


def test_ollama_provider_creation():
    """Test Ollama provider is created correctly."""
    config = Settings(
        LLM_PROVIDER="ollama",
        OLLAMA_BASE_URL="http://localhost:11434",
        DATABASE_URL="sqlite:///:memory:",
        REDIS_URL="redis://localhost",
        CELERY_BROKER_URL="redis://localhost",
        CELERY_RESULT_BACKEND="redis://localhost",
        QDRANT_URL="http://localhost:6333",
        SECRET_KEY="test_secret"
    )
    
    provider = LLMProviderFactory.create_provider(config)
    
    assert isinstance(provider, OllamaProvider)
    assert provider.get_model_name() == "llama3.2:3b"


def test_provider_switching():
    """Test that changing config switches providers."""
    # Start with Groq
    config_groq = Settings(
        LLM_PROVIDER="groq",
        GROQ_API_KEY="test_key",
        DATABASE_URL="sqlite:///:memory:",
        REDIS_URL="redis://localhost",
        CELERY_BROKER_URL="redis://localhost",
        CELERY_RESULT_BACKEND="redis://localhost",
        QDRANT_URL="http://localhost:6333",
        SECRET_KEY="test_secret"
    )
    
    provider1 = LLMProviderFactory.create_provider(config_groq)
    assert isinstance(provider1, GroqProvider)
    
    # Switch to Ollama
    config_ollama = Settings(
        LLM_PROVIDER="ollama",
        OLLAMA_BASE_URL="http://localhost:11434",
        DATABASE_URL="sqlite:///:memory:",
        REDIS_URL="redis://localhost",
        CELERY_BROKER_URL="redis://localhost",
        CELERY_RESULT_BACKEND="redis://localhost",
        QDRANT_URL="http://localhost:6333",
        SECRET_KEY="test_secret"
    )
    
    provider2 = LLMProviderFactory.create_provider(config_ollama)
    assert isinstance(provider2, OllamaProvider)
