"""
Search Module Package

Modular refactoring of legacy search.py into 4 clean modules:
- validation_module: Input validation and normalization
- filtering_module: Recipe filtering by criteria  
- aggregation_module: Ranking and caching
- formatting_module: Response formatting

Feature: 001-search-modular-refactor
Constitution: v1.0.0 (8 Principles)
"""

from search.types import (
    SearchRequest,
    ValidatedSearchInput,
    FilteredRecipes,
    RankedResults,
    SearchResponse,
)
from search.exceptions import (
    ValidationError,
    FilteringError,
    AggregationError,
    FormattingError,
)
from search.validation_module import validate_search_request

__all__ = [
    # Types
    "SearchRequest",
    "ValidatedSearchInput",
    "FilteredRecipes",
    "RankedResults",
    "SearchResponse",
    # Exceptions
    "ValidationError",
    "FilteringError",
    "AggregationError",
    "FormattingError",
    # Validation
    "validate_search_request",
]

__version__ = "1.0.0"
