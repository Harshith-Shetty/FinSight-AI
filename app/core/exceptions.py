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


class DatabaseError(FinSightException):
    """Raised when database operations fail."""
    pass


class TaskNotFoundError(FinSightException):
    """Raised when a task is not found in the database."""
    pass
