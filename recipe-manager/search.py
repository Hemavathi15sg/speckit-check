"""
FlavorHub Search Engine

Thin orchestration layer that coordinates validation, filtering, ranking,
and formatting. The 1 103-line God Object that existed here has been broken
into four focused modules:

  filtering.py   – all recipe-filter functions (fixes Issue #447)
  ranking.py     – relevance / popularity scoring and sort
  formatting.py  – response serialisation and pagination
  validation.py  – Pydantic-based input validation

This module wires those pieces together and exposes the single public entry
point ``search_recipes`` used by the API layer.
"""
from typing import Optional

from models import Recipe, User, SAMPLE_RECIPES
from validation import parse_and_validate
from filtering import apply_all_filters
from ranking import rank_recipes
from formatting import paginate_results


def search_recipes(request_data: dict, user: User) -> dict:
    """
    Execute a recipe search for the given user.

    Steps
    -----
    1. Validate and normalise the raw request dict.
    2. Apply filters (cuisine, difficulty, prep-time, rating, dietary).
    3. Rank the surviving recipes by relevance + rating + popularity.
    4. Paginate and serialise the ranked results.

    Returns a dict with ``results``, ``page``, ``page_size``, ``total``,
    and ``has_more`` keys.

    Previously this function also managed a database connection, a broken
    in-process cache, manual metric counters, and extensive debug prints.
    Those concerns have been removed or deferred to dedicated infrastructure.
    """
    filters = parse_and_validate(request_data)

    all_recipes: list[Recipe] = SAMPLE_RECIPES

    filtered = apply_all_filters(all_recipes, filters, user)
    ranked = rank_recipes(filtered, filters["query"])
    return paginate_results(ranked)
