"""
FlavorHub Response Formatting Module

Responsible for converting domain objects to API response dictionaries
and handling pagination. Extracted from the monolithic search.py.
"""
from __future__ import annotations

from models import Recipe

# Pagination settings
DEFAULT_PAGE_SIZE: int = 50
MAX_PAGE_SIZE: int = 200


def format_recipe_response(recipe: Recipe) -> dict:
    """Serialize a Recipe domain object to an API response dictionary."""
    return {
        "id": str(recipe.id),
        "name": recipe.name,
        "ingredients": recipe.ingredients,
        "dietary_tags": recipe.dietary_tags,
        "cuisine": recipe.cuisine,
        "prep_time_minutes": recipe.prep_time_minutes,
        "difficulty": recipe.difficulty,
        "rating": recipe.avg_rating,
    }


def paginate_results(recipes: list[Recipe], page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> dict:
    """
    Slice a ranked recipe list into a single API page.

    Returns a dict with ``results``, ``page``, ``page_size``, ``total``,
    and ``has_more`` fields.

    Note: page and page_size are clamped to safe values so that callers
    cannot request unreasonably large pages.
    """
    page = max(1, page)
    page_size = min(max(1, page_size), MAX_PAGE_SIZE)

    start = (page - 1) * page_size
    end = start + page_size
    page_recipes = recipes[start:end]

    return {
        "results": [format_recipe_response(r) for r in page_recipes],
        "page": page,
        "page_size": page_size,
        "total": len(recipes),
        "has_more": end < len(recipes),
    }
