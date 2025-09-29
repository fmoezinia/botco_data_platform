"""
Custom exceptions for the Botco Data Platform.
"""
from typing import Optional, Dict, Any


class BotcoException(Exception):
    """Base exception for Botco Data Platform."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationError(BotcoException):
    """Raised when data validation fails."""
    pass


class FileNotFoundError(BotcoException):
    """Raised when a required file is not found."""
    pass


class ProcessingError(BotcoException):
    """Raised when video processing fails."""
    pass


class SAM2Error(BotcoException):
    """Raised when SAM2 processing fails."""
    pass


class StorageError(BotcoException):
    """Raised when storage operations fail."""
    pass


class TaskError(BotcoException):
    """Raised when task management fails."""
    pass


class ConfigurationError(BotcoException):
    """Raised when configuration is invalid."""
    pass


class ServiceUnavailableError(BotcoException):
    """Raised when a required service is unavailable."""
    pass
