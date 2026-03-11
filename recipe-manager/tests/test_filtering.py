"""
Unit Tests for the Filtering Module (filtering.py)

Validates every filter function and specifically tests the Issue #447 fix
(null dietary restrictions must not crash).
"""
import pytest
from uuid import uuid4

from models import User, Recipe
from filtering import (
    filter_by_query,
    filter_by_cuisine,
    filter_by_prep_time,
    filter_by_difficulty,
    filter_by_rating,
    filter_by_dietary,
    apply_all_filters,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_recipe(**kwargs) -> Recipe:
    defaults = dict(
        id=uuid4(),
        name="Test Recipe",
        ingredients=["flour", "water"],
        dietary_tags=[],
        cuisine="American",
        prep_time_minutes=30,
        difficulty="intermediate",
        avg_rating=3.0,
    )
    defaults.update(kwargs)
    return Recipe(**defaults)


def make_user(dietary_restrictions=None) -> User:
    return User(
        id=uuid4(),
        name="Tester",
        email="tester@example.com",
        dietary_restrictions=dietary_restrictions,
    )


# ---------------------------------------------------------------------------
# filter_by_query
# ---------------------------------------------------------------------------

class TestFilterByQuery:
    def test_empty_query_returns_all(self):
        recipes = [make_recipe(name="Pasta"), make_recipe(name="Salad")]
        assert filter_by_query(recipes, "") == recipes

    def test_none_query_returns_all(self):
        recipes = [make_recipe(name="Pasta")]
        assert filter_by_query(recipes, None) == recipes

    def test_matches_recipe_name(self):
        pasta = make_recipe(name="Spaghetti Carbonara")
        salad = make_recipe(name="Caesar Salad")
        result = filter_by_query([pasta, salad], "spaghetti")
        assert pasta in result
        assert salad not in result

    def test_matches_ingredient(self):
        recipe = make_recipe(name="Plain Rice", ingredients=["rice", "water", "salt"])
        other = make_recipe(name="Noodles", ingredients=["noodles", "broth"])
        result = filter_by_query([recipe, other], "rice")
        assert recipe in result
        assert other not in result

    def test_case_insensitive(self):
        recipe = make_recipe(name="PASTA")
        result = filter_by_query([recipe], "pasta")
        assert recipe in result


# ---------------------------------------------------------------------------
# filter_by_cuisine
# ---------------------------------------------------------------------------

class TestFilterByCuisine:
    def test_no_cuisine_returns_all(self):
        recipes = [make_recipe(cuisine="Italian"), make_recipe(cuisine="Thai")]
        assert filter_by_cuisine(recipes, None) == recipes

    def test_filters_by_cuisine(self):
        italian = make_recipe(cuisine="Italian")
        thai = make_recipe(cuisine="Thai")
        result = filter_by_cuisine([italian, thai], "Italian")
        assert italian in result
        assert thai not in result

    def test_case_insensitive(self):
        recipe = make_recipe(cuisine="Italian")
        result = filter_by_cuisine([recipe], "ITALIAN")
        assert recipe in result


# ---------------------------------------------------------------------------
# filter_by_prep_time
# ---------------------------------------------------------------------------

class TestFilterByPrepTime:
    def test_no_max_time_returns_all(self):
        recipes = [make_recipe(prep_time_minutes=10), make_recipe(prep_time_minutes=90)]
        assert filter_by_prep_time(recipes, None) == recipes

    def test_filters_by_max_time(self):
        fast = make_recipe(prep_time_minutes=15)
        slow = make_recipe(prep_time_minutes=60)
        result = filter_by_prep_time([fast, slow], 30)
        assert fast in result
        assert slow not in result

    def test_exact_max_time_included(self):
        recipe = make_recipe(prep_time_minutes=30)
        assert recipe in filter_by_prep_time([recipe], 30)


# ---------------------------------------------------------------------------
# filter_by_difficulty
# ---------------------------------------------------------------------------

class TestFilterByDifficulty:
    def test_no_difficulty_returns_all(self):
        recipes = [make_recipe(difficulty="easy"), make_recipe(difficulty="hard")]
        assert filter_by_difficulty(recipes, None) == recipes

    def test_filters_by_difficulty(self):
        easy = make_recipe(difficulty="beginner")
        hard = make_recipe(difficulty="advanced")
        result = filter_by_difficulty([easy, hard], "beginner")
        assert easy in result
        assert hard not in result

    def test_case_insensitive(self):
        recipe = make_recipe(difficulty="Intermediate")
        result = filter_by_difficulty([recipe], "intermediate")
        assert recipe in result


# ---------------------------------------------------------------------------
# filter_by_rating
# ---------------------------------------------------------------------------

class TestFilterByRating:
    def test_zero_min_rating_returns_all(self):
        recipes = [make_recipe(avg_rating=1.0), make_recipe(avg_rating=5.0)]
        assert filter_by_rating(recipes, 0.0) == recipes

    def test_filters_by_min_rating(self):
        low = make_recipe(avg_rating=2.5)
        high = make_recipe(avg_rating=4.5)
        result = filter_by_rating([low, high], 4.0)
        assert high in result
        assert low not in result


# ---------------------------------------------------------------------------
# filter_by_dietary  ← THE BUG FIX (Issue #447)
# ---------------------------------------------------------------------------

class TestFilterByDietary:
    def test_none_restrictions_returns_all_recipes(self):
        """
        Issue #447 fix: user with dietary_restrictions=None must not crash.
        All recipes are returned unchanged.
        """
        user = make_user(dietary_restrictions=None)
        recipes = [
            make_recipe(dietary_tags=["vegan"]),
            make_recipe(dietary_tags=[]),
        ]
        result = filter_by_dietary(recipes, user)
        assert result == recipes

    def test_empty_restrictions_returns_all_recipes(self):
        user = make_user(dietary_restrictions=[])
        recipes = [make_recipe(dietary_tags=["vegan"]), make_recipe(dietary_tags=[])]
        result = filter_by_dietary(recipes, user)
        assert result == recipes

    def test_restriction_filters_correctly(self):
        user = make_user(dietary_restrictions=["vegan"])
        vegan = make_recipe(dietary_tags=["vegan", "gluten-free"])
        non_vegan = make_recipe(dietary_tags=["gluten-free"])
        result = filter_by_dietary([vegan, non_vegan], user)
        assert vegan in result
        assert non_vegan not in result

    def test_multiple_restrictions_all_must_match(self):
        user = make_user(dietary_restrictions=["vegan", "gluten-free"])
        both = make_recipe(dietary_tags=["vegan", "gluten-free"])
        only_vegan = make_recipe(dietary_tags=["vegan"])
        result = filter_by_dietary([both, only_vegan], user)
        assert both in result
        assert only_vegan not in result


# ---------------------------------------------------------------------------
# apply_all_filters
# ---------------------------------------------------------------------------

class TestApplyAllFilters:
    def test_no_filters_returns_all(self):
        user = make_user()
        recipes = [make_recipe(), make_recipe()]
        filters = {
            "query": "",
            "cuisine": None,
            "max_prep_time": None,
            "difficulty": None,
            "min_rating": 0.0,
        }
        result = apply_all_filters(recipes, filters, user)
        assert result == recipes

    def test_null_dietary_user_does_not_crash(self):
        """Integration check: apply_all_filters must not raise for None dietary user."""
        user = make_user(dietary_restrictions=None)
        recipes = [make_recipe()]
        filters = {
            "query": "",
            "cuisine": None,
            "max_prep_time": None,
            "difficulty": None,
            "min_rating": 0.0,
        }
        result = apply_all_filters(recipes, filters, user)
        assert isinstance(result, list)

    def test_combined_filters(self):
        user = make_user()
        match = make_recipe(
            name="Vegan Pasta",
            cuisine="Italian",
            prep_time_minutes=20,
            difficulty="beginner",
            avg_rating=4.5,
            dietary_tags=["vegan"],
        )
        no_match = make_recipe(
            name="Beef Stew",
            cuisine="American",
            prep_time_minutes=90,
            difficulty="advanced",
            avg_rating=2.0,
        )
        filters = {
            "query": "pasta",
            "cuisine": "Italian",
            "max_prep_time": 30,
            "difficulty": "beginner",
            "min_rating": 4.0,
        }
        result = apply_all_filters([match, no_match], filters, user)
        assert match in result
        assert no_match not in result
