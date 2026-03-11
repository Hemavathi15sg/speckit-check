# Aggregation Module Contract

**Module**: `search/aggregation_module.py`  
**Purpose**: Rank filtered results and manage LRU caching  
**Phase**: 1 (Week 3 rollout)

---

## Public Interface

### Primary Function

```python
def aggregate_and_rank(
    filtered: FilteredRecipes,
    validated_input: ValidatedSearchInput
) -> RankedResults:
    """
    Rank filtered recipes and apply pagination with caching.
    
    Args:
        filtered: Filtered recipes from filtering_module
        validated_input: Original search parameters (for cache key and pagination)
    
    Returns:
        RankedResults with ranked recipes for requested page
    
    Raises:
        AggregationError: Only if internal state is invalid (should never happen)
    
    Performance:
        Target: <10ms P50 with cache, <30ms P50 without cache
        Cache hit rate target: ≥60%
    
    Side Effects:
        Updates LRU cache (in-memory, thread-safe)
    """
```

---

## Ranking Algorithm

### Hybrid Relevance Score (hybrid_v3)

**Formula**:
```
score = (text_relevance * 0.4) + (quality_score * 0.3) + (popularity_score * 0.3)
```

**Components**:

1. **text_relevance** (0.0-1.0):
   - Query appears in recipe name: 1.0
   - Query appears in ingredients only: 0.7
   - No query (empty string): 1.0 (all recipes equal)

2. **quality_score** (0.0-1.0):
   - Normalized rating: `recipe.avg_rating / 5.0`
   - Example: 4.5 stars → 0.9

3. **popularity_score** (0.0-1.0):
   - Based on recipe difficulty (proxy for popularity):
     - "easy": 1.0 (most popular)
     - "medium": 0.7
     - "hard": 0.4
   - Rationale: Easier recipes tend to be tried more often

**Sorting**:
- Recipes sorted by score descending (highest first)
- Tie-breaking: Recipe name alphabetically

**Implementation**:
```python
def _calculate_relevance_score(recipe: Recipe, query: str) -> float:
    """Calculate hybrid relevance score for recipe."""
    # Text relevance
    if not query:
        text_relevance = 1.0  # No query = all equal
    elif query.lower() in recipe.name.lower():
        text_relevance = 1.0  # Exact name match
    elif any(query.lower() in ing.lower() for ing in recipe.ingredients):
        text_relevance = 0.7  # Ingredient match
    else:
        text_relevance = 0.0  # Should not happen (already filtered)
    
    # Quality score
    quality_score = recipe.avg_rating / 5.0
    
    # Popularity score
    popularity_map = {"easy": 1.0, "medium": 0.7, "hard": 0.4}
    popularity_score = popularity_map.get(recipe.difficulty, 0.5)
    
    # Combined score
    return (text_relevance * 0.4) + (quality_score * 0.3) + (popularity_score * 0.3)

def _rank_recipes(recipes: List[Recipe], query: str) -> List[Recipe]:
    """Rank recipes by hybrid relevance score."""
    scored = [
        (recipe, _calculate_relevance_score(recipe, query))
        for recipe in recipes
    ]
    scored.sort(key=lambda x: (-x[1], x[0].name))  # Desc score, then name
    return [recipe for recipe, _ in scored]
```

**Rationale**:
- Text relevance ensures query-relevant results appear first
- Quality score promotes well-reviewed recipes
- Popularity score balances with accessible recipes
- Weighted combination provides balanced ranking

**Alternative Considered**: TF-IDF (rejected due to complexity and marginal improvement)

---

## LRU Cache Implementation

### Cache Configuration

**Constants**:
```python
MAX_CACHE_SIZE = 1000  # Maximum entries
CACHE_TTL_SECONDS = 300  # 5 minutes
```

**Cache Key**:
```python
def _generate_cache_key(validated_input: ValidatedSearchInput) -> str:
    """
    Generate cache key from search parameters.
    
    Includes: user_id, query, cuisine, dietary_restrictions (sorted),
              prep_time_max, difficulty, min_rating
    Excludes: page, page_size (pagination handled separately)
    """
    restrictions_sorted = sorted(validated_input.dietary_restrictions)
    
    key_parts = [
        validated_input.user_id,
        validated_input.query,
        validated_input.cuisine or "",
        ",".join(restrictions_sorted),
        str(validated_input.prep_time_max or ""),
        validated_input.difficulty or "",
        f"{validated_input.min_rating:.1f}"
    ]
    
    return "|".join(key_parts)
```

**Rationale**:
- Include user_id: Different users may have different recipe access
- Include all filter params: Cache must be filter-specific
- Exclude pagination: Same results, different page slicing
- Sort dietary_restrictions: ["vegan", "gluten-free"] == ["gluten-free", "vegan"]

### Cache Entry Structure

```python
@dataclass
class CacheEntry:
    """LRU cache entry for ranked recipes."""
    ranked_recipes: List[Recipe]  # Fully ranked results (all pages)
    total_count: int  # Total recipes (before pagination)
    timestamp: float  # Creation time (for TTL)
    applied_filters: Dict[str, Any]  # Metadata for debugging
```

### LRU Eviction

**Implementation**: Use `functools.lru_cache` with TTL wrapper

```python
from functools import lru_cache
import time

# Thread-safe LRU cache with TTL
_cache_timestamps: Dict[str, float] = {}

@lru_cache(maxsize=MAX_CACHE_SIZE)
def _cached_rank_and_aggregate(cache_key: str, recipes_hash: int) -> CacheEntry:
    """
    Internal cached ranking function.
    
    recipes_hash: Hash of filtered recipes (for cache invalidation)
    """
    # This will be populated by aggregate_and_rank if cache miss
    pass

def _check_cache_ttl(cache_key: str) -> bool:
    """Check if cache entry is still valid (within TTL)."""
    if cache_key not in _cache_timestamps:
        return False
    
    age = time.time() - _cache_timestamps[cache_key]
    return age < CACHE_TTL_SECONDS
```

**Eviction Strategy**:
1. **Size-based**: LRU evicts least recently used entry when max_size reached
2. **Time-based**: Entries older than TTL are considered stale (not returned)
3. **Manual**: Clear cache on demand (for testing or deployment)

**Memory Management**:
- Each CacheEntry: ~5KB (100 recipes * 50 bytes each)
- Max cache size: 1000 entries * 5KB = ~5MB total
- Well within acceptable memory bounds (<50MB per spec)

**Fix for Issue #183**:
Legacy cache had unbounded growth → memory leak.
New cache has explicit max_size (1000) and TTL (300s) → bounded memory.

---

## Pagination

### Pagination Logic

**Slicing**:
```python
def _paginate_recipes(
    ranked_recipes: List[Recipe],
    page: int,
    page_size: int
) -> List[Recipe]:
    """
    Slice ranked recipes for requested page.
    
    Args:
        ranked_recipes: All ranked recipes (from ranking or cache)
        page: 1-indexed page number (validated)
        page_size: Recipes per page (validated)
    
    Returns:
        Recipes for requested page (may be empty if beyond last page)
    """
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    return ranked_recipes[start_idx:end_idx]
```

**Edge Cases**:
- Page beyond last page: Return empty list (not an error)
- Page 1, page_size 50: Recipes [0:50]
- Page 2, page_size 50: Recipes [50:100]
- Total 47 recipes, page 1, page_size 50: Return all 47
- Total 47 recipes, page 2, page_size 50: Return empty list

**Total Pages Calculation**:
```python
import math

def _calculate_total_pages(total_count: int, page_size: int) -> int:
    """Calculate total pages for pagination."""
    if total_count == 0:
        return 0
    return math.ceil(total_count / page_size)
```

---

## Output Structure

**RankedResults** contains:

```python
@dataclass(frozen=True)
class RankedResults:
    recipes: List[Recipe]  # Ranked recipes for current page only
    total_count: int  # Total recipes before pagination
    page: int  # Current page number
    page_size: int  # Recipes per page
    cache_hit: bool  # Whether result was served from cache
    ranking_duration_ms: float  # Time for ranking (0 if cache hit)
    total_duration_ms: float  # Total time (validation + filtering + ranking)
```

### Field Population

**recipes**:
- Ranked subset for requested page only
- Length ≤ page_size
- Empty if page beyond last page

**total_count**:
- Length of all ranked recipes (before pagination)
- Used to calculate total_pages
- 0 if no results

**page, page_size**:
- Copied from ValidatedSearchInput
- Used by formatting_module for response metadata

**cache_hit**:
- `true`: Result served from cache (ranking skipped)
- `false`: Result computed fresh (ranking executed)

**ranking_duration_ms**:
- Time spent ranking recipes
- 0.0 if cache hit
- Typically <10ms for 100 recipes

**total_duration_ms**:
- Sum of all module durations:
  - `validated_input.validation_duration` (if tracked)
  - `filtered.filter_duration_ms`
  - `ranking_duration_ms`
- Used for end-to-end performance monitoring

---

## Error Handling

### AggregationError Exception

```python
class AggregationError(Exception):
    """Raised when aggregation encounters unexpected state."""
    
    def __init__(self, message: str):
        super().__init__(f"Aggregation error: {message}")
```

**Error Cases** (should be extremely rare):
- filtered.recipes is None → `AggregationError("recipes cannot be None")`
- Recipe missing required fields → `AggregationError("Invalid recipe object")`
- Cache corruption → `AggregationError("Cache entry invalid")`

**Handling**:
- API layer catches AggregationError and returns 500 Internal Server Error
- Log full stack trace for debugging
- Clear cache if corruption suspected
- Fallback to legacy search if feature flag enabled

---

## Feature Flag Integration

**Flag Name**: `USE_NEW_AGGREGATION`  
**Default**: `False` (disabled, use legacy aggregation)  
**Rollout**: Week 3 (after filtering_module deployed)

```python
def search_recipes(request: SearchRequest, user: User):
    """Main search entry point"""
    validated = validate_search_request(request, user)
    filtered = apply_filters(validated, SAMPLE_RECIPES)
    
    if os.getenv("USE_NEW_AGGREGATION") == "true":
        try:
            ranked = aggregate_and_rank(filtered, validated)
            # Pass to formatting module (or legacy if not ready)
            return _search_with_new_aggregation(ranked, validated)
        except Exception as e:
            logger.error(f"New aggregation failed: {e}")
            # Automatic fallback to legacy
            return _search_with_legacy_aggregation(filtered, validated)
    else:
        return _search_with_legacy_aggregation(filtered, validated)
```

**Rollout Strategy**:
- Week 3 Day 1: Enable for 10% traffic (canary)
- Week 3 Day 3: Enable for 50% traffic (if no issues)
- Week 3 Day 5: Enable for 100% traffic (if cache hit rate ≥60%)

**Success Metrics**:
- Ranking duration <10ms P50 (cache hit), <30ms P50 (cache miss)
- Cache hit rate ≥60%
- Memory usage ≤10MB for cache
- Zero 500 errors from aggregation
- Issue #183 cache leak resolved (memory bounded)

---

## Testing Requirements

### Unit Tests (Target: 85% coverage)

**tests/unit/test_aggregation_module.py**:

1. **test_ranking_algorithm_text_relevance**
   - Input: Recipe with query in name, recipe with query in ingredients
   - Expected: Name match ranked higher

2. **test_ranking_algorithm_quality_score**
   - Input: Two recipes, one 5-star, one 3-star
   - Expected: 5-star ranked higher (if text relevance equal)

3. **test_ranking_algorithm_popularity_score**
   - Input: Two recipes, one "easy", one "hard"
   - Expected: "easy" ranked higher (if quality equal)

4. **test_ranking_algorithm_hybrid_score**
   - Input: Recipe with high quality but low popularity vs inverse
   - Expected: Balanced ranking based on weighted formula

5. **test_ranking_no_query_all_equal_text_relevance**
   - Input: Empty query, multiple recipes
   - Expected: All text_relevance = 1.0, ranked by quality/popularity

6. **test_cache_hit_returns_cached_results**
   - Input: Same cache_key twice
   - Expected: Second call returns cache_hit=true, ranking_duration_ms=0

7. **test_cache_miss_computes_fresh_results**
   - Input: New cache_key
   - Expected: cache_hit=false, ranking_duration_ms>0

8. **test_cache_key_includes_all_filters**
   - Input: Different filter combinations
   - Expected: Different cache keys generated

9. **test_cache_key_excludes_pagination**
   - Input: Same filters, different page/page_size
   - Expected: Same cache key (pagination handled separately)

10. **test_cache_ttl_expires_old_entries**
    - Input: Cache entry older than TTL
    - Expected: Entry considered stale, recomputed

11. **test_cache_lru_eviction_at_max_size**
    - Input: Insert 1001 entries (max_size=1000)
    - Expected: Least recently used entry evicted

12. **test_pagination_page_within_range**
    - Input: 100 recipes, page=2, page_size=50
    - Expected: Recipes [50:100] returned

13. **test_pagination_page_beyond_range**
    - Input: 47 recipes, page=2, page_size=50
    - Expected: Empty list returned

14. **test_pagination_first_page**
    - Input: 100 recipes, page=1, page_size=50
    - Expected: Recipes [0:50] returned

15. **test_total_pages_calculation**
    - Input: 47 recipes, page_size=50
    - Expected: total_pages=1

16. **test_total_pages_zero_for_no_results**
    - Input: 0 recipes
    - Expected: total_pages=0

17. **test_total_duration_includes_all_modules**
    - Input: Mock filter_duration_ms + ranking_duration_ms
    - Expected: total_duration_ms = sum of all

### Contract Tests (Target: 100% interface coverage)

**tests/contract/test_aggregation_contract.py**:

1. **test_contract_returns_ranked_results_type**
   - Assert return type is RankedResults

2. **test_contract_recipes_list_never_none**
   - Assert RankedResults.recipes is List (may be empty, never None)

3. **test_contract_total_count_matches_filtered**
   - Assert total_count == len(filtered.recipes)

4. **test_contract_page_info_matches_input**
   - Assert page and page_size match validated_input

5. **test_contract_cache_hit_boolean**
   - Assert cache_hit is bool (True or False)

6. **test_contract_ranking_duration_zero_on_cache_hit**
   - If cache_hit=True, assert ranking_duration_ms == 0.0

7. **test_contract_total_duration_always_positive**
   - Assert total_duration_ms ≥ 0.0

### Integration Tests

**tests/integration/test_full_pipeline.py**:

1. **test_validation_filtering_aggregation_pipeline**
   - Run SearchRequest → validate → filter → aggregate
   - Assert end-to-end correctness

2. **test_cache_persistence_across_calls**
   - Call aggregate_and_rank twice with same input
   - Assert second call has cache_hit=true

3. **test_issue_183_memory_bounded**
   - Insert 10,000 entries into cache
   - Assert cache size ≤ MAX_CACHE_SIZE (1000)
   - Assert memory usage ≤ 10MB

---

## Performance Requirements

### Targets

**With Cache Hit**:
- **P50 latency**: <5ms
- **P95 latency**: <10ms
- **Cache overhead**: <1ms

**With Cache Miss**:
- **P50 latency**: <30ms for 100 recipes
- **P95 latency**: <60ms for 100 recipes
- **Ranking throughput**: ≥500 recipes/second

**Cache Performance**:
- **Hit rate**: ≥60% (typical workload)
- **Memory**: ≤10MB for 1000 entries
- **Lookup time**: O(1) average, <1ms

### Optimization Strategies

1. **Caching**: LRU cache with TTL reduces ranking computation
2. **Efficient ranking**: Single-pass scoring (no nested loops)
3. **Lazy pagination**: Only slice needed page, not all pages
4. **In-memory**: No database queries, no I/O
5. **Immutable recipes**: No deep copying needed

### Benchmarking

**tests/performance/test_aggregation_performance.py**:
```python
def test_aggregation_cache_hit_performance():
    """Ensure cache hits meet performance targets"""
    validated = create_sample_validated_input()
    filtered = create_sample_filtered_recipes(100)
    
    # Prime cache
    aggregate_and_rank(filtered, validated)
    
    # Measure cache hits
    durations = []
    for _ in range(1000):
        start = time.perf_counter()
        aggregate_and_rank(filtered, validated)
        durations.append((time.perf_counter() - start) * 1000)
    
    p50 = percentile(durations, 50)
    p95 = percentile(durations, 95)
    
    assert p50 < 5.0, f"Cache hit P50 {p50}ms exceeds 5ms target"
    assert p95 < 10.0, f"Cache hit P95 {p95}ms exceeds 10ms target"

def test_aggregation_cache_miss_performance():
    """Ensure cache misses meet performance targets"""
    durations = []
    for i in range(100):
        validated = create_unique_validated_input(i)  # Different cache keys
        filtered = create_sample_filtered_recipes(100)
        
        start = time.perf_counter()
        aggregate_and_rank(filtered, validated)
        durations.append((time.perf_counter() - start) * 1000)
    
    p50 = percentile(durations, 50)
    p95 = percentile(durations, 95)
    
    assert p50 < 30.0, f"Cache miss P50 {p50}ms exceeds 30ms target"
    assert p95 < 60.0, f"Cache miss P95 {p95}ms exceeds 60ms target"
```

---

## Logging & Observability

### Logging Events

```python
import logging
logger = logging.getLogger(__name__)

# Cache hit (DEBUG level)
logger.debug(f"Cache hit for user {validated_input.user_id}", extra={
    "user_id": validated_input.user_id,
    "cache_key": cache_key,
    "total_count": ranked.total_count
})

# Cache miss (DEBUG level)
logger.debug(f"Cache miss, ranking {len(filtered.recipes)} recipes", extra={
    "user_id": validated_input.user_id,
    "recipe_count": len(filtered.recipes),
    "ranking_duration_ms": ranked.ranking_duration_ms
})

# Performance warning (WARNING level)
if ranking_duration_ms > 60:
    logger.warning(f"Slow ranking: {ranking_duration_ms}ms", extra={
        "user_id": validated_input.user_id,
        "duration_ms": ranking_duration_ms,
        "recipe_count": len(filtered.recipes)
    })

# Cache eviction (INFO level)
if cache_evicted:
    logger.info(f"LRU cache evicted entry", extra={
        "cache_size": MAX_CACHE_SIZE,
        "evicted_key": evicted_key
    })
```

### Metrics to Track

1. **aggregation_cache_hit_total** (counter): Cache hits
2. **aggregation_cache_miss_total** (counter): Cache misses
3. **aggregation_cache_hit_rate** (gauge): Rolling hit rate (hits / total)
4. **aggregation_duration_seconds** (histogram): Ranking latency distribution
5. **aggregation_cache_size** (gauge): Current cache size (entries)
6. **aggregation_cache_memory_bytes** (gauge): Estimated cache memory usage
7. **recipes_ranked_total** (histogram): Number of recipes ranked per request

---

## Dependencies

### Internal
- `models.Recipe`: Recipe object structure
- `search.types.FilteredRecipes`: Input type
- `search.types.ValidatedSearchInput`: For cache key and pagination
- `search.types.RankedResults`: Output type

### External
- `functools.lru_cache`: For LRU caching
- `dataclasses`: For dataclass types
- `typing`: For type hints
- `logging`: For observability
- `time.perf_counter`: For duration measurement
- `time.time`: For TTL timestamps
- `math.ceil`: For total pages calculation

**No Database or External API Calls**: All aggregation in-memory.

---

## Backward Compatibility

**Public API Unchanged**:
- Legacy `search_recipes(request, user)` signature preserved
- New aggregation only used when feature flag enabled
- Automatic fallback to legacy aggregation on errors
- Zero breaking changes for API consumers

**Cache Migration**:
- New cache does not share state with legacy cache
- Gradual rollout means cache warming happens naturally
- No manual cache migration needed

---

## Acceptance Criteria

**From Spec.md**:

✅ **SC-004**: Cache hit rate ≥60%  
✅ **SC-005**: Ranking <10ms P50 (cache hit), <30ms P50 (cache miss)  
✅ **SC-006**: Unit test coverage ≥80% for aggregation_module  
✅ **SC-007**: Issue #183 cache leak fixed (memory bounded ≤10MB)  
✅ **SC-013**: Feature flag rollout with automatic fallback  

**Additional Criteria**:
- LRU cache with max_size=1000, TTL=300s
- Hybrid ranking algorithm (text + quality + popularity)
- Correct pagination for all edge cases
- Cache key excludes pagination params
- mypy --strict passes with zero errors
