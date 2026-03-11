# Validation Module Contract

**Module**: `search/validation_module.py`  
**Purpose**: Validate and normalize untrusted API inputs  
**Phase**: 1 (Week 1 rollout)

---

## Public Interface

### Primary Function

```python
def validate_search_request(
    request: SearchRequest,
    user: User
) -> ValidatedSearchInput:
    """
    Validate and normalize raw search request.
    
    Args:
        request: Untrusted input from API layer
        user: Authenticated user object (for user_id)
    
    Returns:
        ValidatedSearchInput with all fields validated and normalized
    
    Raises:
        ValidationError: If any input is invalid and cannot be normalized
    
    Performance:
        Target: <5ms P50, <15ms P95
    
    Side Effects:
        None (pure function)
    """
```

---

## Input Validation Rules

### query (Optional[str] → str)
- **None or empty**: Normalize to `""`
- **Max length**: 500 characters (truncate if longer)
- **Trimming**: Leading/trailing whitespace removed
- **Case**: Lowercased for consistent filtering
- **SQL safety**: Escape special characters if needed
- **Invalid**: Empty string allowed (means "all recipes")

### cuisine (Optional[str] → Optional[str])
- **None**: Pass through as None (means "any cuisine")
- **Valid values**: Must be in VALID_CUISINES set or None
- **Case**: Normalized to title case ("italian" → "Italian")
- **Invalid**: Raise ValidationError if not in VALID_CUISINES

**VALID_CUISINES**:
```python
VALID_CUISINES = {
    "Italian", "Chinese", "Mexican", "Indian", "Thai",
    "Japanese", "American", "French", "Mediterranean", "Korean"
}
```

### dietary_restrictions (Optional[List[str]] → List[str])
- **None**: **Normalize to []** (empty list) ← **Issue #447 FIX**
- **Empty list**: Pass through as []
- **Valid values**: Each item must be in VALID_DIETARY_RESTRICTIONS
- **Case**: Normalized to lowercase ("Vegan" → "vegan")
- **Duplicates**: Remove duplicates (["vegan", "vegan"] → ["vegan"])
- **Invalid**: Raise ValidationError if any item not in VALID_DIETARY_RESTRICTIONS

**VALID_DIETARY_RESTRICTIONS**:
```python
VALID_DIETARY_RESTRICTIONS = {
    "vegetarian", "vegan", "gluten-free", "dairy-free",
    "nut-free", "keto", "paleo", "low-carb"
}
```

**Critical**: This field **MUST NEVER be None** in ValidatedSearchInput.
This is the root cause fix for Issue #447.

### prep_time_max (Optional[int] → Optional[int])
- **None**: Pass through as None (means "any prep time")
- **Valid range**: Must be positive integer (1-9999 minutes)
- **Invalid**: Raise ValidationError if ≤0 or >9999

### difficulty (Optional[str] → Optional[str])
- **None**: Pass through as None (means "any difficulty")
- **Valid values**: Must be in {"easy", "medium", "hard"} or None
- **Case**: Normalized to lowercase
- **Invalid**: Raise ValidationError if not in valid set

### min_rating (Optional[float] → float)
- **None**: Default to 0.0 (means "any rating")
- **Valid range**: 0.0-5.0 (inclusive)
- **Rounding**: Round to 1 decimal place
- **Invalid**: Raise ValidationError if <0.0 or >5.0

### page (Optional[int] → int)
- **None**: Default to 1
- **Valid range**: Must be ≥1
- **Invalid**: Raise ValidationError if <1

### page_size (Optional[int] → int)
- **None**: Default to 50
- **Valid range**: 1-200 (prevents abuse)
- **Invalid**: Raise ValidationError if <1 or >200

---

## Output Guarantees

**ValidatedSearchInput** returned by this module guarantees:

1. **dietary_restrictions is NEVER None** (always List[str], may be empty)
2. **query is NEVER None** (always str, may be empty)
3. **min_rating is NEVER None** (always float 0.0-5.0)
4. **page is NEVER None** (always int ≥1)
5. **page_size is NEVER None** (always int 1-200)
6. All string fields are trimmed and normalized
7. All values are safe for database queries
8. user_id is populated from user.id

**These guarantees eliminate all None checks in downstream modules.**

---

## Error Handling

### ValidationError Exception

```python
class ValidationError(Exception):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, value: Any, message: str):
        self.field = field
        self.value = value
        self.message = message
        super().__init__(f"Validation error for {field}: {message}")
```

**Error Cases**:
- Invalid cuisine not in VALID_CUISINES → `ValidationError("cuisine", "Spanish", "Invalid cuisine")`
- Invalid dietary restriction → `ValidationError("dietary_restrictions", ["xyz"], "Invalid restriction")`
- prep_time_max ≤0 → `ValidationError("prep_time_max", -10, "Must be positive")`
- page <1 → `ValidationError("page", 0, "Must be ≥1")`
- page_size >200 → `ValidationError("page_size", 500, "Must be ≤200")`

**Handling**:
- API layer catches ValidationError and returns 400 Bad Request
- Error message includes which field failed and why
- Never expose internal details (stack traces, etc.)

---

## Feature Flag Integration

**Flag Name**: `USE_NEW_VALIDATION`  
**Default**: `False` (disabled, use legacy validation)  
**Rollout**: Week 1 (after Phase 1 testing)

```python
def search_recipes(request: SearchRequest, user: User):
    """Main search entry point (legacy code)"""
    if os.getenv("USE_NEW_VALIDATION") == "true":
        try:
            validated = validate_search_request(request, user)
            # Pass to filtering module (or legacy if not ready)
            return _search_with_new_validation(validated, user)
        except Exception as e:
            logger.error(f"New validation failed: {e}")
            # Automatic fallback to legacy
            return _search_with_legacy_validation(request, user)
    else:
        return _search_with_legacy_validation(request, user)
```

**Rollout Strategy**:
- Week 1 Day 1: Enable for 10% traffic (canary)
- Week 1 Day 3: Enable for 50% traffic (if no issues)
- Week 1 Day 5: Enable for 100% traffic (if success rate >99.9%)

**Success Metrics**:
- Issue #447 crash rate → 0 (currently 30% of requests)
- Validation duration <5ms P50
- Zero 500 errors from validation
- Error rate <0.1% (400 errors for truly invalid input)

---

## Testing Requirements

### Unit Tests (Target: 90% coverage)

**tests/unit/test_validation_module.py**:

1. **test_none_dietary_restrictions_normalized_to_empty_list**
   - Input: SearchRequest(dietary_restrictions=None)
   - Expected: ValidatedSearchInput.dietary_restrictions == []
   - **This test prevents Issue #447 regression**

2. **test_empty_dietary_restrictions_preserved**
   - Input: SearchRequest(dietary_restrictions=[])
   - Expected: ValidatedSearchInput.dietary_restrictions == []

3. **test_valid_dietary_restrictions_normalized**
   - Input: SearchRequest(dietary_restrictions=["Vegan", "GLUTEN-FREE"])
   - Expected: ValidatedSearchInput.dietary_restrictions == ["vegan", "gluten-free"]

4. **test_invalid_dietary_restriction_raises_error**
   - Input: SearchRequest(dietary_restrictions=["invalid"])
   - Expected: ValidationError("dietary_restrictions", ...)

5. **test_duplicate_dietary_restrictions_removed**
   - Input: SearchRequest(dietary_restrictions=["vegan", "vegan"])
   - Expected: ValidatedSearchInput.dietary_restrictions == ["vegan"]

6. **test_none_query_normalized_to_empty_string**
   - Input: SearchRequest(query=None)
   - Expected: ValidatedSearchInput.query == ""

7. **test_query_trimmed_and_lowercased**
   - Input: SearchRequest(query="  PASTA  ")
   - Expected: ValidatedSearchInput.query == "pasta"

8. **test_query_truncated_if_too_long**
   - Input: SearchRequest(query="x" * 1000)
   - Expected: ValidatedSearchInput.query has length 500

9. **test_invalid_cuisine_raises_error**
   - Input: SearchRequest(cuisine="Martian")
   - Expected: ValidationError("cuisine", ...)

10. **test_valid_cuisine_normalized**
    - Input: SearchRequest(cuisine="italian")
    - Expected: ValidatedSearchInput.cuisine == "Italian"

11. **test_prep_time_negative_raises_error**
    - Input: SearchRequest(prep_time_max=-10)
    - Expected: ValidationError("prep_time_max", ...)

12. **test_page_zero_raises_error**
    - Input: SearchRequest(page=0)
    - Expected: ValidationError("page", ...)

13. **test_page_size_exceeds_max_raises_error**
    - Input: SearchRequest(page_size=500)
    - Expected: ValidationError("page_size", ...)

14. **test_min_rating_out_of_range_raises_error**
    - Input: SearchRequest(min_rating=6.0)
    - Expected: ValidationError("min_rating", ...)

15. **test_all_defaults_applied**
    - Input: SearchRequest() (all None)
    - Expected: ValidatedSearchInput with all defaults (query="", dietary_restrictions=[], page=1, etc.)

### Contract Tests (Target: 100% coverage of interface)

**tests/contract/test_validation_contract.py**:

1. **test_contract_dietary_restrictions_never_none**
   - Run validate_search_request() with 100 random SearchRequest inputs
   - Assert ValidatedSearchInput.dietary_restrictions is not None for all
   - **Critical: This enforces the Issue #447 fix**

2. **test_contract_all_required_fields_populated**
   - Assert query, dietary_restrictions, min_rating, page, page_size, user_id are never None

3. **test_contract_immutability**
   - Assert ValidatedSearchInput is frozen (dataclass(frozen=True))
   - Attempt to modify field, expect FrozenInstanceError

---

## Performance Requirements

### Targets

- **P50 latency**: <5ms
- **P95 latency**: <15ms
- **P99 latency**: <30ms
- **Throughput**: ≥1000 requests/second (single thread)
- **Memory**: <1KB per validation (no caching, stateless)

### Optimization Notes

- Use set membership for validation (O(1) lookups)
- Pre-compile regex if needed for query sanitization
- Avoid string concatenation in loops
- No I/O operations (pure function)
- No external API calls

### Benchmarking

**tests/performance/test_validation_performance.py**:
```python
def test_validation_performance():
    """Ensure validation meets performance targets"""
    request = SearchRequest(
        query="pasta",
        cuisine="Italian",
        dietary_restrictions=["vegan", "gluten-free"],
        min_rating=4.0
    )
    user = create_sample_user()
    
    durations = []
    for _ in range(1000):
        start = time.perf_counter()
        validate_search_request(request, user)
        durations.append((time.perf_counter() - start) * 1000)
    
    p50 = percentile(durations, 50)
    p95 = percentile(durations, 95)
    
    assert p50 < 5.0, f"P50 {p50}ms exceeds 5ms target"
    assert p95 < 15.0, f"P95 {p95}ms exceeds 15ms target"
```

---

## Logging & Observability

### Logging Events

```python
import logging
logger = logging.getLogger(__name__)

# Success (DEBUG level)
logger.debug(f"Validated search request for user {user.id}", extra={
    "user_id": user.id,
    "query": validated.query,
    "filters_count": len(validated.dietary_restrictions),
    "duration_ms": duration
})

# Validation failure (WARNING level)
logger.warning(f"Validation failed for user {user.id}", extra={
    "user_id": user.id,
    "field": validation_error.field,
    "value": validation_error.value,
    "error": validation_error.message
})

# Performance warning (WARNING level)
if duration_ms > 15:
    logger.warning(f"Slow validation: {duration_ms}ms", extra={
        "user_id": user.id,
        "duration_ms": duration_ms
    })
```

### Metrics to Track

1. **validation_success_total** (counter): Successful validations
2. **validation_error_total** (counter, by field): Failed validations per field
3. **validation_duration_seconds** (histogram): Validation latency distribution
4. **issue_447_fix_triggered_total** (counter): How many times dietary_restrictions was None

---

## Dependencies

### Internal
- `models.User`: For user.id extraction
- `search.types.SearchRequest`: Input type
- `search.types.ValidatedSearchInput`: Output type

### External
- `dataclasses`: For dataclass types
- `typing`: For type hints
- `logging`: For observability

**No Database or External API Calls**: This module is pure computation.

---

## Backward Compatibility

**Public API Unchanged**:
- Legacy `search_recipes(request, user)` signature preserved
- New validation only used when feature flag enabled
- Automatic fallback to legacy validation on errors
- Zero breaking changes for API consumers

**Migration Path**:
1. Introduce validation_module alongside legacy validation
2. Enable feature flag for subset of traffic
3. Monitor error rates and performance
4. Gradually increase traffic percentage
5. Remove legacy validation once 100% rollout successful

---

## Acceptance Criteria

**From Spec.md**:

✅ **SC-001**: Crash rate for None dietary_restrictions → 0 (Issue #447 fixed)  
✅ **SC-002**: All inputs validated within 5ms P50  
✅ **SC-003**: Invalid inputs rejected with 400 Bad Request (not 500)  
✅ **SC-006**: Unit test coverage ≥80% for validation_module  
✅ **SC-013**: Feature flag rollout with automatic fallback  

**Additional Criteria**:
- ValidationError raised for all truly invalid inputs
- All None-able fields normalized to safe defaults
- dietary_restrictions NEVER None in ValidatedSearchInput
- mypy --strict passes with zero errors
- Performance benchmarks pass (P50 <5ms, P95 <15ms)
