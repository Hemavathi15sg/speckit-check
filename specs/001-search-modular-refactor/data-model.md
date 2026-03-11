# Data Model: Module Interface Contracts

**Feature**: Search Module Refactoring  
**Date**: 2026-03-11  
**Purpose**: Define dataclass contracts for interfaces between modules

---

## Overview

This document defines the 5 core dataclasses that represent data flowing between modules in the refactored search pipeline. All classes use `@dataclass(frozen=True)` for immutability and type safety.

**Data Flow**:
```
SearchRequest
     ↓
[validation_module]
     ↓
ValidatedSearchInput
     ↓
[filtering_module]
     ↓
FilteredRecipes
     ↓
[aggregation_module]
     ↓
RankedResults
     ↓
[formatting_module]
     ↓
SearchResponse
```

---

## SearchRequest

**Purpose**: Raw, untrusted input from API layer

**Source**: API request handler  
**Consumer**: validation_module.py  
**Status**: Untrusted (must be validated)

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass(frozen=True)
class SearchRequest:
    """
    Raw search request from API layer.
    
    All fields are Optional because API may send incomplete data.
    validation_module is responsible for normalizing and validating.
    """
    query: Optional[str] = None
    cuisine: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None  # Can be None! (Issue #447)
    prep_time_max: Optional[int] = None
    difficulty: Optional[str] = None
    min_rating: Optional[float] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 50
```

**Validation Rules** (enforced by validation_module):
- `query`: Can be None (default ""), max 500 characters, trimmed
- `cuisine`: Must be valid cuisine type or None
- `dietary_restrictions`: **Can be None** (normalize to []), each value in allowed set
- `prep_time_max`: Must be positive integer or None
- `difficulty`: Must be one of: "easy", "medium", "hard", or None
- `min_rating`: Must be 0.0-5.0 (default 0.0)
- `page`: Must be ≥1 (default 1)
- `page_size`: Must be 1-200 (default 50)

---

## ValidatedSearchInput

**Purpose**: Validated, normalized, trusted search parameters

**Source**: validation_module.py  
**Consumer**: filtering_module.py  
**Status**: Trusted (all validation complete)

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass(frozen=True)
class ValidatedSearchInput:
    """
    Validated and normalized search parameters.
    
    All Optional fields from SearchRequest have been validated.
    dietary_restrictions is NEVER None (Issue #447 fix).
    """
    query: str  # Never None, max 500 chars, trimmed, lowercased
    cuisine: Optional[str]  # Validated or None
    dietary_restrictions: List[str]  # NEVER None, always list (may be empty)
    prep_time_max: Optional[int]  # Positive int or None
    difficulty: Optional[str]  # One of: easy/medium/hard or None
    min_rating: float  # 0.0-5.0, never None (default 0.0)
    page: int  # ≥1, never None
    page_size: int  # 1-200, never None
    user_id: str  # For caching and logging
```

**Guarantees** (enforced by validation_module):
- `query`: Always string (empty string if None), max 500 chars, safe for DB query
- `dietary_restrictions`: **Always list** (never None), **This fixes Issue #447**
- `page`: Always ≥1
- `page_size`: Always 1-200
- `min_rating`: Always 0.0-5.0
- `user_id`: Always populated (for cache keying)

**Type Safety Benefits**:
- filtering_module can safely iterate over `dietary_restrictions` (never None)
- No need for None checks in downstream modules
- mypy enforces these guarantees at compile time

---

## FilteredRecipes

**Purpose**: Recipes after all filters applied

**Source**: filtering_module.py  
**Consumer**: aggregation_module.py  
**Status**: Filtered but not ranked

```python
from dataclasses import dataclass
from typing import List, Dict, Any
from models import Recipe

@dataclass(frozen=True)
class FilteredRecipes:
    """
    Recipes that match all filter criteria.
    
    Includes metadata about which filters were applied and performance metrics.
    """
    recipes: List[Recipe]  # Recipes matching all filters (may be empty)
    applied_filters: Dict[str, Any]  # Which filters were applied
    filter_duration_ms: float  # Performance metric for filtering
    total_before_filters: int  # Total recipes before filtering (for metrics)
```

**Field Details**:

- **recipes**: List of Recipe objects after all filters applied
  - May be empty if no recipes match
  - Order is arbitrary (ranking happens in aggregation_module)
  - Each Recipe has: id, name, ingredients, dietary_tags, cuisine, prep_time_minutes, difficulty, avg_rating

- **applied_filters**: Dict showing which filters were actually applied
  - Example: `{"query": "pasta", "cuisine": "Italian", "dietary": ["vegan"]}`
  - Useful for debugging and logging
  - Excludes filters that were None (not applied)

- **filter_duration_ms**: Time taken to apply all filters
  - Used for performance monitoring
  - Target: <20ms for typical operations

- **total_before_filters**: Count before any filters applied
  - Used to calculate filter effectiveness
  - Example: "10 recipes matched query, 3 after cuisine filter, 1 after dietary filter"

**Usage by aggregation_module**:
- Takes `recipes` list and applies ranking algorithm
- Uses `applied_filters` for cache key generation
- Uses `filter_duration_ms` for total duration calculation

---

## RankedResults

**Purpose**: Recipes ranked, cached, and paginated

**Source**: aggregation_module.py  
**Consumer**: formatting_module.py  
**Status**: Ready for response formatting

```python
from dataclasses import dataclass
from typing import List
from models import Recipe

@dataclass(frozen=True)
class RankedResults:
    """
    Recipes ranked by relevance, with caching and pagination applied.
    
    This is the final data processing step before formatting.
    """
    recipes: List[Recipe]  # Ranked recipes for current page only
    total_count: int  # Total recipes before pagination
    page: int  # Current page number
    page_size: int  # Recipes per page
    cache_hit: bool  # Whether result was served from cache
    ranking_duration_ms: float  # Time for ranking (0 if cache hit)
    total_duration_ms: float  # Total time (validation + filtering + ranking)
```

**Field Details**:

- **recipes**: Ranked recipes for the requested page only
  - Sorted by relevance score (hybrid_v3 algorithm)
  - Length ≤ page_size
  - May be empty if no results or beyond last page

- **total_count**: Total matching recipes before pagination
  - Used to calculate total_pages
  - Example: 47 total recipes, page_size 50 = 1 page

- **page, page_size**: Pagination parameters
  - Copied from ValidatedSearchInput for convenience
  - Used by formatting_module to build response metadata

- **cache_hit**: Boolean indicating cache hit
  - true: Result served from cache (fast path)
  - false: Result computed fresh (slow path)
  - Target cache hit rate: ≥60%

- **ranking_duration_ms**: Time spent ranking
  - 0.0 if cache hit (no ranking needed)
  - Typically <10ms for ranking 100 recipes
  - Includes pagination slicing time

- **total_duration_ms**: End-to-end processing time
  - Includes validation + filtering + ranking
  - Target: <100ms P50, <200ms P95
  - Used for performance monitoring

**Cache Implementation Details** (aggregation_module):
- LRU cache with 1000-entry max
- Cache key: hash(user_id + query + all filters)
- TTL: 300 seconds (5 minutes)
- Memory bound: ≤50MB total

---

## SearchResponse

**Purpose**: Final JSON response structure returned to API

**Source**: formatting_module.py  
**Consumer**: API layer (returned to client)  
**Status**: Final output, ready for JSON serialization

```python
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass(frozen=True)
class SearchResponse:
    """
    Final search response structure.
    
    This matches the existing API contract for backward compatibility.
    Can be serialized directly to JSON.
    """
    recipes: List[Dict[str, Any]]  # Formatted recipe objects (JSON-ready)
    total: int  # Total matching recipes
    page: int  # Current page number
    page_size: int  # Recipes per page
    total_pages: int  # Total pages available
    cache_hit: bool  # Cache indicator (for debugging)
    duration_ms: float  # Total request duration
```

**Field Details**:

- **recipes**: List of recipe dicts ready for JSON serialization
  - Each dict contains: id, name, ingredients, dietary_tags, cuisine, prep_time_minutes, difficulty, avg_rating
  - UUIDs converted to strings
  - All values JSON-serializable
  - Empty list if no results

- **total**: Total matching recipes (before pagination)
  - Used by frontend for "Showing X of Y results"
  - 0 if no matches

- **page**: Current page number (1-indexed)
  - Matches request.page

- **page_size**: Recipes per page
  - Matches request.page_size

- **total_pages**: Calculated total pages
  - Formula: `ceil(total / page_size)`
  - 0 if total is 0
  - Used for pagination controls

- **cache_hit**: Boolean for debugging
  - Indicates if result was cached
  - Can be logged/monitored
  - Not critical for frontend

- **duration_ms**: Total request time in milliseconds
  - Measured from start of validation to end of formatting
  - Includes all module processing
  - Used for performance monitoring

**Backward Compatibility**:
This structure matches the existing search.py response format exactly,
ensuring zero breaking changes for API consumers.

---

## Entity Relationships

```
API Layer
    ↓
    ↓ (SearchRequest)
    ↓
validation_module.py
    ↓
    ↓ (ValidatedSearchInput) ← dietary_restrictions NEVER None
    ↓
filtering_module.py
    ↓
    ↓ (FilteredRecipes)
    ↓
aggregation_module.py ← LRU cache, ranking algorithm
    ↓
    ↓ (RankedResults)
    ↓
formatting_module.py
    ↓
    ↓ (SearchResponse)
    ↓
API Layer (Return to Client)
```

---

## Type Safety Enforcement

**mypy Configuration** (pyproject.toml):
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = false  # Allow List, Dict without full generics
```

**CI/CD Gate**:
```bash
mypy search/ --strict  # Must pass with zero errors
```

**Benefits**:
- Compile-time verification of interface contracts
- IDE autocomplete for all fields
- Catches None handling bugs (Issue #447 type) before runtime
- Refactoring safety (changing a contract breaks dependent code immediately)

---

## Testing Strategy

**Contract Tests** (tests/contract/test_module_contracts.py):
```python
def test_validated_input_never_has_none_dietary_restrictions():
    """Issue #447: ValidatedSearchInput.dietary_restrictions must never be None"""
    # Test all validation paths that could produce ValidatedSearchInput
    test_cases = [
        (SearchRequest(query="pasta", dietary_restrictions=None), []),
        (SearchRequest(query="pasta", dietary_restrictions=[]), []),
        (SearchRequest(query="pasta", dietary_restrictions=["vegan"]), ["vegan"]),
    ]
    
    for request, expected in test_cases:
        validated = validate_search_request(request, sample_user)
        assert validated.dietary_restrictions is not None
        assert validated.dietary_restrictions == expected

def test_all_contracts_are_frozen():
    """All dataclasses must be immutable (frozen=True)"""
    contracts = [
        SearchRequest, ValidatedSearchInput, FilteredRecipes,
        RankedResults, SearchResponse
    ]
    
    for contract in contracts:
        instance = create_sample_instance(contract)
        with pytest.raises(FrozenInstanceError):
            instance.some_field = "modified"  # Should fail
```

---

## Migration Notes

**Phase 1**: Introduce dataclasses alongside legacy code
- Legacy search.py continues using dicts
- New modules use dataclasses
- Adapter layer converts between formats

**Phase 2**: Gradual rollout with feature flags
- validation_module returns ValidatedSearchInput
- If flag disabled, convert to legacy dict format
- If flag enabled, pass ValidatedSearchInput to filtering_module

**Phase 3**: Full migration
- All modules use dataclasses
- Legacy search.py deprecated
- Remove adapter layer

**Zero Breaking Changes**:
- Public API `search_recipes(request, user)` signature unchanged
- Response format identical to legacy (SearchResponse converts to dict)
- API consumers require no code changes

---

## Appendix: Complete Type Definitions

**File**: `search/types.py` (implementation file)
```python
"""Type definitions for search module interfaces."""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from models import Recipe

@dataclass(frozen=True)
class SearchRequest:
    query: Optional[str] = None
    cuisine: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None
    prep_time_max: Optional[int] = None
    difficulty: Optional[str] = None
    min_rating: Optional[float] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 50

@dataclass(frozen=True)
class ValidatedSearchInput:
    query: str
    cuisine: Optional[str]
    dietary_restrictions: List[str]  # NEVER None
    prep_time_max: Optional[int]
    difficulty: Optional[str]
    min_rating: float
    page: int
    page_size: int
    user_id: str

@dataclass(frozen=True)
class FilteredRecipes:
    recipes: List[Recipe]
    applied_filters: Dict[str, Any]
    filter_duration_ms: float
    total_before_filters: int

@dataclass(frozen=True)
class RankedResults:
    recipes: List[Recipe]
    total_count: int
    page: int
    page_size: int
    cache_hit: bool
    ranking_duration_ms: float
    total_duration_ms: float

@dataclass(frozen=True)
class SearchResponse:
    recipes: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    cache_hit: bool
    duration_ms: float
```

**Next Steps**:
1. Create `search/types.py` with these definitions
2. Import in each module: `from search.types import ValidatedSearchInput, ...`
3. Enforce with mypy: `mypy search/ --strict`
4. Write contract tests to verify immutability and type guarantees
