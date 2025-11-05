"""
Custom Exception Classes

This module defines custom exception classes for the Pro-Irrigation Add-on
to provide more specific error handling and better error messages.
"""


class ProIrrigationException(Exception):
    """Base exception for all Pro-Irrigation errors"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(ProIrrigationException):
    """Raised when database operations fail"""
    pass


class HomeAssistantException(ProIrrigationException):
    """Raised when Home Assistant API operations fail"""
    pass


class ValidationException(ProIrrigationException):
    """Raised when input validation fails"""
    pass


class SchedulerException(ProIrrigationException):
    """Raised when scheduler operations fail"""
    pass


class QueueProcessorException(ProIrrigationException):
    """Raised when queue processor operations fail"""
    pass


class ConfigurationException(ProIrrigationException):
    """Raised when configuration is invalid or incomplete"""
    pass
