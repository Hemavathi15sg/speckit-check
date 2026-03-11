"""
Formatting Module
Converts internal search results into the public API response format.
This module is the FOURTH and final step in the search pipeline.

Data Flow:
    RankedResults + ValidatedSearchInput → format_response() → SearchResponse

Design Principles:
- Single responsibility: only response formatting, no business logic
- Backward compatible: response dict matches legacy search.py output exactly
- No magic numbers: field names and structure defined by the type contract
- Graceful handling of empty result sets

Performance Target: <5ms P50
Line Count Target: ≤300 lines
"""
import logging
import math
import time
from typing import Any, Dict, List

from models import Recipe
from search.types import RankedResults, SearchResponse, ValidatedSearchInput

logger = logging.getLogger(__name__)


def format_response(
    ranked: RankedResults,
    validated_input: ValidatedSearchInput,
    total_duration_ms: float,
) -> SearchResponse:
    """
    Format ranked results into the public API response.

    The response structure is backward-compatible with the legacy
    ``search_recipes()`` return value so that existing API consumers
    require no changes.

    Args:
        ranked: Output of aggregation_module (page of recipes + metadata).
        validated_input: Validated parameters (used for pagination metadata).
        total_duration_ms: End-to-end pipeline duration for observability.

    Returns:
        SearchResponse containing formatted recipes, pagination, and metadata.

    Side Effects:
        None (pure function).

    Example:
        >>> response = format_response(ranked, validated_input, 12.5)
        >>> response.results[0]["id"]  # UUID as string
        '...'
    """
    start_time = time.perf_counter()

    formatted_recipes = [_format_recipe(recipe) for recipe in ranked.recipes]

    pagination = _build_pagination(
        page=ranked.page,
        page_size=ranked.page_size,
        total=ranked.total_results,
        total_pages=ranked.total_pages,
    )

    metadata = _build_metadata(
        cache_hit=ranked.cache_hit,
        ranking_duration_ms=ranked.ranking_duration_ms,
        total_duration_ms=total_duration_ms,
        cache_key=ranked.cache_key,
    )

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(
        "Formatted %d recipes in %.2fms (cache_hit=%s)",
        len(formatted_recipes),
        duration_ms,
        ranked.cache_hit,
    )

    return SearchResponse(
        results=formatted_recipes,
        pagination=pagination,
        metadata=metadata,
        total_duration_ms=total_duration_ms,
    )


def to_legacy_dict(response: SearchResponse) -> Dict[str, Any]:
    """
    Convert a SearchResponse into the legacy dict format returned by search.py.

    Maintains 100% backward compatibility with the existing ``search_recipes()``
    response shape so that API consumers do not need to change.

    Args:
        response: Fully formatted SearchResponse.

    Returns:
        Dict with keys: results, page, page_size, total, has_more.
    """
    pagination = response.pagination
    return {
        "results": response.results,
        "page": pagination["page"],
        "page_size": pagination["page_size"],
        "total": pagination["total"],
        "has_more": pagination["has_more"],
    }


# ---------------------------------------------------------------------------
# Private formatting helpers
# ---------------------------------------------------------------------------


def _format_recipe(recipe: Recipe) -> Dict[str, Any]:
    """
    Convert a Recipe object to an API-ready dict.

    Field mapping:
    - id: UUID → str
    - rating: avg_rating rounded to 1 decimal place
    - All other fields preserved as-is

    Args:
        recipe: Recipe domain object.

    Returns:
        Dict representation suitable for JSON serialisation.
    """
    return {
        "id": str(recipe.id),
        "name": recipe.name,
        "ingredients": list(recipe.ingredients),
        "dietary_tags": list(recipe.dietary_tags),
        "cuisine": recipe.cuisine,
        "prep_time_minutes": recipe.prep_time_minutes,
        "difficulty": recipe.difficulty,
        "rating": round(recipe.avg_rating, 1),
    }


def _build_pagination(
    page: int,
    page_size: int,
    total: int,
    total_pages: int,
) -> Dict[str, Any]:
    """
    Build pagination metadata dict.

    Args:
        page: Current 1-based page number.
        page_size: Results per page.
        total: Total matching results.
        total_pages: Total available pages.

    Returns:
        Pagination dict with keys: page, page_size, total, total_pages, has_more.
    """
    end = page * page_size
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_more": end < total,
    }


def _build_metadata(
    cache_hit: bool,
    ranking_duration_ms: float,
    total_duration_ms: float,
    cache_key: str,
) -> Dict[str, Any]:
    """
    Build response metadata for observability.

    Args:
        cache_hit: Whether results came from cache.
        ranking_duration_ms: Time spent on ranking (0 on cache hit).
        total_duration_ms: End-to-end pipeline duration.
        cache_key: Cache key used (for debugging).

    Returns:
        Metadata dict.
    """
    return {
        "cache_hit": cache_hit,
        "ranking_duration_ms": round(ranking_duration_ms, 2),
        "total_duration_ms": round(total_duration_ms, 2),
        "cache_key": cache_key,
    }
