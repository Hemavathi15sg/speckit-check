"""
FlavorHub Search Filtering Module

Responsible for all recipe filtering logic. Extracted from the monolithic
search.py to address the God Object anti-pattern.

Fixes Issue #447: null dietary restrictions crash (filter_by_dietary).
"""
from __future__ import annotations

from typing import Optional

from models import Recipe, User


def filter_by_query(recipes: list[Recipe], query: str) -> list[Recipe]:
    """Filter recipes whose name or ingredients match the search query."""
    if not query:
        return recipes

    query_lower = query.lower()
    results = []
    for recipe in recipes:
        if query_lower in recipe.name.lower():
            results.append(recipe)
            continue
        if any(query_lower in ingredient.lower() for ingredient in recipe.ingredients):
            results.append(recipe)
    return results


def filter_by_cuisine(recipes: list[Recipe], cuisine: Optional[str]) -> list[Recipe]:
    """Filter recipes by cuisine type (case-insensitive)."""
    if not cuisine:
        return recipes
    return [r for r in recipes if r.cuisine.lower() == cuisine.lower()]


def filter_by_prep_time(recipes: list[Recipe], max_time: Optional[int]) -> list[Recipe]:
    """Filter recipes by maximum preparation time in minutes."""
    if max_time is None:
        return recipes
    try:
        return [r for r in recipes if r.prep_time_minutes <= max_time]
    except TypeError:
        return recipes


def filter_by_difficulty(recipes: list[Recipe], difficulty: Optional[str]) -> list[Recipe]:
    """Filter recipes by difficulty level (case-insensitive)."""
    if not difficulty:
        return recipes
    return [r for r in recipes if r.difficulty.lower() == difficulty.lower()]


def filter_by_rating(recipes: list[Recipe], min_rating: float) -> list[Recipe]:
    """Filter recipes that meet or exceed the minimum average rating."""
    if not min_rating:
        return recipes
    try:
        return [r for r in recipes if r.avg_rating >= min_rating]
    except (TypeError, AttributeError):
        return recipes


def filter_by_dietary(recipes: list[Recipe], user: User) -> list[Recipe]:
    """
    Filter recipes based on a user's dietary restrictions.

    Fixes Issue #447: user.dietary_restrictions can be None for users who
    have not set any preferences. When None, no dietary filtering is applied
    and all recipes are returned as-is.
    """
    restrictions = user.dietary_restrictions or []
    for restriction in restrictions:
        recipes = [r for r in recipes if restriction in r.dietary_tags]
    return recipes


def apply_all_filters(recipes: list[Recipe], filters: dict, user: User) -> list[Recipe]:
    """
    Apply every active filter to the recipe list in an efficient order.

    Filters are applied from most-selective to least-selective to reduce
    the number of recipes processed by later, more expensive steps.
    """
    results = recipes

    # Apply most-selective filters first to prune the result set early
    if filters.get("cuisine"):
        results = filter_by_cuisine(results, filters["cuisine"])

    if filters.get("difficulty"):
        results = filter_by_difficulty(results, filters["difficulty"])

    if filters.get("max_prep_time") is not None:
        results = filter_by_prep_time(results, filters["max_prep_time"])

    if filters.get("min_rating"):
        results = filter_by_rating(results, filters["min_rating"])

    results = filter_by_dietary(results, user)

    # Full-text query match is O(n*m) so run last on the pruned set
    if filters.get("query"):
        results = filter_by_query(results, filters["query"])

    return results
