"""
Integration Tests for the Full Search Pipeline

Tests the complete validation → filtering → aggregation → formatting pipeline,
including backward compatibility with the legacy search_recipes() API.

Focus:
- Issue #447 fix end-to-end (null dietary restrictions no longer crash)
- Issue #183 fix (cache memory is bounded)
- Backward-compatible response format
"""
import pytest
from uuid import uuid4
from models import User, SAMPLE_RECIPES
from search import search_recipes
from search.aggregation_module import get_cache
from search.types import SearchRequest
from search.validation_module import validate_search_request
from search.filtering_module import apply_filters
from search.aggregation_module import aggregate_and_rank
from search.formatting_module import format_response, to_legacy_dict


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_cache():
    """Isolate cache state between tests."""
    get_cache().clear()
    yield
    get_cache().clear()


def make_user(dietary_restrictions=None):
    return User(
        id=uuid4(),
        name="Test User",
        email="test@example.com",
        dietary_restrictions=dietary_restrictions,
    )


# ---------------------------------------------------------------------------
# Issue #447 end-to-end fix
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_issue_447_prevented_end_to_end():
    """
    End-to-end: search_recipes() must not raise TypeError for any user,
    regardless of dietary_restrictions value.

    This test validates the full fix for Issue #447.
    """
    user_none = make_user(dietary_restrictions=None)
    user_empty = make_user(dietary_restrictions=[])
    user_valid = make_user(dietary_restrictions=["vegan"])

    for user in [user_none, user_empty, user_valid]:
        result = search_recipes({"query": "pasta"}, user)
        assert isinstance(result, dict), f"Expected dict for user {user.dietary_restrictions}"
        assert "results" in result
        assert "total" in result


@pytest.mark.integration
def test_validation_to_filtering_pipeline():
    """
    Validation output feeds correctly into filtering.
    Validated dietary_restrictions (never None) passes through filtering.
    """
    user = make_user(dietary_restrictions=None)
    request = SearchRequest(query="")
    validated = validate_search_request(request, user)

    # dietary_restrictions must be [] after validation (Issue #447 fix)
    assert validated.dietary_restrictions == []

    filtered = apply_filters(validated, SAMPLE_RECIPES)
    # All recipes should be returned (no restrictions active)
    assert len(filtered.recipes) == len(SAMPLE_RECIPES)


@pytest.mark.integration
def test_validation_filtering_aggregation_pipeline():
    """
    Full pipeline (validation → filtering → aggregation) returns correct results.
    """
    user = make_user(dietary_restrictions=["vegan"])
    request = SearchRequest(query="")
    validated = validate_search_request(request, user)
    filtered = apply_filters(validated, SAMPLE_RECIPES)
    ranked = aggregate_and_rank(filtered, validated)

    # Only vegan recipes should be in results
    for recipe in ranked.recipes:
        assert "vegan" in recipe.dietary_tags


# ---------------------------------------------------------------------------
# Issue #183 end-to-end fix (bounded cache)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_issue_183_memory_bounded():
    """
    Issue #183 fix: cache must stay bounded.

    Insert 1500 unique searches (> MAX_CACHE_SIZE=1000).
    Cache must never exceed MAX_CACHE_SIZE entries.
    """
    from search.constants import MAX_CACHE_SIZE

    cache = get_cache()
    for i in range(MAX_CACHE_SIZE + 500):
        cache.put(f"key_{i}", {"data": i})

    assert cache.size <= MAX_CACHE_SIZE, (
        f"Cache size {cache.size} exceeds MAX_CACHE_SIZE {MAX_CACHE_SIZE}"
    )


@pytest.mark.integration
def test_cache_persistence_across_calls():
    """
    Cache hit returns the same results on second call with identical parameters.
    """
    user = make_user(dietary_restrictions=None)
    request_data = {"query": "pasta", "cuisine": "Italian"}

    result1 = search_recipes(request_data, user)
    result2 = search_recipes(request_data, user)

    # Both calls must return the same results
    assert result1["results"] == result2["results"]
    assert result1["total"] == result2["total"]


# ---------------------------------------------------------------------------
# Backward compatibility tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_backward_compatibility_response_format():
    """
    search_recipes() must return the exact same response structure as
    the legacy search.py implementation (SC-014, SC-015).

    Required keys: results, page, page_size, total, has_more.
    """
    user = make_user(dietary_restrictions=None)
    result = search_recipes({"query": "pasta"}, user)

    assert "results" in result, "Missing 'results' key"
    assert "page" in result, "Missing 'page' key"
    assert "page_size" in result, "Missing 'page_size' key"
    assert "total" in result, "Missing 'total' key"
    assert "has_more" in result, "Missing 'has_more' key"

    assert isinstance(result["results"], list)
    assert isinstance(result["page"], int)
    assert isinstance(result["page_size"], int)
    assert isinstance(result["total"], int)
    assert isinstance(result["has_more"], bool)


@pytest.mark.integration
def test_end_to_end_search_pipeline():
    """
    Full pipeline returns correct results for a realistic search scenario.
    """
    user = make_user(dietary_restrictions=None)
    result = search_recipes({"query": "pasta", "cuisine": "Italian"}, user)

    assert result["total"] >= 1
    for recipe_dict in result["results"]:
        assert recipe_dict["cuisine"] == "Italian"
        assert "pasta" in recipe_dict["name"].lower() or any(
            "pasta" in ing for ing in recipe_dict.get("ingredients", [])
        )


@pytest.mark.integration
def test_empty_query_returns_all_matching_cuisine():
    """Empty query with cuisine filter returns all recipes of that cuisine."""
    user = make_user()
    result = search_recipes({"query": "", "cuisine": "Thai"}, user)

    for recipe_dict in result["results"]:
        assert recipe_dict["cuisine"] == "Thai"


@pytest.mark.integration
def test_dietary_filter_applied_correctly():
    """search_recipes filters out recipes not matching dietary restrictions."""
    user = make_user(dietary_restrictions=None)
    result = search_recipes({"dietary_restrictions": ["vegan"]}, user)

    for recipe_dict in result["results"]:
        assert "vegan" in recipe_dict["dietary_tags"]
