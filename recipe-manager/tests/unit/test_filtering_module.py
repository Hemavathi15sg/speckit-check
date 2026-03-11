"""
Unit Tests for Filtering Module

Tests search/filtering_module.py functions.

Test Coverage Target: ≥80%
Constitution Principle III: Testability
"""
import pytest
from uuid import uuid4
from models import Recipe, User
from search.filtering_module import (
    apply_filters,
    _filter_by_query,
    _filter_by_cuisine,
    _filter_by_dietary_restrictions,
    _filter_by_prep_time,
    _filter_by_difficulty,
    _filter_by_rating,
)
from search.types import ValidatedSearchInput


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_validated(
    query: str = "",
    cuisine=None,
    dietary_restrictions=None,
    prep_time_max=None,
    difficulty=None,
    min_rating: float = 0.0,
    page: int = 1,
    page_size: int = 50,
    user_id: str = "test-user",
) -> ValidatedSearchInput:
    return ValidatedSearchInput(
        query=query,
        cuisine=cuisine,
        dietary_restrictions=dietary_restrictions or [],
        prep_time_max=prep_time_max,
        difficulty=difficulty,
        min_rating=min_rating,
        page=page,
        page_size=page_size,
        user_id=user_id,
    )


def make_recipe(
    name="Test Recipe",
    ingredients=None,
    dietary_tags=None,
    cuisine="Italian",
    prep_time_minutes=30,
    difficulty="intermediate",
    avg_rating=4.0,
) -> Recipe:
    return Recipe(
        id=uuid4(),
        name=name,
        ingredients=ingredients or ["ingredient1"],
        dietary_tags=dietary_tags or [],
        cuisine=cuisine,
        prep_time_minutes=prep_time_minutes,
        difficulty=difficulty,
        avg_rating=avg_rating,
    )


# ---------------------------------------------------------------------------
# Query filter tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_query_filter_matches_name():
    """Filter returns recipe when query matches recipe name."""
    recipe = make_recipe(name="Spaghetti Carbonara")
    result = _filter_by_query([recipe], "spaghetti")
    assert len(result) == 1
    assert result[0].name == "Spaghetti Carbonara"


@pytest.mark.unit
def test_query_filter_matches_ingredient():
    """Filter returns recipe when query matches an ingredient."""
    recipe = make_recipe(name="Pasta Dish", ingredients=["pasta", "eggs", "bacon"])
    result = _filter_by_query([recipe], "eggs")
    assert len(result) == 1


@pytest.mark.unit
def test_query_filter_empty_returns_all():
    """Empty query string returns all recipes (no filter applied)."""
    recipes = [make_recipe(name="A"), make_recipe(name="B")]
    result = _filter_by_query(recipes, "")
    assert len(result) == 2


@pytest.mark.unit
def test_query_filter_no_match_returns_empty():
    """Query with no match returns empty list."""
    recipe = make_recipe(name="Pasta", ingredients=["pasta"])
    result = _filter_by_query([recipe], "sushi")
    assert result == []


@pytest.mark.unit
def test_query_filter_case_insensitive():
    """Query filtering is case-insensitive."""
    recipe = make_recipe(name="Vegan Buddha Bowl")
    result = _filter_by_query([recipe], "buddha")
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Cuisine filter tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_cuisine_filter_exact_match():
    """Filter returns recipe with matching cuisine."""
    recipe = make_recipe(cuisine="Italian")
    result = _filter_by_cuisine([recipe], "Italian")
    assert len(result) == 1


@pytest.mark.unit
def test_cuisine_filter_none_returns_all():
    """When cuisine is None, apply_filters skips cuisine filter."""
    recipes = [make_recipe(cuisine="Italian"), make_recipe(cuisine="Thai")]
    validated = make_validated(cuisine=None)
    result = apply_filters(validated, recipes)
    assert len(result.recipes) == 2


@pytest.mark.unit
def test_cuisine_filter_case_insensitive():
    """Cuisine filtering is case-insensitive."""
    recipe = make_recipe(cuisine="Italian")
    result = _filter_by_cuisine([recipe], "italian")
    assert len(result) == 1


@pytest.mark.unit
def test_cuisine_filter_no_match():
    """Cuisine filter returns empty list for non-matching cuisine."""
    recipe = make_recipe(cuisine="Italian")
    result = _filter_by_cuisine([recipe], "Thai")
    assert result == []


# ---------------------------------------------------------------------------
# Dietary restrictions filter tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_dietary_restrictions_all_required():
    """Recipe must have ALL dietary restriction tags."""
    vegan_gf_recipe = make_recipe(dietary_tags=["vegan", "gluten-free"])
    vegan_only_recipe = make_recipe(dietary_tags=["vegan"])

    result = _filter_by_dietary_restrictions(
        [vegan_gf_recipe, vegan_only_recipe], ["vegan", "gluten-free"]
    )
    assert len(result) == 1
    assert vegan_gf_recipe in result


@pytest.mark.unit
def test_dietary_restrictions_empty_returns_all():
    """When restrictions list is empty, apply_filters skips dietary filter."""
    recipes = [make_recipe(dietary_tags=[]), make_recipe(dietary_tags=["vegan"])]
    validated = make_validated(dietary_restrictions=[])
    result = apply_filters(validated, recipes)
    assert len(result.recipes) == 2


@pytest.mark.unit
def test_dietary_restrictions_never_none(sample_user_without_dietary):
    """
    Issue #447 prevented end-to-end: dietary_restrictions=None never
    reaches _filter_by_dietary_restrictions because validation normalises it.
    """
    from search.validation_module import validate_search_request
    from search.types import SearchRequest
    from models import SAMPLE_RECIPES

    request = SearchRequest(query="pasta")
    validated = validate_search_request(request, sample_user_without_dietary)

    # dietary_restrictions must be a list (never None) at this point
    assert isinstance(validated.dietary_restrictions, list)

    # Filtering with the validated input must not raise
    result = apply_filters(validated, SAMPLE_RECIPES)
    assert isinstance(result.recipes, list)


# ---------------------------------------------------------------------------
# Prep time filter tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_prep_time_filter_less_than_or_equal():
    """Recipes with prep time ≤ max_minutes are returned."""
    quick = make_recipe(prep_time_minutes=15)
    slow = make_recipe(prep_time_minutes=60)
    result = _filter_by_prep_time([quick, slow], 30)
    assert quick in result
    assert slow not in result


@pytest.mark.unit
def test_prep_time_filter_exact_match():
    """Recipes with prep time == max_minutes are included (≤ not <)."""
    recipe = make_recipe(prep_time_minutes=30)
    result = _filter_by_prep_time([recipe], 30)
    assert len(result) == 1


@pytest.mark.unit
def test_prep_time_filter_none_returns_all():
    """When prep_time_max is None, apply_filters skips prep time filter."""
    recipes = [make_recipe(prep_time_minutes=10), make_recipe(prep_time_minutes=120)]
    validated = make_validated(prep_time_max=None)
    result = apply_filters(validated, recipes)
    assert len(result.recipes) == 2


# ---------------------------------------------------------------------------
# Difficulty filter tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_difficulty_filter_exact_match():
    """Filter returns recipe with matching difficulty."""
    easy = make_recipe(difficulty="easy")
    hard = make_recipe(difficulty="hard")
    result = _filter_by_difficulty([easy, hard], "easy")
    assert easy in result
    assert hard not in result


@pytest.mark.unit
def test_difficulty_filter_case_insensitive():
    """Difficulty filtering is case-insensitive."""
    recipe = make_recipe(difficulty="intermediate")
    result = _filter_by_difficulty([recipe], "INTERMEDIATE")
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Rating filter tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_rating_filter_greater_than_or_equal():
    """Recipes with avg_rating ≥ min_rating are returned."""
    good = make_recipe(avg_rating=4.5)
    bad = make_recipe(avg_rating=3.0)
    result = _filter_by_rating([good, bad], 4.0)
    assert good in result
    assert bad not in result


@pytest.mark.unit
def test_rating_filter_exact_boundary():
    """Recipes with avg_rating == min_rating are included (≥ not >)."""
    recipe = make_recipe(avg_rating=4.0)
    result = _filter_by_rating([recipe], 4.0)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Combined filters & short-circuit tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_combined_filters_all_criteria():
    """All active filters applied together correctly narrow the result set."""
    match = make_recipe(
        name="Vegan Pasta",
        ingredients=["pasta"],
        dietary_tags=["vegan"],
        cuisine="Italian",
        prep_time_minutes=20,
        difficulty="easy",
        avg_rating=4.5,
    )
    no_match = make_recipe(
        name="Steak",
        ingredients=["beef"],
        dietary_tags=[],
        cuisine="American",
        prep_time_minutes=45,
        difficulty="hard",
        avg_rating=3.0,
    )
    validated = make_validated(
        query="pasta",
        cuisine="Italian",
        dietary_restrictions=["vegan"],
        prep_time_max=30,
        difficulty="easy",
        min_rating=4.0,
    )
    result = apply_filters(validated, [match, no_match])
    assert result.recipes == [match]


@pytest.mark.unit
def test_short_circuit_on_empty_result():
    """apply_filters stops early when no recipes remain after a filter."""
    recipe = make_recipe(cuisine="Italian")
    validated = make_validated(cuisine="Thai", query="pasta")
    result = apply_filters(validated, [recipe])

    # Short-circuit: cuisine eliminates everything so query is never applied
    assert result.recipes == []
    assert "cuisine" in result.applied_filters
    # query filter should NOT be in applied_filters (short-circuited)
    assert "query" not in result.applied_filters


@pytest.mark.unit
def test_applied_filters_metadata():
    """FilteredRecipes.applied_filters records which filters were active."""
    recipe = make_recipe(cuisine="Italian", prep_time_minutes=20)
    validated = make_validated(cuisine="Italian", prep_time_max=30)
    result = apply_filters(validated, [recipe])

    assert "cuisine" in result.applied_filters
    assert "prep_time_max" in result.applied_filters


@pytest.mark.unit
def test_filter_duration_always_positive():
    """filter_duration_ms is always a positive number."""
    validated = make_validated()
    result = apply_filters(validated, [make_recipe()])
    assert result.filter_duration_ms >= 0.0


@pytest.mark.unit
def test_total_before_filters_matches_input():
    """total_before_filters matches the number of input recipes."""
    recipes = [make_recipe(), make_recipe(), make_recipe()]
    validated = make_validated()
    result = apply_filters(validated, recipes)
    assert result.total_before_filters == 3


@pytest.mark.unit
def test_empty_input_returns_empty():
    """apply_filters with an empty recipe list returns empty FilteredRecipes."""
    validated = make_validated(query="pasta")
    result = apply_filters(validated, [])
    assert result.recipes == []
    assert result.total_before_filters == 0
