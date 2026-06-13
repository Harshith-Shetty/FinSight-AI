"""
Groq API provider implementation.
Used for development - fast, free, production-quality inference.
"""

from groq import AsyncGroq
from app.services.llm.base import LLMProvider
from app.core.config import settings
from typing import AsyncGenerator, Optional
import json


class GroqProvider(LLMProvider):
    """
    Groq API provider implementation.
    
    Uses Groq's LPU-accelerated inference for blazing-fast responses.
    Perfect for development and can be used in production with free tier.
    """
    
    def __init__(self, config=None):
        cfg = config or settings
        self.api_key = cfg.GROQ_API_KEY
        self.model = cfg.GROQ_MODEL
        self.client = AsyncGroq(api_key=self.api_key)
    
    async def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> tuple[str, int]:
        """
        Generate response using Groq API.

        Args:
            prompt: User prompt or question
            context: Optional context (for analysis tasks)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            json_mode: Whether to use JSON response format

        Returns:
            Tuple of (generated text response, total tokens used)
        """
        if context:
            # Analysis mode - structured JSON output
            messages = self._build_messages(prompt, context)
            response_format = {"type": "json_object"} if json_mode else None
        else:
            # Chat mode - simple prompt
            messages = [{"role": "user", "content": prompt}]
            response_format = None

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format
        )

        tokens_used = response.usage.total_tokens if response.usage else 0
        return response.choices[0].message.content, tokens_used
    
    async def stream(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from Groq API.
        
        Args:
            prompt: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Yields:
            Text chunks as they are generated
        """
        messages = [{"role": "user", "content": prompt}]
        
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        total_chars = 0
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                total_chars += len(content)
                yield content
        
        # Estimate token usage safely (approx 4 chars per token)
        total_tokens = int(total_chars * 0.25) + len(prompt) // 4
        yield f"__TOKENS__:{total_tokens}"
    
    def _build_messages(self, prompt: str, context: str) -> list:
        """Build chat messages for Groq API (analysis mode)."""
        system_prompt = """You are a senior financial analyst with expertise in SEC filings analysis.
Analyze the provided context from SEC filings and answer the user's question accurately.

Return your response in JSON format with the following structure:
{
    "summary": "Brief summary of findings",
    "key_risks": ["risk 1", "risk 2", ...],
    "sentiment_score": 0.5,
    "citations": [{"text": "quote", "section": "Risk Factors", "page": 10}]
}

Be precise, cite specific sections, and provide actionable insights."""
        
        user_message = f"""Context from SEC Filing:
{context}

Question: {prompt}"""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    
    def get_model_name(self) -> str:
        """Return Groq model name."""
        return self.model
    
    def validate_config(self) -> bool:
        """Validate Groq configuration."""
        return self.api_key is not None and len(self.api_key) > 0
