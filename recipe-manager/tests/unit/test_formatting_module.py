"""
Unit Tests for Formatting Module

Tests search/formatting_module.py functions.

Test Coverage Target: ≥80%
Constitution Principle III: Testability
"""
import json
import pytest
from uuid import UUID, uuid4
from models import Recipe
from search.formatting_module import (
    format_response,
    to_legacy_dict,
    _format_recipe,
    _build_pagination,
)
from search.types import RankedResults, ValidatedSearchInput


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_recipe(
    name="Test Recipe",
    avg_rating=4.5,
    dietary_tags=None,
    ingredients=None,
) -> Recipe:
    return Recipe(
        id=uuid4(),
        name=name,
        ingredients=ingredients if ingredients is not None else ["ingredient"],
        dietary_tags=dietary_tags if dietary_tags is not None else [],
        cuisine="Italian",
        prep_time_minutes=20,
        difficulty="easy",
        avg_rating=avg_rating,
    )


def make_ranked(
    recipes=None,
    total: int = 0,
    page: int = 1,
    page_size: int = 50,
    cache_hit: bool = False,
    ranking_duration_ms: float = 5.0,
    cache_key: str = "test-key",
) -> RankedResults:
    r = recipes or []
    total = total or len(r)
    import math
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return RankedResults(
        recipes=r,
        total_results=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        cache_hit=cache_hit,
        ranking_duration_ms=ranking_duration_ms,
        cache_key=cache_key,
    )


def make_validated(page: int = 1, page_size: int = 50) -> ValidatedSearchInput:
    return ValidatedSearchInput(
        query="",
        cuisine=None,
        dietary_restrictions=[],
        prep_time_max=None,
        difficulty=None,
        min_rating=0.0,
        page=page,
        page_size=page_size,
        user_id="user-1",
    )


# ---------------------------------------------------------------------------
# Recipe formatting tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_format_recipe_converts_uuid_to_string():
    """Recipe ID (UUID) is converted to a string in the formatted output."""
    recipe = make_recipe()
    result = _format_recipe(recipe)
    assert isinstance(result["id"], str)
    # Must be a valid UUID string
    UUID(result["id"])


@pytest.mark.unit
def test_format_recipe_rounds_rating():
    """avg_rating is rounded to 1 decimal place."""
    recipe = make_recipe(avg_rating=4.567)
    result = _format_recipe(recipe)
    assert result["rating"] == 4.6


@pytest.mark.unit
def test_format_recipe_preserves_all_fields():
    """All expected fields are present in the formatted recipe dict."""
    recipe = make_recipe(name="Pasta", ingredients=["pasta", "eggs"])
    result = _format_recipe(recipe)
    required_keys = {"id", "name", "ingredients", "dietary_tags", "cuisine",
                     "prep_time_minutes", "difficulty", "rating"}
    assert required_keys.issubset(result.keys())


@pytest.mark.unit
def test_format_recipe_handles_empty_lists():
    """Recipes with empty ingredient/tag lists are formatted correctly."""
    recipe = make_recipe(ingredients=[], dietary_tags=[])
    result = _format_recipe(recipe)
    assert result["ingredients"] == []
    assert result["dietary_tags"] == []


@pytest.mark.unit
def test_json_serialization():
    """Formatted recipe dict is JSON-serializable."""
    recipe = make_recipe()
    result = _format_recipe(recipe)
    serialized = json.dumps(result)
    assert isinstance(serialized, str)


# ---------------------------------------------------------------------------
# Response formatting tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_format_response_populates_all_fields():
    """format_response returns a SearchResponse with all required fields."""
    recipe = make_recipe()
    ranked = make_ranked(recipes=[recipe])
    validated = make_validated()

    response = format_response(ranked, validated, total_duration_ms=10.0)

    assert len(response.results) == 1
    assert "page" in response.pagination
    assert "total" in response.pagination
    assert "cache_hit" in response.metadata
    assert response.total_duration_ms == 10.0


@pytest.mark.unit
def test_format_response_empty_recipes():
    """format_response handles an empty recipe list gracefully."""
    ranked = make_ranked(recipes=[], total=0)
    validated = make_validated()

    response = format_response(ranked, validated, total_duration_ms=5.0)

    assert response.results == []
    assert response.pagination["total"] == 0


@pytest.mark.unit
def test_format_response_single_page():
    """Pagination metadata is correct for a single page."""
    recipes = [make_recipe(name=str(i)) for i in range(3)]
    ranked = make_ranked(recipes=recipes, total=3, page=1, page_size=50)
    validated = make_validated()

    response = format_response(ranked, validated, total_duration_ms=8.0)

    assert response.pagination["total_pages"] == 1
    assert response.pagination["has_more"] is False


@pytest.mark.unit
def test_format_response_multiple_pages():
    """has_more is True when there are more pages available."""
    recipes = [make_recipe(name=str(i)) for i in range(5)]
    ranked = make_ranked(recipes=recipes[:2], total=5, page=1, page_size=2)
    import math
    total_pages = math.ceil(5 / 2)
    ranked = RankedResults(
        recipes=recipes[:2],
        total_results=5,
        page=1,
        page_size=2,
        total_pages=total_pages,
        cache_hit=False,
        ranking_duration_ms=1.0,
        cache_key="key",
    )
    validated = make_validated(page_size=2)

    response = format_response(ranked, validated, total_duration_ms=8.0)

    assert response.pagination["has_more"] is True
    assert response.pagination["total_pages"] == 3


@pytest.mark.unit
def test_format_response_cache_hit_preserved():
    """cache_hit flag is preserved in response metadata."""
    ranked = make_ranked(recipes=[make_recipe()], cache_hit=True)
    validated = make_validated()

    response = format_response(ranked, validated, total_duration_ms=2.0)

    assert response.metadata["cache_hit"] is True


@pytest.mark.unit
def test_format_response_duration_preserved():
    """total_duration_ms is stored in the response."""
    ranked = make_ranked(recipes=[make_recipe()])
    validated = make_validated()

    response = format_response(ranked, validated, total_duration_ms=42.5)

    assert response.total_duration_ms == 42.5


# ---------------------------------------------------------------------------
# Legacy dict conversion tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_to_legacy_dict_has_required_keys():
    """to_legacy_dict returns a dict with the legacy response keys."""
    ranked = make_ranked(recipes=[make_recipe()])
    validated = make_validated()
    response = format_response(ranked, validated, total_duration_ms=5.0)

    legacy = to_legacy_dict(response)

    assert "results" in legacy
    assert "page" in legacy
    assert "page_size" in legacy
    assert "total" in legacy
    assert "has_more" in legacy


@pytest.mark.unit
def test_to_legacy_dict_results_match():
    """to_legacy_dict results list matches format_response results."""
    recipe = make_recipe(name="Pasta")
    ranked = make_ranked(recipes=[recipe])
    validated = make_validated()
    response = format_response(ranked, validated, total_duration_ms=5.0)

    legacy = to_legacy_dict(response)

    assert legacy["results"] == response.results
    assert legacy["results"][0]["name"] == "Pasta"
