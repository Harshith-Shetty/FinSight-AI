"""
LLM Provider Factory - enables one-config-change provider switching.
Implements Factory Pattern.
"""

from app.services.llm.base import LLMProvider
from app.services.llm.groq_provider import GroqProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.core.config import Settings
from app.core.exceptions import InvalidProviderError


class LLMProviderFactory:
    """
    Factory for creating LLM providers based on configuration.
    
    This is the magic that enables switching from Groq to Ollama
    with a single environment variable change.
    """
    
    @staticmethod
    def create_provider(config: Settings) -> LLMProvider:
        """
        Create and return the configured LLM provider.
        
        Args:
            config: Application settings
            
        Returns:
            LLMProvider instance (GroqProvider or OllamaProvider)
            
        Raises:
            InvalidProviderError: If provider type is unknown
            
        Example:
            # In .env: LLM_PROVIDER=groq
            provider = LLMProviderFactory.create_provider(settings)
            # Returns GroqProvider instance
            
            # Change .env: LLM_PROVIDER=ollama
            provider = LLMProviderFactory.create_provider(settings)
            # Returns OllamaProvider instance
        """
        provider_type = config.LLM_PROVIDER.lower()
        
        if provider_type == "groq":
            provider = GroqProvider(config)
        elif provider_type == "ollama":
            provider = OllamaProvider(config)
        else:
            raise InvalidProviderError(
                f"Unknown LLM provider: {provider_type}. "
                f"Supported providers: groq, ollama"
            )
        
        # Validate configuration
        if not provider.validate_config():
            raise InvalidProviderError(
                f"Invalid configuration for provider: {provider_type}"
            )
        
        return provider


# Convenience function for easy imports
def get_llm_provider() -> LLMProvider:
    """
    Get the configured LLM provider.
    
    This is the main function used throughout the application.
    """
    from app.core.config import settings
    return LLMProviderFactory.create_provider(settings)
