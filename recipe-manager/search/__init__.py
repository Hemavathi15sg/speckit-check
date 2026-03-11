"""
Search Module Package

Modular refactoring of legacy search.py into 4 clean modules:
- validation_module: Input validation and normalization
- filtering_module: Recipe filtering by criteria
- aggregation_module: Ranking and caching
- formatting_module: Response formatting

Public API maintains full backward compatibility with legacy search.py:
    from search import search_recipes
    result = search_recipes(request_data, user)

Feature: 001-search-modular-refactor
Constitution: v1.0.0 (8 Principles)
"""
import logging
import time
from typing import Any, Dict, Optional

from models import Recipe, User, SAMPLE_RECIPES
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
from search.filtering_module import apply_filters
from search.aggregation_module import aggregate_and_rank
from search.formatting_module import format_response, to_legacy_dict

logger = logging.getLogger(__name__)


def search_recipes(request_data: Dict[str, Any], user: User) -> Dict[str, Any]:
    """
    Search recipes using the modular pipeline.

    This function is the public entry point with the same signature and
    response format as the legacy ``search_recipes()`` in search.py,
    ensuring 100% backward compatibility (SC-014, SC-015, FR-028).

    Pipeline:
        1. Validate & normalise input  (validation_module)
        2. Filter recipes              (filtering_module)
        3. Rank & cache results        (aggregation_module)
        4. Format API response         (formatting_module)

    Args:
        request_data: Raw request dict (may contain None values).
        user: Authenticated user (dietary_restrictions may be None).

    Returns:
        Dict with keys: results, page, page_size, total, has_more.

    Raises:
        ValidationError: When input cannot be normalised (e.g. unknown cuisine).

    Example:
        >>> result = search_recipes({"query": "pasta"}, user)
        >>> result["total"]
        1
    """
    pipeline_start = time.perf_counter()

    # 1. Build raw SearchRequest from request dict
    raw_request = SearchRequest(
        query=request_data.get("query"),
        cuisine=request_data.get("cuisine"),
        dietary_restrictions=request_data.get("dietary_restrictions"),
        prep_time_max=request_data.get("max_prep_time"),
        difficulty=request_data.get("difficulty"),
        min_rating=request_data.get("min_rating"),
        page=request_data.get("page", 1),
        page_size=request_data.get("page_size", 50),
    )

    # 2. Validate & normalise (fixes Issue #447 — dietary_restrictions=None)
    validated = validate_search_request(raw_request, user)

    # 3. Filter
    filtered = apply_filters(validated, SAMPLE_RECIPES)

    # 4. Rank & paginate (with bounded LRU cache)
    ranked = aggregate_and_rank(filtered, validated)

    # 5. Format
    total_duration_ms = (time.perf_counter() - pipeline_start) * 1000
    response = format_response(ranked, validated, total_duration_ms)

    logger.debug(
        "search_recipes completed in %.2fms (cache_hit=%s, results=%d)",
        total_duration_ms,
        response.metadata.get("cache_hit"),
        len(response.results),
    )

    return to_legacy_dict(response)


__all__ = [
    # Public API
    "search_recipes",
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
    # Module functions
    "validate_search_request",
    "apply_filters",
    "aggregate_and_rank",
    "format_response",
    "to_legacy_dict",
]

__version__ = "1.0.0"
