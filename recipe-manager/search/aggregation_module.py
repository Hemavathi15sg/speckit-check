"""
Aggregation Module
Ranks filtered recipes and manages the bounded LRU result cache.
This module is the THIRD step in the search pipeline, after filtering.

Data Flow:
    FilteredRecipes + ValidatedSearchInput → aggregate_and_rank() → RankedResults

Design Principles:
- Single responsibility: only ranking and caching, no filtering or formatting
- Bounded LRU cache: fixes Issue #183 (unbounded memory growth)
- Thread-safe cache: uses a lock for concurrent access
- Hybrid_v3 ranking: text relevance 40% + quality 30% + popularity 30%
- All weights and limits come from constants.py (no magic numbers)

Performance Target: <5ms P50 cache hit, <30ms P50 cache miss
Line Count Target: ≤300 lines (currently: will be checked post-implementation)
"""
import hashlib
import json
import logging
import math
import threading
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

from models import Recipe
from search.constants import (
    CACHE_TTL_SECONDS,
    MAX_CACHE_SIZE,
    RANKING_WEIGHT_POPULARITY,
    RANKING_WEIGHT_QUALITY,
    RANKING_WEIGHT_TEXT_MATCH,
    TEXT_MATCH_EXACT,
    TEXT_MATCH_INGREDIENT,
    TEXT_MATCH_PARTIAL,
    TEXT_MATCH_TAG,
)
from search.types import FilteredRecipes, RankedResults, ValidatedSearchInput

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Bounded LRU cache with TTL (fixes Issue #183)
# ---------------------------------------------------------------------------


class _LRUCache:
    """
    Thread-safe LRU cache with TTL expiration.

    Stores up to ``max_size`` entries; when full, the least-recently-used
    entry is evicted before inserting a new one.  Entries older than
    ``ttl_seconds`` are treated as cache misses.

    This class fixes Issue #183 (unbounded memory growth in legacy search.py).
    """

    def __init__(self, max_size: int, ttl_seconds: int) -> None:
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._store: OrderedDict[str, Tuple[Dict, float]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Dict]:
        """Return cached value or None if missing/expired."""
        with self._lock:
            if key not in self._store:
                self._misses += 1
                return None
            value, timestamp = self._store[key]
            if time.monotonic() - timestamp > self._ttl:
                # Expired: remove and treat as miss
                del self._store[key]
                self._misses += 1
                logger.debug("Cache expired: %s", key[:40])
                return None
            # Move to end (most recently used)
            self._store.move_to_end(key)
            self._hits += 1
            logger.debug("Cache hit: %s", key[:40])
            return value

    def put(self, key: str, value: Dict) -> None:
        """Insert or update a cache entry, evicting LRU if at capacity."""
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
                self._store[key] = (value, time.monotonic())
                return
            if len(self._store) >= self._max_size:
                evicted_key, _ = self._store.popitem(last=False)
                logger.debug("Cache evicted LRU: %s", evicted_key[:40])
            self._store[key] = (value, time.monotonic())
            logger.debug("Cache stored: %s (%d entries)", key[:40], len(self._store))

    @property
    def size(self) -> int:
        """Current number of entries."""
        with self._lock:
            return len(self._store)

    @property
    def hit_rate(self) -> float:
        """Cumulative cache hit rate (0.0–1.0)."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def clear(self) -> None:
        """Remove all entries (for testing)."""
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0


# Module-level cache instance (shared across all requests)
_cache = _LRUCache(max_size=MAX_CACHE_SIZE, ttl_seconds=CACHE_TTL_SECONDS)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def aggregate_and_rank(
    filtered: FilteredRecipes,
    validated_input: ValidatedSearchInput,
) -> RankedResults:
    """
    Rank filtered recipes and paginate the result.

    Steps:
    1. Generate a deterministic cache key from the search parameters.
    2. Check the LRU cache; return immediately on hit.
    3. On miss: rank recipes with hybrid_v3 algorithm, paginate, cache.

    Args:
        filtered: Output from filtering_module (may be empty).
        validated_input: Validated parameters (page, page_size, query, etc.).

    Returns:
        RankedResults with the requested page of ranked recipes and metadata.

    Side Effects:
        Reads from / writes to the module-level LRU cache.
    """
    start_time = time.perf_counter()
    cache_key = _generate_cache_key(validated_input)

    cached = _cache.get(cache_key)
    if cached is not None:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.debug("Returning cached result in %.2fms", duration_ms)
        # Rebuild RankedResults from cached dict
        return RankedResults(
            recipes=cached["recipes"],
            total_results=cached["total_results"],
            page=validated_input.page,
            page_size=validated_input.page_size,
            total_pages=cached["total_pages"],
            cache_hit=True,
            ranking_duration_ms=0.0,
            cache_key=cache_key,
        )

    # Rank
    rank_start = time.perf_counter()
    ranked = _rank_recipes(filtered.recipes, validated_input.query)
    ranking_duration_ms = (time.perf_counter() - rank_start) * 1000

    total = len(ranked)
    total_pages = _calculate_total_pages(total, validated_input.page_size)
    page_recipes = _paginate_recipes(
        ranked, validated_input.page, validated_input.page_size
    )

    # Store in cache (without pagination to allow cache reuse across pages)
    _cache.put(
        cache_key,
        {
            "recipes": ranked,  # full ranked list
            "total_results": total,
            "total_pages": total_pages,
        },
    )

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(
        "Aggregation complete: %d results, page %d/%d in %.2fms",
        total,
        validated_input.page,
        total_pages,
        duration_ms,
    )

    return RankedResults(
        recipes=page_recipes,
        total_results=total,
        page=validated_input.page,
        page_size=validated_input.page_size,
        total_pages=total_pages,
        cache_hit=False,
        ranking_duration_ms=ranking_duration_ms,
        cache_key=cache_key,
    )


# ---------------------------------------------------------------------------
# Ranking helpers
# ---------------------------------------------------------------------------


def _rank_recipes(recipes: List[Recipe], query: str) -> List[Recipe]:
    """
    Rank recipes using the hybrid_v3 algorithm.

    Score = text_relevance * RANKING_WEIGHT_TEXT_MATCH
           + avg_rating    * RANKING_WEIGHT_QUALITY
           + avg_rating    * RANKING_WEIGHT_POPULARITY   (popularity proxy)

    Tie-breaks are resolved alphabetically by recipe name.

    Args:
        recipes: Filtered recipe list (may be empty).
        query: Normalized search query (empty string = no text component).

    Returns:
        Recipes sorted by descending hybrid score.
    """
    if not recipes:
        return []

    scored: List[Tuple[float, str, Recipe]] = []
    for recipe in recipes:
        text_score = _calculate_text_relevance(recipe, query) if query else 0.0
        quality_score = recipe.avg_rating * RANKING_WEIGHT_QUALITY
        popularity_score = recipe.avg_rating * RANKING_WEIGHT_POPULARITY
        final = (
            text_score * RANKING_WEIGHT_TEXT_MATCH
            + quality_score
            + popularity_score
        )
        scored.append((final, recipe.name, recipe))

    scored.sort(key=lambda x: (-x[0], x[1]))
    return [recipe for _, _, recipe in scored]


def _calculate_text_relevance(recipe: Recipe, query: str) -> float:
    """
    Calculate text relevance score for a recipe against a query.

    Scoring (all values from constants.py):
    - Exact name match:       TEXT_MATCH_EXACT      (10.0)
    - Partial name match:     TEXT_MATCH_PARTIAL    (5.0)
    - Per ingredient match:   TEXT_MATCH_INGREDIENT (3.0)
    - Per dietary-tag match:  TEXT_MATCH_TAG        (2.0)

    Args:
        recipe: Recipe to score.
        query: Lowercased, stripped query string.

    Returns:
        Non-negative relevance score.
    """
    score = 0.0
    name_lower = recipe.name.lower()

    if query == name_lower:
        score += TEXT_MATCH_EXACT
    elif query in name_lower:
        score += TEXT_MATCH_PARTIAL

    score += sum(
        TEXT_MATCH_INGREDIENT
        for ing in recipe.ingredients
        if query in ing.lower()
    )
    score += sum(
        TEXT_MATCH_TAG
        for tag in recipe.dietary_tags
        if query in tag.lower()
    )
    return score


# ---------------------------------------------------------------------------
# Cache key
# ---------------------------------------------------------------------------


def _generate_cache_key(validated_input: ValidatedSearchInput) -> str:
    """
    Generate a deterministic cache key from all filter parameters.

    Pagination (page / page_size) is intentionally EXCLUDED so that
    different pages of the same search share a single cache entry.

    Args:
        validated_input: Fully validated search input.

    Returns:
        SHA-256 hex digest (64 chars) of the canonical JSON representation.
    """
    payload = {
        "user_id": validated_input.user_id,
        "query": validated_input.query,
        "cuisine": validated_input.cuisine,
        "dietary_restrictions": sorted(validated_input.dietary_restrictions),
        "prep_time_max": validated_input.prep_time_max,
        "difficulty": validated_input.difficulty,
        "min_rating": validated_input.min_rating,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Pagination helpers
# ---------------------------------------------------------------------------


def _paginate_recipes(
    recipes: List[Recipe], page: int, page_size: int
) -> List[Recipe]:
    """
    Slice the recipe list to the requested page.

    Args:
        recipes: Full ranked list.
        page: 1-based page number (validated ≥1).
        page_size: Results per page (validated 1–200).

    Returns:
        Slice of recipes for the requested page (may be empty for out-of-range pages).
    """
    start = (page - 1) * page_size
    return recipes[start : start + page_size]


def _calculate_total_pages(total: int, page_size: int) -> int:
    """
    Calculate total number of pages.

    Args:
        total: Total number of results.
        page_size: Results per page.

    Returns:
        Number of pages (0 when total is 0).
    """
    if total == 0:
        return 0
    return math.ceil(total / page_size)


# ---------------------------------------------------------------------------
# Cache access (for testing / diagnostics)
# ---------------------------------------------------------------------------


def get_cache() -> _LRUCache:
    """Return the module-level cache instance (for testing and diagnostics)."""
    return _cache
