# Phase 0 Research: Module Extraction Strategy

**Feature**: Search Module Refactoring  
**Date**: 2026-03-11  
**Purpose**: Research and finalize decisions on module extraction sequence, interface design, testing strategy, and rollout approach

---

## Research Topic 1: Module Extraction Sequence Strategy

### Question
In what order should modules be extracted from the monolith to minimize risk and enable incremental value delivery?

### Analysis

**Current State**: search.py (1006 lines) contains:
- Input validation (scattered, incomplete)
- Filter logic (5+ functions, some deprecated)
- Ranking algorithms (multiple versions)
- Caching logic (broken LRU implementation)
- Response formatting (JSON + half-implemented XML)

**Dependency Analysis** (from existing code):
```
API Request → Parse/Validate → Filter → Rank/Cache → Format → Response
```

**Extraction Order Evaluation**:

**Option A: Bottom-up (formatting → aggregation → filtering → validation)**
- ✅ Lowest risk (leaf nodes first)
- ❌ Doesn't fix critical bug early
- ❌ Low early value delivery

**Option B: Top-down (validation → filtering → aggregation → formatting)**
- ✅ Fixes Issue #447 immediately (validation module first)
- ✅ Natural data flow order
- ✅ Each module delivers incremental value
- ❌ Higher risk (core logic extracted early)

**Option C: Critical-first (validation → aggregation → filtering → formatting)**
- ✅ Fixes both critical issues (crash + cache leak) early
- ❌ Unnatural extraction order
- ❌ Aggregation depends on filtering output

### Decision: **Option B - Top-Down (validation → filtering → aggregation → formatting)**

**Rationale**:
1. **Immediate Value**: Validation module fixes Issue #447 (30% of users affected) in Phase 1.1
2. **Natural Flow**: Matches actual data flow through search pipeline
3. **Independent Testing**: Each module can be tested with mocked dependencies
4. **Risk Mitigation**: Feature flags allow gradual rollout, automatic fallback on errors

**Validated Sequence**:

**Phase 1.1: validation_module.py** (Week 1)
- **Lines**: ~250
- **Purpose**: Validate and normalize inputs, fix None dietary_restrictions crash
- **Dependencies**: None (only uses models.User)
- **Value**: Eliminates TypeError for 30% of users
- **Rollout**: 10% traffic, monitor crash rate

**Phase 1.2: filtering_module.py** (Week 2)
- **Lines**: ~280
- **Purpose**: Apply all filters in optimal order, remove deprecated code
- **Dependencies**: Validated input from validation_module
- **Value**: Clean filter logic, remove 3 deprecated functions
- **Rollout**: 25% traffic (requires Phase 1.1 deployed)

**Phase 1.3: aggregation_module.py** (Week 3)
- **Lines**: ~295
- **Purpose**: Rank recipes, fix cache memory leak, implement LRU properly
- **Dependencies**: Filtered recipes from filtering_module
- **Value**: Performance improvement, cache fix (Issue #183)
- **Rollout**: 50% traffic (requires Phases 1.1 and 1.2 deployed)

**Phase 1.4: formatting_module.py** (Week 4)
- **Lines**: ~180
- **Purpose**: Format response, remove legacy XML support
- **Dependencies**: Ranked results from aggregation_module
- **Value**: Complete migration, clean response formatting
- **Rollout**: 100% traffic (all modules deployed)

---

## Research Topic 2: Interface Design Patterns

### Question
What Python patterns best represent interfaces between modules while maintaining type safety and testability?

### Options Evaluated

**Option A: Python Dataclasses**
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class ValidatedSearchInput:
    query: str
    dietary_restrictions: List[str]  # Never None
    page: int
```

**Pros**:
- ✅ Native Python 3.11 (no dependencies)
- ✅ Immutable with `frozen=True`
- ✅ Excellent mypy support
- ✅ IDE autocomplete works perfectly
- ✅ Clean repr() and eq() implementations

**Cons**:
- ❌ Slightly more verbose than dicts
- ❌ Must be imported explicitly

**Option B: TypedDict**
```python
from typing import TypedDict, List

class ValidatedSearchInput(TypedDict):
    query: str
    dietary_restrictions: List[str]
    page: int
```

**Pros**:
- ✅ Dict-compatible (easy serialization)
- ✅ Lightweight

**Cons**:
- ❌ Mutable (can be accidentally modified)
- ❌ Weaker type checking than dataclasses
- ❌ No guaranteed structure at runtime

**Option C: Protocol (Structural Subtyping)**
```python
from typing import Protocol, List

class ValidatedSearchInput(Protocol):
    query: str
    dietary_restrictions: List[str]
    page: int
```

**Pros**:
- ✅ Very flexible (structural typing)

**Cons**:
- ❌ Complex for simple DTOs
- ❌ No runtime validation
- ❌ Overkill for this use case

### Decision: **Dataclasses with frozen=True**

**Rationale**:
1. **Immutability**: `frozen=True` prevents accidental mutations between modules
2. **Type Safety**: Strong mypy checking catches errors at development time
3. **Python 3.11 Native**: No additional dependencies required
4. **Developer Experience**: Excellent IDE support, clear error messages
5. **Clear Semantics**: Explicit structure, easy to understand

**Contracts to Define**:
1. `SearchRequest`: Raw API input (untrusted)
2. `ValidatedSearchInput`: Validated, normalized parameters (trusted)
3. `FilteredRecipes`: Recipes after filters applied
4. `RankedResults`: Ranked, cached, paginated results
5. `SearchResponse`: Final JSON response structure

**Implementation Pattern**:
```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass(frozen=True)
class ValidatedSearchInput:
    """Output from validation_module, input to filtering_module."""
    query: str  # Never None, max 500 chars
    cuisine: Optional[str]
    dietary_restrictions: List[str]  # Never None, normalized to []
    prep_time_max: Optional[int]
    difficulty: Optional[str]
    min_rating: float  # 0.0-5.0
    page: int  # ≥1
    page_size: int  # 1-200
    user_id: str  # For caching
```

---

## Research Topic 3: Testing Strategy Per Module

### Question
How can each module achieve ≥80% coverage with independent, maintainable tests?

### Testing Pyramid for This Project

```
                /\
               /  \
              / E2E\          ← Integration tests (10%)
             /------\
            /Contract\        ← Contract tests (20%)
           /----------\
          /    Unit    \      ← Unit tests (70%)
         /--------------\
```

### Strategy: Three-Tier Testing

**Tier 1: Unit Tests (70% of test effort)**

**Purpose**: Test each module in isolation with ≥80% coverage

**Location**: `tests/unit/test_{module}_module.py`

**Approach**:
- Mock all dependencies (use pytest fixtures)
- Test all code paths (happy path + edge cases)
- Parametrized tests for variations
- Fast execution (<1s per module)

**Example** (validation_module):
```python
import pytest
from search.validation_module import validate_search_request
from models import User

def test_validate_none_dietary_restrictions():
    """Issue #447: None dietary_restrictions should normalize to []"""
    user = User(id=uuid4(), name="Test", email="test@example.com",
                dietary_restrictions=None)  # ← The bug
    request = SearchRequest(query="pasta")
    
    result = validate_search_request(request, user)
    
    assert result.dietary_restrictions == []  # ← Normalized, not None
    assert result.query == "pasta"

@pytest.mark.parametrize("invalid_page", [-1, 0, "invalid"])
def test_validate_invalid_page_fails(invalid_page):
    """Validation should reject invalid page numbers"""
    request = SearchRequest(query="pasta", page=invalid_page)
    user = valid_user_fixture()
    
    with pytest.raises(ValidationError, match="page must be >= 1"):
        validate_search_request(request, user)
```

**Coverage Target**: ≥80% per module (measured with pytest-cov)

**Tier 2: Contract Tests (20% of test effort)**

**Purpose**: Verify interface contracts between modules are honored

**Location**: `tests/contract/test_module_contracts.py`

**Approach**:
- Test that outputs match expected dataclass structure
- Verify type constraints (e.g., dietary_restrictions never None)
- Catch breaking changes early

**Example**:
```python
def test_validation_output_contract():
    """Validation module output must match ValidatedSearchInput contract"""
    result = validate_search_request(sample_request, sample_user)
    
    # Verify contract
    assert isinstance(result, ValidatedSearchInput)
    assert isinstance(result.dietary_restrictions, list)  # Never None
    assert result.page >= 1
    assert 1 <= result.page_size <= 200
    assert 0.0 <= result.min_rating <= 5.0

def test_filtering_to_aggregation_contract():
    """FilteredRecipes must have structure expected by aggregation"""
    filtered = apply_filters(validated_input, recipes)
    
    assert isinstance(filtered, FilteredRecipes)
    assert all(isinstance(r, Recipe) for r in filtered.recipes)
    assert isinstance(filtered.applied_filters, dict)
```

**Tier 3: Integration Tests (10% of test effort)**

**Purpose**: Test full search pipeline end-to-end

**Location**: `tests/integration/test_search_flow.py`

**Approach**:
- Real data flow through all modules
- No mocks (except external dependencies like DB)
- Verify modules work together correctly

**Example**:
```python
def test_full_search_pipeline_with_none_dietary_restrictions():
    """End-to-end: User with None dietary_restrictions gets results"""
    user = User(id=uuid4(), name="Bob", email="bob@example.com",
                dietary_restrictions=None)  # ← Issue #447
    request = SearchRequest(query="pasta", cuisine="Italian")
    
    # Full pipeline: validation → filtering → aggregation → formatting
    response = search_recipes(request, user)  # Public API
    
    assert isinstance(response, SearchResponse)
    assert response.total >= 0
    assert len(response.recipes) <= response.page_size
    # No TypeError! Bug fixed.
```

### Test Fixtures Strategy

**Shared fixtures** (tests/conftest.py):
```python
@pytest.fixture
def sample_recipes():
    """Sample recipe data for testing"""
    return [
        Recipe(id=uuid4(), name="Pasta Carbonara", ...),
        Recipe(id=uuid4(), name="Vegan Buddha Bowl", ...),
        Recipe(id=uuid4(), name="Chicken Curry", ...)
    ]

@pytest.fixture
def user_with_dietary_restrictions():
    return User(id=uuid4(), name="Alice", email="alice@example.com",
                dietary_restrictions=["vegan", "gluten-free"])

@pytest.fixture
def user_without_dietary_restrictions():
    """User with None dietary_restrictions (Issue #447 case)"""
    return User(id=uuid4(), name="Bob", email="bob@example.com",
                dietary_restrictions=None)
```

### Decision: Three-Tier Testing with 80/15/5 Split

**Rationale**:
- **Unit tests (80%)**: Fast feedback, high coverage, test all edge cases
- **Contract tests (15%)**: Catch interface breaking changes
- **Integration tests (5%)**: Validate full pipeline works

**Tools**:
- pytest: Test runner
- pytest-cov: Coverage reporting
- pytest-mock: Mocking utilities
- pytest-parametrize: Edge case testing

---

## Research Topic 4: Gradual Rollout Approach

### Question
How can modules be rolled out incrementally to minimize risk while maintaining ability to rollback?

### Rollout Strategies Evaluated

**Option A: Big Bang (all modules at once)**
- ❌ High risk: All changes deployed simultaneously
- ❌ Hard to identify which module causes issues
- ❌ Difficult rollback (revert entire feature)

**Option B: Per-Module with Feature Flags**
- ✅ Low risk: One module at a time
- ✅ Easy to identify problem modules
- ✅ Simple rollback (flip flag off)
- ✅ Gradual traffic increase per module
- ✅ Automatic fallback on exceptions

**Option C: Blue-Green Deployment**
- ✅ Full infrastructure switch
- ❌ Requires duplicate infrastructure
- ❌ All-or-nothing approach
- ❌ No gradual traffic split

### Decision: **Per-Module Feature Flags with Automatic Fallback**

**Rationale**:
1. **Granular Control**: Enable/disable each module independently
2. **Risk Mitigation**: Fallback to legacy code on any exception
3. **Incremental Validation**: Validate one module at a time
4. **Data-Driven**: Monitor metrics per module, adjust rollout based on data

**Implementation Approach**:

**Feature Flag Configuration** (constants.py):
```python
# Feature flags for gradual rollout
USE_NEW_VALIDATION = os.getenv("USE_NEW_VALIDATION", "false").lower() == "true"
USE_NEW_FILTERING = os.getenv("USE_NEW_FILTERING", "false").lower() == "true"
USE_NEW_AGGREGATION = os.getenv("USE_NEW_AGGREGATION", "false").lower() == "true"
USE_NEW_FORMATTING = os.getenv("USE_NEW_FORMATTING", "false").lower() == "true"

# Rollout percentages (for A/B testing)
VALIDATION_ROLLOUT_PERCENT = int(os.getenv("VALIDATION_ROLLOUT_PERCENT", "0"))
FILTERING_ROLLOUT_PERCENT = int(os.getenv("FILTERING_ROLLOUT_PERCENT", "0"))
# etc.
```

**Automatic Fallback Pattern**:
```python
def search_recipes_with_fallback(request, user):
    """Public API with automatic fallback to legacy code."""
    
    # Phase 1.1: Validation module with fallback
    if USE_NEW_VALIDATION and should_use_new_code(user, VALIDATION_ROLLOUT_PERCENT):
        try:
            validated = validation_module.validate_search_request(request, user)
        except Exception as e:
            logger.error(f"New validation failed: {e}, using legacy")
            validated = legacy_validate(request, user)  # Fallback
    else:
        validated = legacy_validate(request, user)
    
    # Phase 1.2: Filtering module with fallback
    if USE_NEW_FILTERING and USE_NEW_VALIDATION:
        try:
            filtered = filtering_module.apply_filters(validated, recipes)
        except Exception as e:
            logger.error(f"New filtering failed: {e}, using legacy")
            filtered = legacy_filter(validated, recipes)  # Fallback
    else:
        filtered = legacy_filter(validated, recipes)
    
    # ... repeat for aggregation and formatting
```

**Rollout Timeline**:

**Week 1: validation_module**
- Deploy with `USE_NEW_VALIDATION=false` (feature disabled)
- Enable for 10% of traffic: `VALIDATION_ROLLOUT_PERCENT=10`
- Monitor: Crash rate, error logs, latency
- Success criteria: Zero None dietary_restrictions crashes
- If success: Increase to 50% → 100% over 2 days
- If failure: Set `USE_NEW_VALIDATION=false`, investigate

**Week 2: filtering_module**
- Prerequisites: validation_module at 100%
- Deploy with `USE_NEW_FILTERING=false`
- Enable for 25% of traffic
- Monitor: Filter correctness, performance
- Success criteria: Identical results to legacy, latency maintained
- Gradual increase: 25% → 50% → 100%

**Week 3: aggregation_module**
- Prerequisites: validation + filtering at 100%
- Deploy with `USE_NEW_AGGREGATION=false`
- Enable for 50% of traffic
- Monitor: Cache hit rate, memory usage, latency
- Success criteria: Cache hit ≥60%, memory ≤50MB
- Gradual increase: 50% → 100%

**Week 4: formatting_module**
- Prerequisites: All previous modules at 100%
- Deploy with `USE_NEW_FORMATTING=false`
- Enable for 100% of traffic (final module)
- Monitor: Full pipeline metrics
- Success criteria: All SC-001 through SC-016 met

**Week 5+: Cleanup**
- Run at 100% for 2 weeks
- Remove feature flags
- Delete legacy search.py
- Mark migration complete

**Monitoring Dashboards** (per module):
- Error rate (must remain at baseline)
- Latency (P50, P95, P99)
- Throughput (requests/sec)
- Cache hit rate (aggregation module)
- Memory usage (aggregation module)

---

## Summary of Decisions

| Decision Point | Choice | Rationale |
|----------------|--------|-----------|
| **Extraction Sequence** | Top-down (validation → filtering → aggregation → formatting) | Fixes critical bug early, natural data flow, incremental value |
| **Interface Pattern** | Dataclasses (frozen=True) | Immutability, strong typing, native Python 3.11 |
| **Testing Strategy** | Three-tier (Unit 80% + Contract 15% + Integration 5%) | High coverage, fast feedback, catch breaking changes |
| **Rollout Approach** | Per-module feature flags with automatic fallback | Low risk, gradual validation, easy rollback |

---

## Next Actions

1. **Phase 1.1**: Create data-model.md with all dataclass definitions
2. **Phase 1.2**: Create contracts/ with per-module interface specs
3. **Phase 1.3**: Create quickstart.md with developer guide
4. **Phase 1.4**: Update agent context with Python/pytest/mypy tech stack
5. **Phase 2**: Generate tasks.md with `/speckit.tasks`
6. **Phase 3**: Begin implementation (test-first approach)

**Research complete. Proceeding to Phase 1 design artifacts.**
