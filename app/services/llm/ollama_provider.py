"""
Ollama provider implementation.
Used for production deployment on AWS EC2 - self-hosted, private, cost-effective.
"""

import httpx
from app.services.llm.base import LLMProvider
from app.core.config import Settings
import json


class OllamaProvider(LLMProvider):
    """
    Ollama provider for self-hosted LLMs on AWS.
    
    Connects to Ollama server running on AWS EC2 instance.
    Provides complete data privacy and control over infrastructure.
    """
    
    def __init__(self, config: Settings):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=120.0)  # Longer timeout for self-hosted
    
    async def generate(
        self, 
        prompt: str, 
        context: str,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> str:
        """Generate response using Ollama API."""
        payload = self._build_payload(prompt, context, temperature, max_tokens)
        
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        response.raise_for_status()
        
        # Ollama streams responses, concatenate them
        full_response = ""
        for line in response.text.split("\n"):
            if line.strip():
                try:
                    chunk = json.loads(line)
                    full_response += chunk.get("response", "")
                except json.JSONDecodeError:
                    continue
        
        return full_response
    
    def _build_payload(self, prompt: str, context: str, temperature: float, max_tokens: int) -> dict:
        """Build request payload for Ollama API."""
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
        
        full_prompt = f"""{system_prompt}

Context from SEC Filing:
{context}

Question: {prompt}"""
        
        return {
            "model": self.model,
            "prompt": full_prompt,
            "temperature": temperature,
            "options": {
                "num_predict": max_tokens
            },
            "format": "json",  # Request JSON output
            "stream": False
        }
    
    def get_model_name(self) -> str:
        """Return Ollama model name."""
        return self.model
    
    def validate_config(self) -> bool:
        """Validate Ollama configuration."""
        return self.base_url is not None and len(self.base_url) > 0
