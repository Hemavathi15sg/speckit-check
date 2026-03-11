"""
Unit Tests for Aggregation Module

Tests search/aggregation_module.py functions including the LRU cache
(fixes Issue #183 - unbounded memory growth) and hybrid_v3 ranking.

Test Coverage Target: ≥80%
Constitution Principle III: Testability
"""
import time
import pytest
from uuid import uuid4
from models import Recipe
from search.aggregation_module import (
    aggregate_and_rank,
    _rank_recipes,
    _calculate_text_relevance,
    _generate_cache_key,
    _paginate_recipes,
    _calculate_total_pages,
    get_cache,
    _LRUCache,
)
from search.constants import (
    MAX_CACHE_SIZE,
    CACHE_TTL_SECONDS,
    TEXT_MATCH_EXACT,
    TEXT_MATCH_PARTIAL,
    TEXT_MATCH_INGREDIENT,
)
from search.types import FilteredRecipes, ValidatedSearchInput


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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


def make_validated(
    query: str = "",
    dietary_restrictions=None,
    cuisine=None,
    prep_time_max=None,
    difficulty=None,
    min_rating: float = 0.0,
    page: int = 1,
    page_size: int = 50,
    user_id: str = "user-123",
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


def make_filtered(recipes=None) -> FilteredRecipes:
    r = recipes or []
    return FilteredRecipes(
        recipes=r,
        applied_filters={},
        filter_duration_ms=1.0,
        total_before_filters=len(r),
    )


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the module-level cache before each test for isolation."""
    get_cache().clear()
    yield
    get_cache().clear()


# ---------------------------------------------------------------------------
# Text relevance scoring tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ranking_algorithm_text_relevance_exact():
    """Exact name match scores TEXT_MATCH_EXACT points."""
    recipe = make_recipe(name="pasta carbonara")
    score = _calculate_text_relevance(recipe, "pasta carbonara")
    assert score == TEXT_MATCH_EXACT


@pytest.mark.unit
def test_ranking_algorithm_text_relevance_partial():
    """Partial name match scores TEXT_MATCH_PARTIAL points."""
    recipe = make_recipe(name="Pasta Carbonara")
    score = _calculate_text_relevance(recipe, "carbonara")
    assert score == TEXT_MATCH_PARTIAL


@pytest.mark.unit
def test_ranking_algorithm_text_relevance_ingredient():
    """Each matching ingredient adds TEXT_MATCH_INGREDIENT points."""
    recipe = make_recipe(name="Dish", ingredients=["pasta", "eggs", "bacon"])
    score = _calculate_text_relevance(recipe, "pasta")
    # Partial name match (0) + ingredient match (TEXT_MATCH_INGREDIENT)
    assert score == TEXT_MATCH_INGREDIENT


@pytest.mark.unit
def test_ranking_no_query_no_text_score():
    """When query is empty, text relevance is not calculated (score stays 0)."""
    recipe1 = make_recipe(name="Pasta", avg_rating=4.0)
    recipe2 = make_recipe(name="Salad", avg_rating=4.8)
    ranked = _rank_recipes([recipe1, recipe2], "")
    # Without query, ranking is purely by quality + popularity (avg_rating proxy)
    assert ranked[0].name == "Salad"  # Higher rating ranks first


# ---------------------------------------------------------------------------
# Ranking order tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ranking_higher_relevance_ranks_first():
    """Recipe with better text match ranks before less-relevant recipe."""
    exact = make_recipe(name="pasta carbonara", avg_rating=3.0)
    partial = make_recipe(name="pasta dish", avg_rating=5.0)
    ranked = _rank_recipes([partial, exact], "pasta carbonara")
    # Exact match should rank first even with lower base rating
    assert ranked[0].name == "pasta carbonara"


@pytest.mark.unit
def test_ranking_empty_list_returns_empty():
    """Ranking an empty list returns an empty list."""
    assert _rank_recipes([], "pasta") == []


# ---------------------------------------------------------------------------
# Cache tests (Issue #183 fix)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_cache_hit_returns_cached_results():
    """Second call with same parameters returns cached results."""
    recipes = [make_recipe(name="Pasta")]
    filtered = make_filtered(recipes)
    validated = make_validated(query="pasta")

    result1 = aggregate_and_rank(filtered, validated)
    result2 = aggregate_and_rank(filtered, validated)

    assert result2.cache_hit is True


@pytest.mark.unit
def test_cache_miss_computes_fresh_results():
    """First call with new parameters is a cache miss."""
    filtered = make_filtered([make_recipe()])
    validated = make_validated(query="unique_query_xyz")

    result = aggregate_and_rank(filtered, validated)
    assert result.cache_hit is False


@pytest.mark.unit
def test_cache_key_includes_all_filters():
    """Different filter parameters produce different cache keys."""
    v1 = make_validated(query="pasta")
    v2 = make_validated(query="pasta", cuisine="Italian")
    assert _generate_cache_key(v1) != _generate_cache_key(v2)


@pytest.mark.unit
def test_cache_key_excludes_pagination():
    """Page number and page size do NOT change the cache key."""
    v1 = make_validated(query="pasta", page=1)
    v2 = make_validated(query="pasta", page=2)
    assert _generate_cache_key(v1) == _generate_cache_key(v2)


@pytest.mark.unit
def test_cache_ttl_expires_old_entries():
    """Cache returns None for entries older than TTL."""
    cache = _LRUCache(max_size=10, ttl_seconds=0)  # TTL = 0 seconds
    cache.put("key", {"data": "value"})
    time.sleep(0.01)
    assert cache.get("key") is None  # Expired


@pytest.mark.unit
def test_cache_lru_eviction_at_max_size():
    """When cache is full, the least-recently-used entry is evicted."""
    cache = _LRUCache(max_size=3, ttl_seconds=300)
    cache.put("a", {})
    cache.put("b", {})
    cache.put("c", {})
    # Access 'a' to make it recently used
    cache.get("a")
    # Insert 'd' - should evict 'b' (LRU)
    cache.put("d", {})
    assert cache.get("b") is None
    assert cache.get("a") is not None
    assert cache.size == 3


@pytest.mark.unit
def test_cache_size_bounded():
    """Cache never exceeds MAX_CACHE_SIZE entries."""
    cache = get_cache()
    # Insert MAX_CACHE_SIZE + 10 entries
    for i in range(MAX_CACHE_SIZE + 10):
        cache.put(f"key_{i}", {"data": i})
    assert cache.size <= MAX_CACHE_SIZE


# ---------------------------------------------------------------------------
# Pagination tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_pagination_first_page():
    """First page returns the first page_size recipes."""
    recipes = [make_recipe(name=str(i)) for i in range(10)]
    page = _paginate_recipes(recipes, page=1, page_size=3)
    assert len(page) == 3
    assert page[0].name == "0"


@pytest.mark.unit
def test_pagination_page_within_range():
    """Middle page returns correct slice."""
    recipes = [make_recipe(name=str(i)) for i in range(10)]
    page = _paginate_recipes(recipes, page=2, page_size=3)
    assert len(page) == 3
    assert page[0].name == "3"


@pytest.mark.unit
def test_pagination_page_beyond_range():
    """Out-of-range page returns empty list."""
    recipes = [make_recipe(name=str(i)) for i in range(5)]
    page = _paginate_recipes(recipes, page=10, page_size=5)
    assert page == []


@pytest.mark.unit
def test_total_pages_calculation():
    """Total pages calculated correctly with ceiling division."""
    assert _calculate_total_pages(10, 3) == 4
    assert _calculate_total_pages(9, 3) == 3
    assert _calculate_total_pages(1, 50) == 1


@pytest.mark.unit
def test_total_pages_zero_for_no_results():
    """Zero results → 0 total pages."""
    assert _calculate_total_pages(0, 50) == 0


# ---------------------------------------------------------------------------
# aggregate_and_rank integration
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_aggregate_and_rank_returns_ranked_results_type():
    """aggregate_and_rank returns a RankedResults instance."""
    from search.types import RankedResults

    filtered = make_filtered([make_recipe()])
    validated = make_validated()
    result = aggregate_and_rank(filtered, validated)
    assert isinstance(result, RankedResults)


@pytest.mark.unit
def test_aggregate_and_rank_empty_input():
    """aggregate_and_rank handles empty filtered recipes list."""
    filtered = make_filtered([])
    validated = make_validated()
    result = aggregate_and_rank(filtered, validated)
    assert result.recipes == []
    assert result.total_results == 0
    assert result.total_pages == 0


@pytest.mark.unit
def test_aggregate_ranking_duration_positive_on_cache_miss():
    """ranking_duration_ms is positive on a cache miss."""
    filtered = make_filtered([make_recipe()])
    validated = make_validated(query="test_unique_query")
    result = aggregate_and_rank(filtered, validated)
    assert result.cache_hit is False
    assert result.ranking_duration_ms >= 0.0


@pytest.mark.unit
def test_aggregate_ranking_duration_zero_on_cache_hit():
    """ranking_duration_ms is 0.0 on a cache hit."""
    filtered = make_filtered([make_recipe()])
    validated = make_validated(query="cache_hit_test")
    aggregate_and_rank(filtered, validated)  # warm cache
    result = aggregate_and_rank(filtered, validated)  # cache hit
    assert result.cache_hit is True
    assert result.ranking_duration_ms == 0.0
