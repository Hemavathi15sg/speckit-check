# Quickstart Guide: Search Module Refactoring

**Feature**: Search Module Refactoring  
**Audience**: Developers implementing or maintaining the refactored search modules  
**Last Updated**: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [Module Architecture](#module-architecture)
3. [Getting Started](#getting-started)
4. [Import Patterns](#import-patterns)
5. [Testing Guide](#testing-guide)
6. [Feature Flags](#feature-flags)
7. [Debugging](#debugging)
8. [Common Patterns](#common-patterns)
9. [Performance Guidelines](#performance-guidelines)
10. [Contributing](#contributing)

---

## Overview

### What is This?

The search module refactoring breaks the monolithic 1006-line `search.py` into 4 focused modules:

1. **validation_module.py** (250 lines): Input validation and normalization
2. **filtering_module.py** (280 lines): Apply search filters to recipe collection
3. **aggregation_module.py** (295 lines): Ranking, caching, and pagination
4. **formatting_module.py** (180 lines): Convert results to JSON response

**Total**: ~1005 lines (similar to legacy, but organized and testable)

### Why Refactor?

**Problems Solved**:
- ✅ **Issue #447**: TypeError when `dietary_restrictions=None` (affects 30% of users)
- ✅ **Issue #183**: Unbounded cache causing memory leak
- ✅ **74 magic numbers**: Replaced with named constants
- ✅ **0% test coverage**: Now targeting ≥80% per module
- ✅ **No type hints**: Full mypy strict mode compliance

**Benefits**:
- Each module ≤300 lines (easier to understand)
- Independent testing (unit tests per module + contract tests)
- Clear interfaces (dataclass contracts between modules)
- Gradual rollout (feature flags per module)
- Performance improvement (better caching, optimized filtering)

---

## Module Architecture

### Data Flow Diagram

```
API Request (Dict)
     ↓
SearchRequest (dataclass)
     ↓
[ validation_module.py ]
     ↓
ValidatedSearchInput (dataclass) ← dietary_restrictions NEVER None
     ↓
[ filtering_module.py ]
     ↓
FilteredRecipes (dataclass)
     ↓
[ aggregation_module.py ] ← LRU cache, ranking algorithm
     ↓
RankedResults (dataclass)
     ↓
[ formatting_module.py ]
     ↓
SearchResponse (dataclass)
     ↓
API Response (JSON)
```

### Module Responsibilities

| Module | Input | Output | Purpose | LOC |
|--------|-------|--------|---------|-----|
| **validation_module** | SearchRequest | ValidatedSearchInput | Validate & normalize untrusted input | 250 |
| **filtering_module** | ValidatedSearchInput | FilteredRecipes | Apply query & filter criteria | 280 |
| **aggregation_module** | FilteredRecipes | RankedResults | Rank, cache, paginate results | 295 |
| **formatting_module** | RankedResults | SearchResponse | Convert to JSON response | 180 |

### Interface Contracts

All modules communicate via **frozen dataclasses** (immutable):

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from models import Recipe

@dataclass(frozen=True)
class SearchRequest:
    """Raw API input (untrusted)"""
    query: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None  # Can be None!
    # ... other fields

@dataclass(frozen=True)
class ValidatedSearchInput:
    """Validated input (trusted)"""
    query: str  # Never None
    dietary_restrictions: List[str]  # NEVER None (Issue #447 fix)
    # ... other fields

@dataclass(frozen=True)
class FilteredRecipes:
    """Recipes after filtering"""
    recipes: List[Recipe]
    applied_filters: Dict[str, Any]
    filter_duration_ms: float
    total_before_filters: int

@dataclass(frozen=True)
class RankedResults:
    """Recipes ranked and paginated"""
    recipes: List[Recipe]
    total_count: int
    page: int
    page_size: int
    cache_hit: bool
    ranking_duration_ms: float
    total_duration_ms: float

@dataclass(frozen=True)
class SearchResponse:
    """Final JSON response"""
    recipes: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    cache_hit: bool
    duration_ms: float
```

**Why frozen?** Immutability prevents accidental modifications and makes debugging easier.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Dependencies: `pip install -r requirements.txt`
- Test tools: `pytest`, `pytest-cov`, `mypy`, `pylint`

### Installation

1. **Clone repository**:
   ```bash
   git clone <repo-url>
   cd recipe-manager
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify setup**:
   ```bash
   pytest --version  # Should show pytest 7.x
   mypy --version    # Should show mypy 1.x
   ```

### Project Structure

```
recipe-manager/
├── search/                    # New modular implementation
│   ├── __init__.py
│   ├── types.py              # Dataclass definitions
│   ├── validation_module.py  # Input validation
│   ├── filtering_module.py   # Query & filter logic
│   ├── aggregation_module.py # Ranking & caching
│   └── formatting_module.py  # Response formatting
├── tests/
│   ├── unit/                 # Unit tests per module
│   │   ├── test_validation_module.py
│   │   ├── test_filtering_module.py
│   │   ├── test_aggregation_module.py
│   │   └── test_formatting_module.py
│   ├── contract/             # Interface contract tests
│   │   └── test_module_contracts.py
│   ├── integration/          # End-to-end tests
│   │   └── test_full_pipeline.py
│   └── performance/          # Performance benchmarks
│       └── test_performance.py
├── search.py                 # Legacy monolith (for fallback)
├── models.py                 # User, Recipe models
└── api/
    └── routes.py             # API endpoints
```

---

## Import Patterns

### Importing Modules

**Within search package**:
```python
# In search/filtering_module.py
from search.types import ValidatedSearchInput, FilteredRecipes
from search.validation_module import validate_search_request
```

**From outside search package**:
```python
# In api/routes.py
from search.validation_module import validate_search_request
from search.filtering_module import apply_filters
from search.aggregation_module import aggregate_and_rank
from search.formatting_module import format_response
from search.types import SearchRequest, SearchResponse
```

### Importing Types

**All dataclasses in one file**:
```python
# search/types.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from models import Recipe

@dataclass(frozen=True)
class SearchRequest:
    # ... fields

@dataclass(frozen=True)
class ValidatedSearchInput:
    # ... fields

# ... other contracts
```

**Import in modules**:
```python
from search.types import (
    SearchRequest,
    ValidatedSearchInput,
    FilteredRecipes,
    RankedResults,
    SearchResponse
)
```

---

## Testing Guide

### Running Tests

**All tests**:
```bash
pytest
```

**Specific test file**:
```bash
pytest tests/unit/test_validation_module.py
```

**Specific test function**:
```bash
pytest tests/unit/test_validation_module.py::test_none_dietary_restrictions_normalized
```

**With coverage**:
```bash
pytest --cov=search --cov-report=term-missing
```

**Target**: ≥80% coverage per module

### Writing Unit Tests

**Example: Testing validation_module**

```python
# tests/unit/test_validation_module.py
import pytest
from search.validation_module import validate_search_request, ValidationError
from search.types import SearchRequest
from models import User

def test_none_dietary_restrictions_normalized_to_empty_list():
    """Issue #447: Ensure None dietary_restrictions becomes []"""
    # Arrange
    request = SearchRequest(query="pasta", dietary_restrictions=None)
    user = User(id="test-user", name="Test", dietary_restrictions=None)
    
    # Act
    validated = validate_search_request(request, user)
    
    # Assert
    assert validated.dietary_restrictions == []
    assert validated.dietary_restrictions is not None  # NEVER None!

def test_invalid_cuisine_raises_error():
    """Invalid cuisine should raise ValidationError"""
    # Arrange
    request = SearchRequest(query="pasta", cuisine="Martian")
    user = User(id="test-user", name="Test")
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validate_search_request(request, user)
    
    assert "cuisine" in str(exc_info.value)
```

### Writing Contract Tests

**Example: Testing interface guarantees**

```python
# tests/contract/test_module_contracts.py
import pytest
from dataclasses import FrozenInstanceError
from search.validation_module import validate_search_request
from search.types import SearchRequest, ValidatedSearchInput

def test_validated_input_dietary_restrictions_never_none():
    """CRITICAL: dietary_restrictions must NEVER be None (Issue #447)"""
    # Test 100 random inputs to ensure guarantee holds
    for i in range(100):
        request = create_random_search_request()  # May have None dietary_restrictions
        user = create_sample_user()
        
        validated = validate_search_request(request, user)
        
        assert validated.dietary_restrictions is not None, \
            f"dietary_restrictions was None for input {i}"
        assert isinstance(validated.dietary_restrictions, list), \
            f"dietary_restrictions was not list for input {i}"

def test_all_contracts_are_frozen():
    """All dataclasses must be immutable (frozen=True)"""
    contracts = [
        SearchRequest, ValidatedSearchInput, FilteredRecipes,
        RankedResults, SearchResponse
    ]
    
    for contract in contracts:
        instance = create_sample_instance(contract)
        
        with pytest.raises(FrozenInstanceError):
            # Try to modify a field (should raise error)
            instance.__dict__["query"] = "modified"
```

### Writing Integration Tests

**Example: End-to-end pipeline**

```python
# tests/integration/test_full_pipeline.py
from search.validation_module import validate_search_request
from search.filtering_module import apply_filters
from search.aggregation_module import aggregate_and_rank
from search.formatting_module import format_response
from search.types import SearchRequest
from models import SAMPLE_RECIPES

def test_full_search_pipeline():
    """Test complete search flow: validate → filter → aggregate → format"""
    # Arrange
    request = SearchRequest(
        query="pasta",
        cuisine="Italian",
        dietary_restrictions=["vegan"],
        min_rating=4.0,
        page=1,
        page_size=50
    )
    user = create_sample_user()
    
    # Act
    validated = validate_search_request(request, user)
    filtered = apply_filters(validated, SAMPLE_RECIPES)
    ranked = aggregate_and_rank(filtered, validated)
    response = format_response(ranked, validated)
    
    # Assert
    assert isinstance(response, SearchResponse)
    assert response.total >= 0
    assert len(response.recipes) <= response.page_size
    assert response.total_pages >= 0
    assert response.duration_ms > 0
```

### Type Checking

**Run mypy**:
```bash
mypy search/ --strict
```

**Expected output**: `Success: no issues found`

**Common mypy errors**:
- `error: Argument has incompatible type` → Check dataclass field types
- `error: Function is missing a return type annotation` → Add `-> ReturnType`
- `error: Incompatible return value type` → Return type doesn't match annotation

---

## Feature Flags

### Flag Configuration

**Environment Variables** (set in `.env` or deployment config):
```bash
USE_NEW_VALIDATION=true    # Week 1 rollout
USE_NEW_FILTERING=true     # Week 2 rollout
USE_NEW_AGGREGATION=true   # Week 3 rollout
USE_NEW_FORMATTING=true    # Week 4 rollout
```

**Local Development** (.env.local):
```bash
# Enable all new modules
USE_NEW_VALIDATION=true
USE_NEW_FILTERING=true
USE_NEW_AGGREGATION=true
USE_NEW_FORMATTING=true
```

### Using Feature Flags

**In search entry point**:

```python
import os
from search.validation_module import validate_search_request
from search.filtering_module import apply_filters
# ... other imports

def search_recipes(request: SearchRequest, user: User) -> SearchResponse:
    """
    Main search entry point with gradual rollout support.
    
    Feature flags control which modules are enabled.
    Automatic fallback to legacy on errors.
    """
    # Validation (Week 1)
    if os.getenv("USE_NEW_VALIDATION") == "true":
        try:
            validated = validate_search_request(request, user)
        except Exception as e:
            logger.error(f"New validation failed: {e}")
            return _legacy_search(request, user)  # Fallback
    else:
        validated = _legacy_validate(request, user)
    
    # Filtering (Week 2)
    if os.getenv("USE_NEW_FILTERING") == "true":
        try:
            filtered = apply_filters(validated, SAMPLE_RECIPES)
        except Exception as e:
            logger.error(f"New filtering failed: {e}")
            return _legacy_search(request, user)  # Fallback
    else:
        filtered = _legacy_filter(validated)
    
    # ... similar for aggregation and formatting
```

### Testing with Feature Flags

**Test with flags enabled**:
```python
import os

def test_with_new_validation_enabled():
    os.environ["USE_NEW_VALIDATION"] = "true"
    
    response = search_recipes(request, user)
    
    assert response.total >= 0  # Verify behavior with new module

def test_with_new_validation_disabled():
    os.environ["USE_NEW_VALIDATION"] = "false"
    
    response = search_recipes(request, user)
    
    assert response.total >= 0  # Verify legacy behavior unchanged
```

---

## Debugging

### Logging

**Enable debug logging**:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("search")
```

**Log statements in modules**:
```python
# In validation_module.py
logger.debug(f"Validating request for user {user.id}", extra={
    "user_id": user.id,
    "query": request.query,
    "filters_count": len(request.dietary_restrictions or [])
})
```

**View logs**:
```bash
pytest --log-cli-level=DEBUG  # Show logs during tests
```

### Debugging Tests

**Use pytest debugger**:
```python
def test_something():
    request = SearchRequest(query="pasta")
    
    import pdb; pdb.set_trace()  # Breakpoint
    
    validated = validate_search_request(request, user)
```

**Run with debugger**:
```bash
pytest --pdb  # Drop into debugger on failures
```

### Common Issues

**Issue #447: TypeError on None dietary_restrictions**

**Symptom**:
```python
TypeError: 'NoneType' object is not iterable
```

**Root Cause**: Legacy code iterates over `user.dietary_restrictions` without None check.

**Fix**: validation_module normalizes None to `[]`:
```python
dietary_restrictions = request.dietary_restrictions or []
```

**Verify Fix**:
```python
def test_issue_447_prevented():
    request = SearchRequest(dietary_restrictions=None)
    validated = validate_search_request(request, user)
    assert validated.dietary_restrictions == []  # NEVER None
```

**Issue #183: Cache memory leak**

**Symptom**: Memory usage grows unbounded over time.

**Root Cause**: Legacy cache has no max size or TTL.

**Fix**: aggregation_module uses LRU cache with max_size=1000, TTL=300s:
```python
@lru_cache(maxsize=1000)
def _cached_rank(...):
    ...
```

**Verify Fix**:
```python
def test_issue_183_cache_bounded():
    # Insert 10,000 entries
    for i in range(10000):
        aggregate_and_rank(...)
    
    # Cache should only have 1000 entries (LRU evicted rest)
    assert len(cache) <= 1000
```

---

## Common Patterns

### Pattern 1: Adding a New Filter

**Goal**: Add a new filter (e.g., "max_calories")

**Steps**:

1. **Update SearchRequest** (search/types.py):
   ```python
   @dataclass(frozen=True)
   class SearchRequest:
       # ... existing fields
       max_calories: Optional[int] = None  # NEW
   ```

2. **Update ValidatedSearchInput** (search/types.py):
   ```python
   @dataclass(frozen=True)
   class ValidatedSearchInput:
       # ... existing fields
       max_calories: Optional[int]  # NEW (validated)
   ```

3. **Add validation** (search/validation_module.py):
   ```python
   def validate_search_request(...) -> ValidatedSearchInput:
       # ... existing validation
       
       # Validate max_calories
       max_calories = request.max_calories
       if max_calories is not None and max_calories <= 0:
           raise ValidationError("max_calories", max_calories, "Must be positive")
       
       return ValidatedSearchInput(
           # ... existing fields
           max_calories=max_calories  # NEW
       )
   ```

4. **Add filter** (search/filtering_module.py):
   ```python
   def apply_filters(...) -> FilteredRecipes:
       # ... existing filters
       
       # Apply max_calories filter
       if validated_input.max_calories is not None:
           recipes = [r for r in recipes if r.calories <= validated_input.max_calories]
       
       # ... rest of function
   ```

5. **Write tests**:
   ```python
   def test_max_calories_filter():
       validated = ValidatedSearchInput(max_calories=500, ...)
       filtered = apply_filters(validated, SAMPLE_RECIPES)
       
       for recipe in filtered.recipes:
           assert recipe.calories <= 500
   ```

### Pattern 2: Modifying Ranking Algorithm

**Goal**: Change ranking weights or add new factor

**Steps**:

1. **Update ranking function** (search/aggregation_module.py):
   ```python
   def _calculate_relevance_score(recipe: Recipe, query: str) -> float:
       text_relevance = ...  # Existing
       quality_score = ...   # Existing
       popularity_score = ... # Existing
       freshness_score = ... # NEW
       
       # Update weights
       return (
           (text_relevance * 0.3) +      # Reduced from 0.4
           (quality_score * 0.3) +
           (popularity_score * 0.2) +    # Reduced from 0.3
           (freshness_score * 0.2)       # NEW
       )
   ```

2. **Write tests**:
   ```python
   def test_freshness_affects_ranking():
       old_recipe = Recipe(..., created_days_ago=365)
       new_recipe = Recipe(..., created_days_ago=1)
       
       old_score = _calculate_relevance_score(old_recipe, "pasta")
       new_score = _calculate_relevance_score(new_recipe, "pasta")
       
       assert new_score > old_score  # Newer should rank higher
   ```

### Pattern 3: Adding Performance Metrics

**Goal**: Track new performance metric

**Steps**:

1. **Add metric to contract** (search/types.py):
   ```python
   @dataclass(frozen=True)
   class FilteredRecipes:
       # ... existing fields
       cache_check_duration_ms: float = 0.0  # NEW
   ```

2. **Measure in module** (search/filtering_module.py):
   ```python
   import time
   
   def apply_filters(...) -> FilteredRecipes:
       start = time.perf_counter()
       
       # ... filtering logic
       
       duration_ms = (time.perf_counter() - start) * 1000
       
       return FilteredRecipes(
           # ... existing fields
           filter_duration_ms=duration_ms
       )
   ```

3. **Log metric**:
   ```python
   logger.info(f"Filtering took {duration_ms:.2f}ms", extra={
       "duration_ms": duration_ms
   })
   ```

---

## Performance Guidelines

### Performance Targets

| Module | P50 | P95 | Throughput |
|--------|-----|-----|------------|
| validation_module | <5ms | <15ms | 1000 req/s |
| filtering_module | <20ms | <50ms | 500 req/s |
| aggregation_module (cache hit) | <5ms | <10ms | 2000 req/s |
| aggregation_module (cache miss) | <30ms | <60ms | 500 req/s |
| formatting_module | <5ms | <10ms | 10000 req/s |

### Optimization Tips

1. **Use list comprehensions** (faster than loops):
   ```python
   # Good
   results = [r for r in recipes if r.rating >= 4.0]
   
   # Bad
   results = []
   for r in recipes:
       if r.rating >= 4.0:
           results.append(r)
   ```

2. **Use set operations** for membership checks:
   ```python
   # Good (O(1) lookup)
   valid_cuisines = {"Italian", "Chinese", "Mexican"}
   if cuisine in valid_cuisines:
       ...
   
   # Bad (O(n) lookup)
   valid_cuisines = ["Italian", "Chinese", "Mexican"]
   if cuisine in valid_cuisines:
       ...
   ```

3. **Short-circuit evaluations**:
   ```python
   # Good (stop filtering if no results)
   recipes = filter_by_query(recipes, query)
   if not recipes:
       return FilteredRecipes(recipes=[], ...)
   
   recipes = filter_by_cuisine(recipes, cuisine)
   if not recipes:
       return FilteredRecipes(recipes=[], ...)
   ```

4. **Avoid deep copying**:
   ```python
   # Good (filter by reference, recipes are immutable)
   filtered = [r for r in recipes if condition(r)]
   
   # Bad (unnecessary copying)
   import copy
   filtered = [copy.deepcopy(r) for r in recipes if condition(r)]
   ```

5. **Cache expensive computations**:
   ```python
   @lru_cache(maxsize=1000)
   def expensive_computation(arg):
       # ... complex logic
       return result
   ```

### Performance Testing

**Benchmark template**:
```python
import time
from statistics import median, quantiles

def test_module_performance():
    durations = []
    
    for _ in range(1000):
        start = time.perf_counter()
        result = module_function(input_data)
        duration_ms = (time.perf_counter() - start) * 1000
        durations.append(duration_ms)
    
    p50 = median(durations)
    p95 = quantiles(durations, n=20)[18]  # 95th percentile
    
    print(f"P50: {p50:.2f}ms, P95: {p95:.2f}ms")
    
    assert p50 < TARGET_P50, f"P50 {p50}ms exceeds target"
    assert p95 < TARGET_P95, f"P95 {p95}ms exceeds target"
```

---

## Contributing

### Code Style

**Follow PEP 8** (enforced by pylint):
```bash
pylint search/
```

**Target score**: ≥9.0/10

**Common style guidelines**:
- Max line length: 100 characters
- Use 4 spaces for indentation
- Use snake_case for functions and variables
- Use PascalCase for classes
- Add docstrings to all public functions

**Docstring format**:
```python
def validate_search_request(request: SearchRequest, user: User) -> ValidatedSearchInput:
    """
    Validate and normalize raw search request.
    
    Args:
        request: Untrusted input from API layer
        user: Authenticated user object
    
    Returns:
        ValidatedSearchInput with all fields validated
    
    Raises:
        ValidationError: If any input is invalid
    """
```

### Pull Request Process

1. **Create feature branch**:
   ```bash
   git checkout -b feature/add-calories-filter
   ```

2. **Make changes** (follow patterns above)

3. **Run tests**:
   ```bash
   pytest --cov=search --cov-report=term-missing
   mypy search/ --strict
   pylint search/
   ```

4. **Ensure coverage ≥80%**:
   ```bash
   pytest --cov=search --cov-report=html
   open htmlcov/index.html  # View coverage report
   ```

5. **Commit with descriptive message**:
   ```bash
   git commit -m "Add max_calories filter to filtering_module

   - Add max_calories field to SearchRequest and ValidatedSearchInput
   - Add validation for max_calories (must be positive)
   - Add filter to filtering_module
   - Add unit tests (coverage 85%)
   - Update contracts documentation"
   ```

6. **Push and create PR**:
   ```bash
   git push origin feature/add-calories-filter
   ```

7. **Ensure CI passes**:
   - All tests pass
   - Coverage ≥80%
   - mypy --strict passes
   - pylint score ≥9.0/10

---

## Additional Resources

### Documentation

- **Spec**: `specs/001-search-modular-refactor/spec.md`
- **Plan**: `specs/001-search-modular-refactor/plan.md`
- **Contracts**: `specs/001-search-modular-refactor/contracts/`
- **Data Model**: `specs/001-search-modular-refactor/data-model.md`

### Related Files

- **Legacy search**: `search.py` (for comparison)
- **Models**: `models.py` (User, Recipe)
- **API routes**: `api/routes.py` (integration points)

### Useful Commands

```bash
# Run specific test file
pytest tests/unit/test_validation_module.py

# Run tests matching pattern
pytest -k "test_dietary"

# Run tests with output
pytest -v -s

# Run tests and drop into debugger on failure
pytest --pdb

# Generate coverage report
pytest --cov=search --cov-report=html

# Type check
mypy search/ --strict

# Lint code
pylint search/

# Format code (if using black)
black search/
```

---

## Questions or Issues?

- **Documentation unclear?** Create an issue with label `docs`
- **Bug found?** Create an issue with label `bug`
- **Feature request?** Create an issue with label `enhancement`
- **Need help?** Ask in team chat or create discussion

**Remember**: Always check existing issues and documentation first!
