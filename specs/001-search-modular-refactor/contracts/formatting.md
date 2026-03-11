# Formatting Module Contract

**Module**: `search/formatting_module.py`  
**Purpose**: Convert ranked results to final JSON response structure  
**Phase**: 1 (Week 4 rollout)

---

## Public Interface

### Primary Function

```python
def format_response(
    ranked: RankedResults,
    validated_input: ValidatedSearchInput
) -> SearchResponse:
    """
    Format ranked results into final JSON response.
    
    Args:
        ranked: Ranked results from aggregation_module
        validated_input: Original search parameters (for metadata)
    
    Returns:
        SearchResponse ready for JSON serialization
    
    Raises:
        FormattingError: Only if internal state is invalid (should never happen)
    
    Performance:
        Target: <5ms P50, <10ms P95 for 50 recipes
    
    Side Effects:
        None (pure function)
    """
```

---

## Formatting Logic

### Recipe Object Conversion

**Input**: `Recipe` dataclass from models.py  
**Output**: `Dict[str, Any]` ready for JSON serialization

```python
def _format_recipe(recipe: Recipe) -> Dict[str, Any]:
    """
    Convert Recipe object to JSON-serializable dict.
    
    Handles UUID conversion, ensures all values are JSON-compatible.
    """
    return {
        "id": str(recipe.id),  # UUID → string
        "name": recipe.name,
        "ingredients": recipe.ingredients,  # List[str]
        "dietary_tags": recipe.dietary_tags,  # List[str]
        "cuisine": recipe.cuisine,
        "prep_time_minutes": recipe.prep_time_minutes,
        "difficulty": recipe.difficulty,
        "avg_rating": round(recipe.avg_rating, 1)  # Round to 1 decimal
    }
```

**Transformations**:
- `recipe.id` (UUID) → `str(recipe.id)` (string)
- `recipe.avg_rating` (float) → Rounded to 1 decimal (4.8472 → 4.8)
- All other fields: Pass through as-is (already JSON-compatible)

**Edge Cases**:
- Recipe with empty ingredients: `[]` (valid JSON)
- Recipe with empty dietary_tags: `[]` (valid JSON)
- Recipe with None fields: Should never happen (models enforce non-null)

### Total Pages Calculation

```python
import math

def _calculate_total_pages(total_count: int, page_size: int) -> int:
    """Calculate total pages for pagination metadata."""
    if total_count == 0:
        return 0
    return math.ceil(total_count / page_size)
```

**Examples**:
- 100 recipes, page_size 50 → 2 pages
- 47 recipes, page_size 50 → 1 page
- 101 recipes, page_size 50 → 3 pages
- 0 recipes, any page_size → 0 pages

### Response Structure

**SearchResponse** fields populated:

```python
@dataclass(frozen=True)
class SearchResponse:
    recipes: List[Dict[str, Any]]  # Formatted recipe dicts
    total: int  # Total matching recipes
    page: int  # Current page number
    page_size: int  # Recipes per page
    total_pages: int  # Total pages available
    cache_hit: bool  # Cache indicator
    duration_ms: float  # Total request duration
```

**Field Population**:

1. **recipes**: `[_format_recipe(r) for r in ranked.recipes]`
   - List of dicts, one per recipe on current page
   - Empty list if no results or page beyond range

2. **total**: `ranked.total_count`
   - Total recipes before pagination
   - 0 if no results

3. **page**: `ranked.page`
   - Current page number (1-indexed)
   - Copied from ranked results

4. **page_size**: `ranked.page_size`
   - Recipes per page
   - Copied from ranked results

5. **total_pages**: `_calculate_total_pages(ranked.total_count, ranked.page_size)`
   - Calculated from total_count and page_size
   - 0 if no results

6. **cache_hit**: `ranked.cache_hit`
   - Boolean indicating cache hit
   - Copied from ranked results

7. **duration_ms**: `ranked.total_duration_ms`
   - Total request processing time
   - Copied from ranked results

---

## Backward Compatibility

### Legacy Response Format

**Critical**: This response format **MUST** match legacy search.py exactly.

**Legacy Response** (from search.py):
```python
{
    "recipes": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Pasta Carbonara",
            "ingredients": ["pasta", "eggs", "bacon", "parmesan"],
            "dietary_tags": ["gluten-free"],
            "cuisine": "Italian",
            "prep_time_minutes": 30,
            "difficulty": "medium",
            "avg_rating": 4.5
        },
        ...
    ],
    "total": 47,
    "page": 1,
    "page_size": 50,
    "total_pages": 1,
    "cache_hit": false,
    "duration_ms": 87.3
}
```

**New Response** (from formatting_module):
- **IDENTICAL** structure to legacy
- Same field names, same types, same format
- UUIDs as strings (not objects)
- Ratings rounded to 1 decimal
- All values JSON-serializable

**Validation**:
During rollout, compare responses byte-by-byte:
- Same recipes in same order ✓
- Same pagination metadata ✓
- Same recipe field formats ✓
- Only difference: duration_ms may vary slightly

**Zero Breaking Changes**: API consumers require NO code changes.

---

## Error Handling

### FormattingError Exception

```python
class FormattingError(Exception):
    """Raised when formatting encounters unexpected state."""
    
    def __init__(self, message: str):
        super().__init__(f"Formatting error: {message}")
```

**Error Cases** (should be extremely rare):
- ranked.recipes is None → `FormattingError("recipes cannot be None")`
- Recipe missing required field → `FormattingError("Invalid recipe object")`
- Recipe field not JSON-serializable → `FormattingError("Cannot serialize recipe")`

**Handling**:
- API layer catches FormattingError and returns 500 Internal Server Error
- Log full stack trace for debugging
- Fallback to legacy search if feature flag enabled

**Note**: FormattingError should NEVER occur if Recipe model is correct.

---

## JSON Serialization

### Serialization Method

**Option 1**: Manual dict construction (chosen for control)
```python
def format_response(ranked: RankedResults, validated_input: ValidatedSearchInput) -> SearchResponse:
    """Format response manually for full control."""
    formatted_recipes = [_format_recipe(r) for r in ranked.recipes]
    total_pages = _calculate_total_pages(ranked.total_count, ranked.page_size)
    
    return SearchResponse(
        recipes=formatted_recipes,
        total=ranked.total_count,
        page=ranked.page,
        page_size=ranked.page_size,
        total_pages=total_pages,
        cache_hit=ranked.cache_hit,
        duration_ms=ranked.total_duration_ms
    )
```

**Option 2**: dataclass.asdict() (rejected due to dataclass nesting)

### API Layer Serialization

**API route** (in api/routes.py):
```python
from dataclasses import asdict
import json

@app.post("/search")
def search_endpoint(request: Dict[str, Any], user: User):
    """Search API endpoint."""
    search_request = SearchRequest(**request)
    response = search_recipes(search_request, user)  # Returns SearchResponse
    
    # Convert SearchResponse to dict, then to JSON
    response_dict = asdict(response)
    return json.dumps(response_dict)
```

**Note**: `asdict(response)` works because SearchResponse fields are already JSON-compatible.

---

## Feature Flag Integration

**Flag Name**: `USE_NEW_FORMATTING`  
**Default**: `False` (disabled, use legacy formatting)  
**Rollout**: Week 4 (after aggregation_module deployed)

```python
def search_recipes(request: SearchRequest, user: User):
    """Main search entry point"""
    validated = validate_search_request(request, user)
    filtered = apply_filters(validated, SAMPLE_RECIPES)
    ranked = aggregate_and_rank(filtered, validated)
    
    if os.getenv("USE_NEW_FORMATTING") == "true":
        try:
            response = format_response(ranked, validated)
            return response
        except Exception as e:
            logger.error(f"New formatting failed: {e}")
            # Automatic fallback to legacy
            return _format_with_legacy(ranked, validated)
    else:
        return _format_with_legacy(ranked, validated)
```

**Rollout Strategy**:
- Week 4 Day 1: Enable for 10% traffic (canary)
- Week 4 Day 3: Enable for 50% traffic (if no issues)
- Week 4 Day 5: Enable for 100% traffic (if response format matches legacy 100%)

**Success Metrics**:
- Format duration <5ms P50
- Response format matches legacy 100%
- Zero 500 errors from formatting
- Zero JSON serialization errors

---

## Testing Requirements

### Unit Tests (Target: 90% coverage)

**tests/unit/test_formatting_module.py**:

1. **test_format_recipe_converts_uuid_to_string**
   - Input: Recipe with UUID id
   - Expected: Output dict has "id" as string

2. **test_format_recipe_rounds_rating**
   - Input: Recipe with avg_rating=4.8472
   - Expected: Output dict has "avg_rating"=4.8

3. **test_format_recipe_preserves_all_fields**
   - Input: Recipe with all fields
   - Expected: Output dict contains all 8 fields

4. **test_format_recipe_handles_empty_lists**
   - Input: Recipe with ingredients=[], dietary_tags=[]
   - Expected: Output dict has empty lists (valid JSON)

5. **test_format_response_populates_all_fields**
   - Input: RankedResults with 10 recipes
   - Expected: SearchResponse contains all 7 fields

6. **test_format_response_empty_recipes**
   - Input: RankedResults with 0 recipes
   - Expected: SearchResponse.recipes=[], total=0, total_pages=0

7. **test_format_response_single_page**
   - Input: 47 recipes, page_size=50
   - Expected: total_pages=1

8. **test_format_response_multiple_pages**
   - Input: 150 recipes, page_size=50
   - Expected: total_pages=3

9. **test_format_response_cache_hit_preserved**
   - Input: RankedResults with cache_hit=True
   - Expected: SearchResponse.cache_hit=True

10. **test_format_response_duration_preserved**
    - Input: RankedResults with total_duration_ms=87.3
    - Expected: SearchResponse.duration_ms=87.3

11. **test_total_pages_calculation**
    - Test cases: (0, 50) → 0, (47, 50) → 1, (100, 50) → 2, (101, 50) → 3
    - Expected: Correct total_pages for all cases

12. **test_json_serialization**
    - Input: SearchResponse with various data
    - Expected: `json.dumps(asdict(response))` succeeds without errors

### Contract Tests (Target: 100% interface coverage)

**tests/contract/test_formatting_contract.py**:

1. **test_contract_returns_search_response_type**
   - Assert return type is SearchResponse

2. **test_contract_recipes_list_never_none**
   - Assert SearchResponse.recipes is List (may be empty, never None)

3. **test_contract_all_fields_json_serializable**
   - Assert `json.dumps(asdict(response))` succeeds
   - Assert no TypeError or ValueError

4. **test_contract_recipe_dicts_have_required_keys**
   - Assert each recipe dict has: id, name, ingredients, dietary_tags, cuisine, prep_time_minutes, difficulty, avg_rating

5. **test_contract_total_pages_matches_calculation**
   - Assert total_pages == ceil(total / page_size)

6. **test_contract_pagination_metadata_consistent**
   - Assert page ≥ 1, page_size ≥ 1, total_pages ≥ 0

### Integration Tests

**tests/integration/test_full_search_pipeline.py**:

1. **test_end_to_end_search_pipeline**
   - Run SearchRequest → validate → filter → aggregate → format
   - Assert final SearchResponse is valid and JSON-serializable

2. **test_backward_compatibility_response_format**
   - Compare new formatting_module output vs legacy search.py output
   - Assert structure identical (field names, types, formats)

3. **test_api_endpoint_returns_json**
   - Call `/search` endpoint with test request
   - Assert response is valid JSON with expected structure

---

## Performance Requirements

### Targets

- **P50 latency**: <5ms for 50 recipes
- **P95 latency**: <10ms for 50 recipes
- **P99 latency**: <20ms for 200 recipes
- **Throughput**: ≥10,000 requests/second (single thread)
- **Memory**: <1KB per formatting operation

### Optimization Strategies

1. **List comprehension**: Use `[_format_recipe(r) for r in recipes]` (faster than loops)
2. **No deep copying**: Recipe objects are immutable
3. **Minimal transformations**: Only UUID→string and rating rounding
4. **No I/O operations**: Pure in-memory computation
5. **No external calls**: No database or API calls

### Benchmarking

**tests/performance/test_formatting_performance.py**:
```python
def test_formatting_performance():
    """Ensure formatting meets performance targets"""
    ranked = create_sample_ranked_results(50)
    validated = create_sample_validated_input()
    
    durations = []
    for _ in range(1000):
        start = time.perf_counter()
        format_response(ranked, validated)
        durations.append((time.perf_counter() - start) * 1000)
    
    p50 = percentile(durations, 50)
    p95 = percentile(durations, 95)
    
    assert p50 < 5.0, f"P50 {p50}ms exceeds 5ms target"
    assert p95 < 10.0, f"P95 {p95}ms exceeds 10ms target"
```

---

## Logging & Observability

### Logging Events

```python
import logging
logger = logging.getLogger(__name__)

# Success (DEBUG level)
logger.debug(f"Formatted response for user {validated_input.user_id}", extra={
    "user_id": validated_input.user_id,
    "recipe_count": len(response.recipes),
    "total_pages": response.total_pages,
    "cache_hit": response.cache_hit,
    "duration_ms": response.duration_ms
})

# Empty results (INFO level)
if response.total == 0:
    logger.info(f"Empty search result", extra={
        "user_id": validated_input.user_id,
        "query": validated_input.query,
        "filters": len(validated_input.dietary_restrictions)
    })

# Performance warning (WARNING level)
if format_duration_ms > 10:
    logger.warning(f"Slow formatting: {format_duration_ms}ms", extra={
        "user_id": validated_input.user_id,
        "duration_ms": format_duration_ms,
        "recipe_count": len(ranked.recipes)
    })
```

### Metrics to Track

1. **formatting_success_total** (counter): Successful formatting operations
2. **formatting_duration_seconds** (histogram): Formatting latency distribution
3. **response_size_bytes** (histogram): JSON response size distribution
4. **empty_result_total** (counter): Responses with 0 results

---

## Dependencies

### Internal
- `models.Recipe`: Recipe object structure
- `search.types.RankedResults`: Input type
- `search.types.ValidatedSearchInput`: For metadata
- `search.types.SearchResponse`: Output type

### External
- `dataclasses`: For dataclass types
- `typing`: For type hints
- `logging`: For observability
- `json`: For JSON serialization (in API layer)
- `math.ceil`: For total pages calculation

**No Database or External API Calls**: Pure formatting logic.

---

## Backward Compatibility Verification

### Response Comparison Test

**tests/integration/test_backward_compatibility.py**:

```python
def test_response_format_matches_legacy_exactly():
    """
    Verify new formatting produces identical response to legacy.
    
    This test ensures zero breaking changes for API consumers.
    """
    # Create test request
    request = SearchRequest(
        query="pasta",
        cuisine="Italian",
        dietary_restrictions=["vegan"],
        min_rating=4.0,
        page=1,
        page_size=50
    )
    user = create_sample_user()
    
    # Get legacy response
    legacy_response = legacy_search_recipes(request, user)
    
    # Get new response (all modules enabled)
    new_response = search_recipes(request, user)  # With all feature flags enabled
    
    # Compare structure
    assert set(new_response.keys()) == set(legacy_response.keys()), \
        "Response keys must match legacy exactly"
    
    # Compare recipes
    assert len(new_response["recipes"]) == len(legacy_response["recipes"]), \
        "Recipe count must match"
    
    for new_recipe, legacy_recipe in zip(new_response["recipes"], legacy_response["recipes"]):
        assert set(new_recipe.keys()) == set(legacy_recipe.keys()), \
            "Recipe keys must match"
        assert new_recipe["id"] == legacy_recipe["id"], \
            "Recipe IDs must match (same recipes returned)"
        assert new_recipe["name"] == legacy_recipe["name"], \
            "Recipe names must match"
    
    # Compare pagination metadata
    assert new_response["total"] == legacy_response["total"]
    assert new_response["page"] == legacy_response["page"]
    assert new_response["page_size"] == legacy_response["page_size"]
    assert new_response["total_pages"] == legacy_response["total_pages"]
    
    # Note: duration_ms and cache_hit may differ (expected)
```

**Pass Criteria**: 100% of fields match (except duration_ms, cache_hit)

---

## Edge Cases

### Empty Results

**Input**: RankedResults with 0 recipes  
**Output**: 
```python
SearchResponse(
    recipes=[],
    total=0,
    page=1,
    page_size=50,
    total_pages=0,
    cache_hit=False,
    duration_ms=12.5
)
```

**JSON**:
```json
{
    "recipes": [],
    "total": 0,
    "page": 1,
    "page_size": 50,
    "total_pages": 0,
    "cache_hit": false,
    "duration_ms": 12.5
}
```

### Page Beyond Range

**Input**: RankedResults with total_count=47, page=2, page_size=50  
**Output**: 
```python
SearchResponse(
    recipes=[],  # Empty because page beyond range
    total=47,
    page=2,
    page_size=50,
    total_pages=1,
    cache_hit=False,
    duration_ms=25.3
)
```

**Note**: This is NOT an error. Frontend shows "No results on this page" message.

### Large Result Set

**Input**: RankedResults with 200 recipes on page 1  
**Output**: Same format, recipes list has 50 items (page_size=50)

**Note**: JSON response size ~30KB for 50 recipes (well under typical limits)

---

## Acceptance Criteria

**From Spec.md**:

✅ **SC-005**: Formatting <5ms P50, <10ms P95  
✅ **SC-006**: Unit test coverage ≥80% for formatting_module  
✅ **SC-010**: Response format matches legacy 100%  
✅ **SC-011**: All modules work together (end-to-end)  
✅ **SC-012**: Zero breaking changes for API consumers  
✅ **SC-013**: Feature flag rollout with automatic fallback  

**Additional Criteria**:
- SearchResponse structure identical to legacy
- UUIDs serialized as strings
- Ratings rounded to 1 decimal
- total_pages calculation correct
- JSON serialization successful for all cases
- mypy --strict passes with zero errors

---

## Final Integration

### Complete Search Pipeline

**With all modules enabled**:

```python
def search_recipes(request: SearchRequest, user: User) -> SearchResponse:
    """
    Main search entry point with modular refactored implementation.
    
    Pipeline: validate → filter → aggregate → format
    """
    # Phase 1: Validation
    validated = validate_search_request(request, user)
    
    # Phase 2: Filtering
    filtered = apply_filters(validated, SAMPLE_RECIPES)
    
    # Phase 3: Aggregation & Ranking
    ranked = aggregate_and_rank(filtered, validated)
    
    # Phase 4: Formatting
    response = format_response(ranked, validated)
    
    return response
```

**Feature Flags** (gradual rollout):
- Week 1: `USE_NEW_VALIDATION` (fixes Issue #447)
- Week 2: `USE_NEW_FILTERING` (independent testability)
- Week 3: `USE_NEW_AGGREGATION` (fixes Issue #183 cache leak)
- Week 4: `USE_NEW_FORMATTING` (completes refactor)

**Success**: All 4 modules enabled, legacy search.py deprecated, zero breaking changes.
