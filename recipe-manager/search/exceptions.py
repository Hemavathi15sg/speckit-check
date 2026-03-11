"""
Search Module Exceptions

Custom exception classes for each module phase.
Enables precise error handling and debugging.

Constitution Principle VII: Observability & Operations
- Clear error messages with context
- Module-specific exceptions for targeted handling
- Field-level error details for API responses
"""

from typing import Any, Optional, Dict


class SearchError(Exception):
    """Base exception for all search module errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(SearchError):
    """
    Raised when input validation fails.
    
    API layer should catch this and return 400 Bad Request.
    """
    
    def __init__(self, field: str, value: Any, message: str):
        self.field = field
        self.value = value
        error_message = f"Validation error for {field}: {message}"
        details = {
            "field": field,
            "value": value,
            "error": message,
        }
        super().__init__(error_message, details)
    
    def to_api_response(self) -> Dict[str, Any]:
        """Convert to API-friendly error response."""
        return {
            "error": "ValidationError",
            "field": self.field,
            "message": self.details["error"],
            # Never expose the actual invalid value in production
            "value": "***" if self._is_sensitive_field() else self.value,
        }
    
    def _is_sensitive_field(self) -> bool:
        """Check if field contains sensitive data."""
        sensitive_fields = {"password", "token", "api_key", "secret"}
        return self.field.lower() in sensitive_fields


class FilteringError(SearchError):
    """
    Raised when recipe filtering fails.
    
    This should be rare - indicates data corruption or logic error.
    API layer should return 500 Internal Server Error.
    """
    
    def __init__(self, filter_name: str, message: str, recipe_id: Optional[str] = None):
        self.filter_name = filter_name
        self.recipe_id = recipe_id
        error_message = f"Filtering error in {filter_name}: {message}"
        details = {
            "filter": filter_name,
            "recipe_id": recipe_id,
            "error": message,
        }
        super().__init__(error_message, details)


class AggregationError(SearchError):
    """
    Raised when ranking or caching fails.
    
    Should trigger fallback to non-cached results.
    API layer can return results but should log error.
    """
    
    def __init__(self, operation: str, message: str, cache_key: Optional[str] = None):
        self.operation = operation
        self.cache_key = cache_key
        error_message = f"Aggregation error in {operation}: {message}"
        details = {
            "operation": operation,
            "cache_key": cache_key,
            "error": message,
        }
        super().__init__(error_message, details)


class FormattingError(SearchError):
    """
    Raised when response formatting fails.
    
    Should be extremely rare - indicates data type mismatch.
    API layer should return 500 Internal Server Error.
    """
    
    def __init__(self, field: str, message: str, recipe_id: Optional[str] = None):
        self.field = field
        self.recipe_id = recipe_id
        error_message = f"Formatting error for {field}: {message}"
        details = {
            "field": field,
            "recipe_id": recipe_id,
            "error": message,
        }
        super().__init__(error_message, details)
