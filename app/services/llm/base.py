"""
Abstract base class for LLM providers.
Implements Strategy Pattern for provider switching.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    This enables easy switching between different LLM providers (Groq, Ollama, etc.)
    by implementing a common interface. Change provider by updating config only.
    """
    
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate LLM response given prompt and context.
        
        Args:
            prompt: User query or instruction
            context: Retrieved context from RAG
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum response length
            
        Returns:
            Generated text response (JSON formatted)
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier."""
        pass
    
    def validate_config(self) -> bool:
        """Validate provider configuration."""
        return True
