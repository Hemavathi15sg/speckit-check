"""
FlavorHub Search Ranking Module

Responsible for scoring and ordering recipe results. Extracted from the
monolithic search.py to address the God Object anti-pattern.

Named constants replace the magic numbers that were scattered through
the original implementation.
"""
from __future__ import annotations

from models import Recipe

# Scoring weights for the hybrid ranking algorithm
RELEVANCE_WEIGHT: float = 0.45
RATING_WEIGHT: float = 0.30
POPULARITY_WEIGHT: float = 0.25

# Relevance score contributions
EXACT_NAME_SCORE: float = 10.0
PARTIAL_NAME_SCORE: float = 5.0
INGREDIENT_MATCH_SCORE: float = 2.0

# Active ranking algorithm
RANKING_ALGORITHM: str = "hybrid_v3"


def calculate_relevance_score(recipe: Recipe, query: str) -> float:
    """
    Return a relevance score for a recipe against a search query.

    Scoring:
    - Exact name match  → +10.0
    - Partial name match → +5.0
    - Each ingredient match → +2.0
    """
    if not query:
        return 0.0

    score = 0.0
    query_lower = query.lower()

    if query_lower == recipe.name.lower():
        score += EXACT_NAME_SCORE
    elif query_lower in recipe.name.lower():
        score += PARTIAL_NAME_SCORE

    ingredient_matches = sum(1 for ing in recipe.ingredients if query_lower in ing.lower())
    score += ingredient_matches * INGREDIENT_MATCH_SCORE

    return score


def calculate_popularity_score(recipe: Recipe) -> float:
    """Return a popularity score based on the recipe's average rating."""
    return recipe.avg_rating * POPULARITY_WEIGHT


def rank_recipes(recipes: list[Recipe], query: str) -> list[Recipe]:
    """
    Rank recipes using the hybrid_v3 algorithm: a weighted combination of
    relevance, rating, and popularity scores.

    When no query string is supplied the recipes are sorted by rating alone.
    """
    if not recipes:
        return recipes

    if not query:
        return sorted(recipes, key=lambda r: r.avg_rating, reverse=True)

    scored: list[tuple] = []
    for recipe in recipes:
        relevance = calculate_relevance_score(recipe, query)
        score = (
            relevance * RELEVANCE_WEIGHT
            + recipe.avg_rating * RATING_WEIGHT
            + calculate_popularity_score(recipe)
        )
        scored.append((score, recipe))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [recipe for _, recipe in scored]
