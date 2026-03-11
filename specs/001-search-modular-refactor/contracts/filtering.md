# Filtering Module Contract

**Module**: `search/filtering_module.py`  
**Purpose**: Apply query and filter criteria to recipe collection  
**Phase**: 1 (Week 2 rollout)

---

## Public Interface

### Primary Function

```python
def apply_filters(
    validated_input: ValidatedSearchInput,
    recipes: List[Recipe]
) -> FilteredRecipes:
    """
    Apply all search filters to recipe collection.
    
    Args:
        validated_input: Validated search parameters (from validation_module)
        recipes: Full recipe collection to filter (typically SAMPLE_RECIPES)
    
    Returns:
        FilteredRecipes with recipes matching all criteria
    
    Raises:
        FilteringError: Only if recipes collection is invalid (should never happen)
    
    Performance:
        Target: <20ms P50 for 1000 recipes, <50ms P95
    
    Side Effects:
        None (pure function, no database queries)
    """
```

---

## Filter Execution Order

**Order matters for performance**: Most selective filters first to minimize work.

1. **Query filter** (if query not empty)
   - Matches against: recipe.name, recipe.ingredients (text search)
   - Short-circuit: Return empty if no matches

2. **Cuisine filter** (if cuisine specified)
   - Matches: recipe.cuisine == validated_input.cuisine (exact match)
   - Applied to: Results from query filter

3. **Dietary restrictions filter** (if restrictions list not empty)
   - Matches: All restrictions in recipe.dietary_tags
   - Applied to: Results from cuisine filter

4. **Prep time filter** (if prep_time_max specified)
   - Matches: recipe.prep_time_minutes ≤ validated_input.prep_time_max
   - Applied to: Results from dietary filter

5. **Difficulty filter** (if difficulty specified)
   - Matches: recipe.difficulty == validated_input.difficulty
   - Applied to: Results from prep time filter

6. **Rating filter** (always applied, may be 0.0)
   - Matches: recipe.avg_rating ≥ validated_input.min_rating
   - Applied to: Results from difficulty filter

**Rationale**:
- Query filter most selective (eliminates ~80% of recipes)
- Cuisine filter second (eliminates ~70% of remaining)
- Dietary restrictions third (eliminates ~50% of remaining)
- Prep time, difficulty, rating least selective (eliminate ~10-20% each)

**Short-Circuit Optimization**:
If any filter returns 0 results, immediately return empty FilteredRecipes
(no need to apply remaining filters).

---

## Filter Implementation Details

### 1. Query Filter

**Algorithm**: Case-insensitive substring match on name AND ingredients

```python
def _filter_by_query(recipes: List[Recipe], query: str) -> List[Recipe]:
    """
    Filter recipes by text query.
    
    Query must match recipe name OR any ingredient (case-insensitive).
    Empty query returns all recipes.
    """
    if not query:  # Empty query = no filter
        return recipes
    
    query_lower = query.lower()  # Already lowercased by validation, but defensive
    
    return [
        recipe for recipe in recipes
        if query_lower in recipe.name.lower()
        or any(query_lower in ingredient.lower() for ingredient in recipe.ingredients)
    ]
```

**Performance**:
- O(n * m) where n = recipes, m = avg ingredients per recipe
- Typically filters 1000 recipes in <10ms
- Short-circuit on name match (avoid ingredient iteration)

**Edge Cases**:
- Empty query: Return all recipes (no filtering)
- Query with special chars: Already sanitized by validation_module
- Unicode: Python 3.11 handles naturally

### 2. Cuisine Filter

**Algorithm**: Exact match on cuisine type

```python
def _filter_by_cuisine(recipes: List[Recipe], cuisine: Optional[str]) -> List[Recipe]:
    """
    Filter recipes by cuisine type.
    
    Exact match required (already normalized by validation_module).
    None cuisine returns all recipes.
    """
    if cuisine is None:  # No cuisine filter
        return recipes
    
    return [recipe for recipe in recipes if recipe.cuisine == cuisine]
```

**Performance**:
- O(n) where n = recipes
- Typically filters in <2ms

**Edge Cases**:
- None cuisine: Return all recipes (no filtering)
- Case sensitivity: Already normalized by validation_module (e.g., "Italian")

### 3. Dietary Restrictions Filter

**Algorithm**: ALL restrictions must be in recipe.dietary_tags (AND logic)

```python
def _filter_by_dietary_restrictions(
    recipes: List[Recipe],
    restrictions: List[str]
) -> List[Recipe]:
    """
    Filter recipes by dietary restrictions.
    
    ALL restrictions must be present in recipe.dietary_tags.
    Empty restrictions list returns all recipes.
    
    CRITICAL: restrictions is NEVER None (guaranteed by validation_module).
    This fixes Issue #447.
    """
    if not restrictions:  # Empty list = no filter
        return recipes
    
    # Convert to set for O(1) membership checks
    required_tags = set(restrictions)
    
    return [
        recipe for recipe in recipes
        if required_tags.issubset(set(recipe.dietary_tags))
    ]
```

**Performance**:
- O(n * k) where n = recipes, k = avg dietary tags per recipe
- Set intersection is O(k) per recipe
- Typically filters in <5ms

**Edge Cases**:
- Empty restrictions: Return all recipes (no filtering)
- **restrictions is NEVER None**: Guaranteed by validation_module (Issue #447 fix)
- Recipe with no dietary tags: `set(recipe.dietary_tags) = {}`, will not match any restrictions

**Critical**:
This is where Issue #447 was originally triggered in legacy code:
```python
# Legacy code (BROKEN):
for restriction in user.dietary_restrictions:  # TypeError if None!
    ...

# New code (FIXED):
if not restrictions:  # restrictions is List[str], never None
    return recipes
```

### 4. Prep Time Filter

**Algorithm**: Recipe prep time must be ≤ max

```python
def _filter_by_prep_time(
    recipes: List[Recipe],
    prep_time_max: Optional[int]
) -> List[Recipe]:
    """
    Filter recipes by maximum prep time.
    
    None prep_time_max returns all recipes.
    """
    if prep_time_max is None:  # No prep time filter
        return recipes
    
    return [
        recipe for recipe in recipes
        if recipe.prep_time_minutes <= prep_time_max
    ]
```

**Performance**:
- O(n) where n = recipes
- Typically filters in <2ms

**Edge Cases**:
- None prep_time_max: Return all recipes
- prep_time_max = 0: Return only recipes with 0 prep time (valid but rare)

### 5. Difficulty Filter

**Algorithm**: Exact match on difficulty level

```python
def _filter_by_difficulty(
    recipes: List[Recipe],
    difficulty: Optional[str]
) -> List[Recipe]:
    """
    Filter recipes by difficulty level.
    
    Exact match required (already normalized by validation_module).
    None difficulty returns all recipes.
    """
    if difficulty is None:  # No difficulty filter
        return recipes
    
    return [recipe for recipe in recipes if recipe.difficulty == difficulty]
```

**Performance**:
- O(n) where n = recipes
- Typically filters in <2ms

**Edge Cases**:
- None difficulty: Return all recipes
- Case sensitivity: Already normalized by validation_module (e.g., "easy")

### 6. Rating Filter

**Algorithm**: Recipe rating must be ≥ minimum

```python
def _filter_by_rating(recipes: List[Recipe], min_rating: float) -> List[Recipe]:
    """
    Filter recipes by minimum rating.
    
    min_rating is never None (default 0.0 from validation_module).
    """
    # min_rating is always float (never None), so always apply
    return [recipe for recipe in recipes if recipe.avg_rating >= min_rating]
```

**Performance**:
- O(n) where n = recipes
- Typically filters in <2ms

**Edge Cases**:
- min_rating = 0.0: Return all recipes (no filtering)
- min_rating = 5.0: Return only perfect-rated recipes

---

## Output Structure

**FilteredRecipes** contains:

```python
@dataclass(frozen=True)
class FilteredRecipes:
    recipes: List[Recipe]  # Recipes matching ALL filters
    applied_filters: Dict[str, Any]  # Which filters were applied
    filter_duration_ms: float  # Time taken to filter
    total_before_filters: int  # Total recipes before filtering
```

### Field Population

**recipes**:
- Contains ALL recipes matching every filter
- Order is arbitrary (ranking happens in aggregation_module)
- Empty list if no matches

**applied_filters**:
Includes only filters that were actually applied (not None/empty):
```python
{
    "query": "pasta",  # Only if query not empty
    "cuisine": "Italian",  # Only if cuisine not None
    "dietary_restrictions": ["vegan"],  # Only if restrictions not empty
    "prep_time_max": 30,  # Only if prep_time_max not None
    "difficulty": "easy",  # Only if difficulty not None
    "min_rating": 4.0  # Always included (never None)
}
```

**filter_duration_ms**:
- Time from start of apply_filters() to return
- Includes all filter steps and metadata generation
- Target: <20ms P50

**total_before_filters**:
- Length of input recipes list
- Used for metrics: "10 recipes → 3 after filtering (70% filtered)"

---

## Error Handling

### FilteringError Exception

```python
class FilteringError(Exception):
    """Raised when filtering encounters unexpected state."""
    
    def __init__(self, message: str):
        super().__init__(f"Filtering error: {message}")
```

**Error Cases** (should be extremely rare):
- Input recipes is None → `FilteringError("recipes cannot be None")`
- Recipe missing required fields → `FilteringError("Invalid recipe object")`

**Handling**:
- API layer catches FilteringError and returns 500 Internal Server Error
- Log full stack trace for debugging
- Fallback to legacy search if feature flag enabled

**Note**: FilteringError should NEVER occur if validation_module and models are correct.

---

## Feature Flag Integration

**Flag Name**: `USE_NEW_FILTERING`  
**Default**: `False` (disabled, use legacy filtering)  
**Rollout**: Week 2 (after validation_module deployed)

```python
def search_recipes(request: SearchRequest, user: User):
    """Main search entry point"""
    validated = validate_search_request(request, user)
    
    if os.getenv("USE_NEW_FILTERING") == "true":
        try:
            filtered = apply_filters(validated, SAMPLE_RECIPES)
            # Pass to aggregation module (or legacy if not ready)
            return _search_with_new_filtering(filtered, validated)
        except Exception as e:
            logger.error(f"New filtering failed: {e}")
            # Automatic fallback to legacy
            return _search_with_legacy_filtering(validated, user)
    else:
        return _search_with_legacy_filtering(validated, user)
```

**Rollout Strategy**:
- Week 2 Day 1: Enable for 10% traffic (canary)
- Week 2 Day 3: Enable for 50% traffic (if no issues)
- Week 2 Day 5: Enable for 100% traffic (if performance meets targets)

**Success Metrics**:
- Filter duration <20ms P50, <50ms P95
- Zero 500 errors from filtering
- Result correctness: 100% match with legacy (A/B comparison)

---

## Testing Requirements

### Unit Tests (Target: 85% coverage)

**tests/unit/test_filtering_module.py**:

1. **test_query_filter_matches_name**
   - Input: query="pasta", recipes with "Pasta Carbonara"
   - Expected: Recipe included in results

2. **test_query_filter_matches_ingredient**
   - Input: query="tomato", recipes with tomato in ingredients
   - Expected: Recipe included in results

3. **test_query_filter_empty_returns_all**
   - Input: query="", recipes
   - Expected: All recipes returned

4. **test_cuisine_filter_exact_match**
   - Input: cuisine="Italian", recipes with cuisine="Italian"
   - Expected: Only Italian recipes

5. **test_cuisine_filter_none_returns_all**
   - Input: cuisine=None, recipes
   - Expected: All recipes returned

6. **test_dietary_restrictions_all_required**
   - Input: restrictions=["vegan", "gluten-free"], recipes
   - Expected: Only recipes with BOTH tags

7. **test_dietary_restrictions_empty_returns_all**
   - Input: restrictions=[], recipes
   - Expected: All recipes returned

8. **test_dietary_restrictions_never_none**
   - Input: restrictions=[] (never None from validation_module)
   - Expected: No TypeError (Issue #447 verification)

9. **test_prep_time_filter_less_than_or_equal**
   - Input: prep_time_max=30, recipes with prep times 20, 30, 40
   - Expected: Only recipes with ≤30 minutes

10. **test_prep_time_filter_none_returns_all**
    - Input: prep_time_max=None, recipes
    - Expected: All recipes returned

11. **test_difficulty_filter_exact_match**
    - Input: difficulty="easy", recipes with difficulty="easy"
    - Expected: Only easy recipes

12. **test_rating_filter_greater_than_or_equal**
    - Input: min_rating=4.0, recipes with ratings 3.5, 4.0, 4.5
    - Expected: Only recipes with ≥4.0 rating

13. **test_combined_filters_all_criteria**
    - Input: query="pasta", cuisine="Italian", restrictions=["vegan"]
    - Expected: Only recipes matching ALL criteria

14. **test_short_circuit_on_empty_query**
    - Input: query="nonexistent", other filters present
    - Expected: Empty results, minimal processing time

15. **test_applied_filters_metadata**
    - Input: Various filter combinations
    - Expected: applied_filters dict contains only non-None/non-empty filters

### Contract Tests (Target: 100% interface coverage)

**tests/contract/test_filtering_contract.py**:

1. **test_contract_returns_filtered_recipes_type**
   - Assert return type is FilteredRecipes

2. **test_contract_recipes_list_never_none**
   - Assert FilteredRecipes.recipes is List (may be empty, never None)

3. **test_contract_applied_filters_dict_never_none**
   - Assert applied_filters is Dict (may be empty, never None)

4. **test_contract_duration_always_positive**
   - Assert filter_duration_ms ≥ 0.0

5. **test_contract_total_before_filters_matches_input**
   - Assert total_before_filters == len(input recipes)

### Integration Tests

**tests/integration/test_validation_filtering.py**:

1. **test_validation_to_filtering_pipeline**
   - Run SearchRequest → validate_search_request → apply_filters
   - Assert end-to-end correctness

2. **test_issue_447_prevented_end_to_end**
   - Input: SearchRequest(dietary_restrictions=None)
   - Assert no TypeError in filtering (validation normalizes to [])

---

## Performance Requirements

### Targets

- **P50 latency**: <20ms for 1000 recipes
- **P95 latency**: <50ms for 1000 recipes
- **P99 latency**: <100ms for 1000 recipes
- **Throughput**: ≥500 requests/second (single thread)
- **Memory**: <10KB per filtering operation

### Optimization Strategies

1. **Short-circuit evaluation**: Stop filtering if results empty
2. **Set operations**: Use set intersection for dietary restrictions (O(1) lookup)
3. **Lazy evaluation**: Don't compute metadata until needed
4. **No database queries**: All filtering in-memory on SAMPLE_RECIPES
5. **No deep copying**: Filter by reference (recipes are immutable)

### Benchmarking

**tests/performance/test_filtering_performance.py**:
```python
def test_filtering_performance():
    """Ensure filtering meets performance targets"""
    validated = ValidatedSearchInput(
        query="pasta",
        cuisine="Italian",
        dietary_restrictions=["vegan"],
        prep_time_max=30,
        difficulty="easy",
        min_rating=4.0,
        page=1,
        page_size=50,
        user_id="test-user"
    )
    
    recipes = load_1000_sample_recipes()
    
    durations = []
    for _ in range(1000):
        start = time.perf_counter()
        apply_filters(validated, recipes)
        durations.append((time.perf_counter() - start) * 1000)
    
    p50 = percentile(durations, 50)
    p95 = percentile(durations, 95)
    
    assert p50 < 20.0, f"P50 {p50}ms exceeds 20ms target"
    assert p95 < 50.0, f"P95 {p95}ms exceeds 50ms target"
```

---

## Logging & Observability

### Logging Events

```python
import logging
logger = logging.getLogger(__name__)

# Success (DEBUG level)
logger.debug(f"Filtered recipes for user {validated.user_id}", extra={
    "user_id": validated.user_id,
    "recipes_before": total_before,
    "recipes_after": len(filtered.recipes),
    "filters_applied": list(filtered.applied_filters.keys()),
    "duration_ms": filtered.filter_duration_ms
})

# Empty results (INFO level)
if not filtered.recipes:
    logger.info(f"No recipes matched filters", extra={
        "user_id": validated.user_id,
        "applied_filters": filtered.applied_filters
    })

# Performance warning (WARNING level)
if filter_duration_ms > 50:
    logger.warning(f"Slow filtering: {filter_duration_ms}ms", extra={
        "user_id": validated.user_id,
        "duration_ms": filter_duration_ms,
        "recipes_count": len(recipes)
    })
```

### Metrics to Track

1. **filtering_success_total** (counter): Successful filtering operations
2. **filtering_empty_results_total** (counter): Filtering returned 0 results
3. **filtering_duration_seconds** (histogram): Filtering latency distribution
4. **recipes_filtered_total** (histogram): Number of recipes after filtering
5. **filter_selectivity_ratio** (histogram): recipes_after / recipes_before

---

## Dependencies

### Internal
- `models.Recipe`: Recipe object structure
- `search.types.ValidatedSearchInput`: Input type
- `search.types.FilteredRecipes`: Output type

### External
- `dataclasses`: For dataclass types
- `typing`: For type hints
- `logging`: For observability
- `time.perf_counter`: For duration measurement

**No Database or External API Calls**: All filtering in-memory.

---

## Backward Compatibility

**Public API Unchanged**:
- Legacy `search_recipes(request, user)` signature preserved
- New filtering only used when feature flag enabled
- Automatic fallback to legacy filtering on errors
- Zero breaking changes for API consumers

**Result Correctness**:
During rollout, compare results from new filtering vs legacy:
- Log any discrepancies for investigation
- If discrepancy rate >0.1%, halt rollout and investigate
- Expect 100% correctness match (new should be identical to legacy)

---

## Acceptance Criteria

**From Spec.md**:

✅ **SC-005**: Filter execution <20ms P50, <50ms P95  
✅ **SC-006**: Unit test coverage ≥80% for filtering_module  
✅ **SC-010**: Filtering results match legacy 100%  
✅ **SC-013**: Feature flag rollout with automatic fallback  
✅ **SC-014**: Issue #447 prevented (dietary_restrictions never None)

**Additional Criteria**:
- All 6 filter types implemented (query, cuisine, dietary, prep_time, difficulty, rating)
- Short-circuit optimization on empty results
- Correct filter order (most selective first)
- applied_filters metadata accurate
- mypy --strict passes with zero errors
