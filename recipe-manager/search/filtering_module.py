"""
Filtering Module
Applies validated search filters to the recipe dataset.
This module is the SECOND step in the search pipeline, after validation.

Data Flow:
    ValidatedSearchInput → apply_filters() → FilteredRecipes

Design Principles:
- Single responsibility: only filtering logic, no validation or ranking
- Optimal filter order: cheapest predicates first (FR-012)
- Short-circuit: stops when recipe set reaches zero (FR-013)
- No magic numbers: all thresholds in constants.py (FR-026)
- Pure functions: no side effects, deterministic output (FR-014)

Performance Target: <20ms P50, <50ms P95 for 10k recipes
Line Count Target: ≤300 lines (currently: will be checked post-implementation)
"""
import logging
import time
from typing import List, Dict, Any, Optional

from models import Recipe
from search.types import ValidatedSearchInput, FilteredRecipes

logger = logging.getLogger(__name__)


def apply_filters(
    validated_input: ValidatedSearchInput,
    recipes: List[Recipe],
) -> FilteredRecipes:
    """
    Apply all active filters to the recipe dataset.

    Filters are applied in optimal order (cheapest predicate first) to
    minimise the number of comparisons. Each filter short-circuits when
    the remaining recipe set reaches zero.

    Args:
        validated_input: Fully validated search parameters (never None fields).
        recipes: Complete recipe dataset to filter.

    Returns:
        FilteredRecipes with matching recipes and performance metadata.

    Side Effects:
        None (pure function).

    Example:
        >>> from search.types import ValidatedSearchInput
        >>> validated = ValidatedSearchInput(query="pasta", ...)
        >>> result = apply_filters(validated, SAMPLE_RECIPES)
        >>> result.recipes  # Only recipes matching all criteria
    """
    start_time = time.perf_counter()
    total_before = len(recipes)
    applied: Dict[str, Any] = {}

    remaining = recipes

    # --- cheapest filters first ---

    # 1. Cuisine: single equality check
    if validated_input.cuisine is not None:
        remaining = _filter_by_cuisine(remaining, validated_input.cuisine)
        applied["cuisine"] = validated_input.cuisine
        logger.debug("After cuisine filter: %d recipes", len(remaining))
        if not remaining:
            return _make_result(remaining, applied, start_time, total_before)

    # 2. Difficulty: single equality check
    if validated_input.difficulty is not None:
        remaining = _filter_by_difficulty(remaining, validated_input.difficulty)
        applied["difficulty"] = validated_input.difficulty
        logger.debug("After difficulty filter: %d recipes", len(remaining))
        if not remaining:
            return _make_result(remaining, applied, start_time, total_before)

    # 3. Prep time: single numeric comparison
    if validated_input.prep_time_max is not None:
        remaining = _filter_by_prep_time(remaining, validated_input.prep_time_max)
        applied["prep_time_max"] = validated_input.prep_time_max
        logger.debug("After prep_time filter: %d recipes", len(remaining))
        if not remaining:
            return _make_result(remaining, applied, start_time, total_before)

    # 4. Rating: single numeric comparison
    if validated_input.min_rating > 0.0:
        remaining = _filter_by_rating(remaining, validated_input.min_rating)
        applied["min_rating"] = validated_input.min_rating
        logger.debug("After rating filter: %d recipes", len(remaining))
        if not remaining:
            return _make_result(remaining, applied, start_time, total_before)

    # 5. Dietary restrictions: set intersection (medium cost)
    if validated_input.dietary_restrictions:
        remaining = _filter_by_dietary_restrictions(
            remaining, validated_input.dietary_restrictions
        )
        applied["dietary_restrictions"] = validated_input.dietary_restrictions
        logger.debug("After dietary filter: %d recipes", len(remaining))
        if not remaining:
            return _make_result(remaining, applied, start_time, total_before)

    # 6. Query: text search across multiple fields (most expensive)
    if validated_input.query:
        remaining = _filter_by_query(remaining, validated_input.query)
        applied["query"] = validated_input.query
        logger.debug("After query filter: %d recipes", len(remaining))

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(
        "Filtering complete: %d/%d recipes in %.2fms",
        len(remaining),
        total_before,
        duration_ms,
    )
    return FilteredRecipes(
        recipes=remaining,
        applied_filters=applied,
        filter_duration_ms=duration_ms,
        total_before_filters=total_before,
    )


# ---------------------------------------------------------------------------
# Private filter helpers
# ---------------------------------------------------------------------------


def _filter_by_cuisine(recipes: List[Recipe], cuisine: str) -> List[Recipe]:
    """
    Keep recipes whose cuisine matches (case-insensitive).

    Args:
        recipes: Input recipe list.
        cuisine: Normalized cuisine string (already title-cased by validator).

    Returns:
        Recipes whose cuisine equals ``cuisine`` (case-insensitive).
    """
    cuisine_lower = cuisine.lower()
    return [r for r in recipes if r.cuisine.lower() == cuisine_lower]


def _filter_by_difficulty(recipes: List[Recipe], difficulty: str) -> List[Recipe]:
    """
    Keep recipes whose difficulty matches (case-insensitive).

    Args:
        recipes: Input recipe list.
        difficulty: Difficulty string (normalised to lowercase by validator,
                    but compared case-insensitively for robustness).

    Returns:
        Recipes whose difficulty equals ``difficulty`` (case-insensitive).
    """
    difficulty_lower = difficulty.lower()
    return [r for r in recipes if r.difficulty.lower() == difficulty_lower]


def _filter_by_prep_time(recipes: List[Recipe], max_minutes: int) -> List[Recipe]:
    """
    Keep recipes whose prep time is within the maximum.

    Args:
        recipes: Input recipe list.
        max_minutes: Maximum prep time in minutes (validated ≥1).

    Returns:
        Recipes whose prep_time_minutes ≤ max_minutes.
    """
    return [r for r in recipes if r.prep_time_minutes <= max_minutes]


def _filter_by_rating(recipes: List[Recipe], min_rating: float) -> List[Recipe]:
    """
    Keep recipes whose average rating meets the minimum.

    Args:
        recipes: Input recipe list.
        min_rating: Minimum rating threshold (validated 0.0–5.0).

    Returns:
        Recipes whose avg_rating ≥ min_rating.
    """
    return [r for r in recipes if r.avg_rating >= min_rating]


def _filter_by_dietary_restrictions(
    recipes: List[Recipe],
    restrictions: List[str],
) -> List[Recipe]:
    """
    Keep recipes that satisfy ALL specified dietary restrictions.

    A recipe satisfies a restriction when the restriction tag is present
    in the recipe's dietary_tags list.

    Note: ``restrictions`` is GUARANTEED non-None by the validation module
    (Issue #447 fix), so this function never needs a None check.

    Args:
        recipes: Input recipe list.
        restrictions: Non-empty list of required dietary tags (lowercased).

    Returns:
        Recipes that contain all requested dietary restriction tags.
    """
    restriction_set = set(restrictions)
    return [r for r in recipes if restriction_set.issubset(set(r.dietary_tags))]


def _filter_by_query(recipes: List[Recipe], query: str) -> List[Recipe]:
    """
    Keep recipes whose name or ingredients contain the query string.

    Performs case-insensitive substring matching against:
    - recipe name
    - each ingredient string

    Args:
        recipes: Input recipe list.
        query: Normalized query string (lowercased, stripped by validator).

    Returns:
        Recipes that match the query in name or ingredients.
    """
    results: List[Recipe] = []
    for recipe in recipes:
        if query in recipe.name.lower():
            results.append(recipe)
            continue
        if any(query in ingredient.lower() for ingredient in recipe.ingredients):
            results.append(recipe)
    return results


# ---------------------------------------------------------------------------
# Private helper
# ---------------------------------------------------------------------------


def _make_result(
    recipes: List[Recipe],
    applied: Dict[str, Any],
    start_time: float,
    total_before: int,
) -> FilteredRecipes:
    """Build a FilteredRecipes result with timing."""
    duration_ms = (time.perf_counter() - start_time) * 1000
    return FilteredRecipes(
        recipes=recipes,
        applied_filters=applied,
        filter_duration_ms=duration_ms,
        total_before_filters=total_before,
    )
