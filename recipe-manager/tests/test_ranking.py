"""
Unit Tests for the Ranking Module (ranking.py)
"""
import pytest
from uuid import uuid4

from models import Recipe
from ranking import (
    calculate_relevance_score,
    calculate_popularity_score,
    rank_recipes,
    EXACT_NAME_SCORE,
    PARTIAL_NAME_SCORE,
    INGREDIENT_MATCH_SCORE,
    POPULARITY_WEIGHT,
)


def make_recipe(**kwargs) -> Recipe:
    defaults = dict(
        id=uuid4(),
        name="Generic Dish",
        ingredients=["water"],
        dietary_tags=[],
        cuisine="None",
        prep_time_minutes=20,
        difficulty="beginner",
        avg_rating=3.0,
    )
    defaults.update(kwargs)
    return Recipe(**defaults)


class TestCalculateRelevanceScore:
    def test_empty_query_returns_zero(self):
        recipe = make_recipe(name="Pasta")
        assert calculate_relevance_score(recipe, "") == 0.0

    def test_none_query_returns_zero(self):
        recipe = make_recipe(name="Pasta")
        assert calculate_relevance_score(recipe, None) == 0.0

    def test_exact_name_match(self):
        recipe = make_recipe(name="Spaghetti")
        score = calculate_relevance_score(recipe, "Spaghetti")
        assert score == EXACT_NAME_SCORE

    def test_partial_name_match(self):
        recipe = make_recipe(name="Spaghetti Carbonara")
        score = calculate_relevance_score(recipe, "spaghetti")
        assert score == PARTIAL_NAME_SCORE

    def test_ingredient_match(self):
        recipe = make_recipe(name="Something", ingredients=["pasta", "water"])
        score = calculate_relevance_score(recipe, "pasta")
        assert score == INGREDIENT_MATCH_SCORE

    def test_multiple_ingredient_matches(self):
        recipe = make_recipe(ingredients=["pasta", "pasta sauce", "parsley"])
        score = calculate_relevance_score(recipe, "pasta")
        assert score == INGREDIENT_MATCH_SCORE * 2  # matches "pasta" and "pasta sauce"


class TestCalculatePopularityScore:
    def test_popularity_is_rating_times_weight(self):
        recipe = make_recipe(avg_rating=4.0)
        expected = 4.0 * POPULARITY_WEIGHT
        assert abs(calculate_popularity_score(recipe) - expected) < 1e-9


class TestRankRecipes:
    def test_empty_list_returns_empty(self):
        assert rank_recipes([], "pasta") == []

    def test_no_query_sorts_by_rating_descending(self):
        low = make_recipe(avg_rating=2.0)
        high = make_recipe(avg_rating=4.8)
        mid = make_recipe(avg_rating=3.5)
        result = rank_recipes([low, mid, high], "")
        assert result[0] is high
        assert result[-1] is low

    def test_relevant_recipe_ranked_higher(self):
        relevant = make_recipe(name="Pasta Primavera", avg_rating=3.0)
        irrelevant = make_recipe(name="Beef Stew", avg_rating=4.9)
        result = rank_recipes([irrelevant, relevant], "pasta")
        assert result[0] is relevant
