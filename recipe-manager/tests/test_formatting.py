"""
Unit Tests for the Formatting Module (formatting.py)
"""
import pytest
from uuid import uuid4

from models import Recipe
from formatting import format_recipe_response, paginate_results, DEFAULT_PAGE_SIZE


def make_recipe(**kwargs) -> Recipe:
    defaults = dict(
        id=uuid4(),
        name="Test Recipe",
        ingredients=["a", "b"],
        dietary_tags=["vegan"],
        cuisine="Italian",
        prep_time_minutes=25,
        difficulty="beginner",
        avg_rating=4.0,
    )
    defaults.update(kwargs)
    return Recipe(**defaults)


class TestFormatRecipeResponse:
    def test_required_fields_present(self):
        recipe = make_recipe()
        result = format_recipe_response(recipe)
        for field in ("id", "name", "ingredients", "dietary_tags", "cuisine",
                      "prep_time_minutes", "difficulty", "rating"):
            assert field in result, f"Missing field: {field}"

    def test_id_is_string(self):
        recipe = make_recipe()
        result = format_recipe_response(recipe)
        assert isinstance(result["id"], str)

    def test_rating_maps_avg_rating(self):
        recipe = make_recipe(avg_rating=4.7)
        result = format_recipe_response(recipe)
        assert result["rating"] == 4.7


class TestPaginateResults:
    def test_empty_list(self):
        result = paginate_results([])
        assert result["total"] == 0
        assert result["results"] == []
        assert result["has_more"] is False

    def test_first_page(self):
        recipes = [make_recipe() for _ in range(5)]
        result = paginate_results(recipes, page=1, page_size=3)
        assert len(result["results"]) == 3
        assert result["total"] == 5
        assert result["has_more"] is True

    def test_last_page(self):
        recipes = [make_recipe() for _ in range(5)]
        result = paginate_results(recipes, page=2, page_size=3)
        assert len(result["results"]) == 2
        assert result["has_more"] is False

    def test_page_size_clamped_to_max(self):
        recipes = [make_recipe() for _ in range(10)]
        result = paginate_results(recipes, page=1, page_size=999999)
        assert result["page_size"] <= 200

    def test_default_page_size_applied(self):
        recipes = [make_recipe() for _ in range(10)]
        result = paginate_results(recipes)
        assert result["page_size"] == DEFAULT_PAGE_SIZE
