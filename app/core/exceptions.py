"""
Custom exceptions for FinSight AI.
"""


class FinSightException(Exception):
    """Base exception for all custom errors."""
    pass


class InvalidProviderError(FinSightException):
    """Raised when LLM provider configuration is invalid."""
    pass


class SECAPIError(FinSightException):
    """Raised when SEC EDGAR API fails."""
    pass


class VectorStoreError(FinSightException):
    """Raised when Qdrant operations fail."""
    pass
