# Implementation Plan: Search Module Refactoring

**Branch**: `001-search-modular-refactor` | **Date**: 2026-03-11 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-search-modular-refactor/spec.md`

**Note**: This plan implements the 4-module refactoring strategy to fix Issue #447 (30% of users experiencing null dietary restrictions crashes) and eliminate technical debt in the 1006-line search.py monolith.

## Summary

**Primary Requirement**: Refactor search.py (1006 lines) into 4 independently testable modules (each ≤300 lines) to fix critical production bug (Issue #447: null dietary restrictions causing TypeError for 30% of users) while eliminating technical debt (74 magic numbers, deprecated code, memory leaks) and achieving ≥80% test coverage per module.

**Technical Approach** (from Phase 0 research):
- **Module Extraction Sequence**: validation → filtering → aggregation → formatting (minimize disruption, enable incremental rollout)
- **Interface Design**: Explicit Python dataclasses for inter-module contracts, type hints enforced via mypy strict mode
- **Testing Strategy**: Test-first approach with independent test suites per module, contract tests for interfaces, integration tests for full flow
- **Rollout Approach**: Gradual per-module deployment with feature flags, original search.py remains as fallback during migration

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pytest (testing), mypy (type checking), pylint (linting), dataclasses (interface contracts)  
**Storage**: PostgreSQL via existing connection pattern (no changes to schema or connection management)  
**Testing**: pytest with coverage plugin (pytest-cov), mypy for static type checking, pylint for code quality  
**Target Platform**: Linux server (existing FlavorHub backend infrastructure)  
**Project Type**: Backend library/service module (recipe search functionality)  
**Performance Goals**: Average latency ≤100ms (P50), P95 latency ≤200ms, cache hit rate ≥60%, throughput ≥1000 searches/sec  
**Constraints**: P95 latency <200ms, cache memory ≤50MB, backward compatible API, zero breaking changes, rollback capability within 5 minutes  
**Scale/Scope**: ~1000 lines of legacy code → 4 modules of ≤300 lines each, 30 functional requirements, 16 success criteria, serving production traffic for thousands of daily users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Reliability Engineering**: Null-safe input validation plan documented (validation_module.py handles all None/null cases per FR-005 through FR-009)
- [x] **II. Modular Architecture**: Module boundaries defined, line counts estimated (4 modules: validation 250 lines, filtering 280 lines, aggregation 295 lines, formatting 180 lines)
- [x] **III. Testability**: Test strategy defined, coverage target set (≥80% per module, test-first approach, independent test suites per FR-024)
- [x] **IV. Performance Optimization**: Performance targets specified, optimization plan clear (100ms P50, 200ms P95, LRU cache with 1000-entry limit, optimal filter ordering per FR-015 through FR-018)
- [x] **V. Maintainability**: Refactoring scope identified (eliminate 74 magic numbers via constants.py, remove 3 deprecated functions per FR-011, FR-026)
- [x] **VI. Quality Standards**: Type hint strategy defined, test framework chosen (complete type hints on all functions, mypy strict mode, pytest framework per FR-025, FR-027)
- [x] **VII. Observability & Operations**: Logging plan documented, guardrails specified (preserve existing DEBUG logging, maintain metrics counters, add module-level instrumentation)
- [x] **VIII. Deployment Safety**: Migration strategy documented, rollback plan ready (feature flags per module, original search.py remains as fallback, gradual per-module rollout per FR-028 through FR-030)

**Status**: ✅ PASS

**Notes**: All 8 constitution principles satisfied. No violations to justify. Module boundaries align with single responsibility principle. Test-first approach ensures quality gate compliance. Gradual rollout strategy mitigates deployment risk.

## Project Structure

### Documentation (this feature)

```text
specs/001-search-modular-refactor/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0: Module extraction strategy, interface design research
├── data-model.md        # Phase 1: Interface contracts (dataclasses) between modules
├── quickstart.md        # Phase 1: Developer guide for working with new modules
├── contracts/           # Phase 1: Module interface specifications
│   ├── validation.md    # validation_module.py public interface
│   ├── filtering.md     # filtering_module.py public interface
│   ├── aggregation.md   # aggregation_module.py public interface
│   └── formatting.md    # formatting_module.py public interface
└── checklists/
    └── requirements.md  # Quality validation checklist (completed)
```

### Source Code (repository root)

```text
recipe-manager/                    # Existing application root
├── models.py                      # Existing - no changes (User, Recipe, SAMPLE_RECIPES)
├── logging_config.py              # Existing - no changes
├── main.py                        # Existing - no changes
├── pytest.ini                     # Existing - no changes
├── requirements.txt               # Existing - will add typing_extensions if needed
├── search.py                      # LEGACY - kept as rollback fallback, deprecated after migration
│
├── search/                        # NEW - module package for refactored search
│   ├── __init__.py               # Public API: exports search_recipes() for backward compatibility
│   ├── constants.py              # NEW - extracted magic numbers (74 constants)
│   ├── validation_module.py     # NEW - Phase 1 Module 1 (~250 lines)
│   ├── filtering_module.py      # NEW - Phase 1 Module 2 (~280 lines)
│   ├── aggregation_module.py    # NEW - Phase 1 Module 3 (~295 lines)
│   └── formatting_module.py     # NEW - Phase 1 Module 4 (~180 lines)
│
├── tests/                        # Existing test directory (currently minimal)
│   ├── __init__.py
│   ├── conftest.py              # Existing - fixtures
│   ├── test_models.py           # Existing - no changes needed
│   ├── test_search.py           # Existing - will be updated for new modules
│   │
│   ├── unit/                    # NEW - unit tests for each module independently
│   │   ├── __init__.py
│   │   ├── test_validation_module.py     # ≥80% coverage for validation
│   │   ├── test_filtering_module.py      # ≥80% coverage for filtering
│   │   ├── test_aggregation_module.py    # ≥80% coverage for aggregation
│   │   └── test_formatting_module.py     # ≥80% coverage for formatting
│   │
│   ├── integration/             # NEW - cross-module integration tests
│   │   ├── __init__.py
│   │   └── test_search_flow.py  # End-to-end search pipeline tests
│   │
│   └── contract/                # NEW - interface contract tests
│       ├── __init__.py
│       └── test_module_contracts.py  # Verify interfaces between modules
│
├── api/                         # Existing API layer - no changes
│   ├── __init__.py
│   ├── routes.py                # Will update imports to use search/ package
│   └── __pycache__/
│
└── __pycache__/                 # Existing - Python bytecode cache
```

**Structure Decision**: Single project structure with new `search/` package for modularized code. Legacy `search.py` remains at root level as fallback during migration. Test organization follows constitution requirement for independent testability: unit tests per module, integration tests for cross-module flows, contract tests for interface verification.

**Key Design Decisions**:
1. **Package-based organization**: `search/` package allows clean imports and clear module boundaries
2. **Backward compatibility layer**: `search/__init__.py` re-exports `search_recipes()` to maintain API contract
3. **Parallel existence**: Legacy `search.py` and new `search/` package coexist during migration, controlled by feature flags
4. **Test hierarchy**: Three-tier testing (unit/integration/contract) enables independent module verification per constitution
5. **Constants extraction**: Dedicated `constants.py` eliminates all 74 magic numbers in single discoverable location

## Complexity Tracking

**No violations**: Constitution Check passed all 8 principles. No complexity justifications required.

---

## Phase 0: Research & Planning

**Goal**: Finalize module extraction strategy, interface design patterns, and rollout approach through research of best practices.

**Output**: `research.md` document with decisions on:
- Module extraction sequence that minimizes system disruption
- Interface design patterns (Python dataclasses vs TypedDict vs Protocol)
- Testing strategy per module (fixtures, mocks, integration patterns)
- Rollout approach: feature flags, A/B testing, gradual migration

**Research Topics**:

### 1. Module Extraction Sequence Strategy

**Question**: In what order should modules be extracted from the monolith to minimize risk and enable incremental value delivery?

**Research Approach**: Analyze dependency graph in existing search.py, identify extraction order that:
- Delivers value early (fix Issue #447 first)
- Minimizes disruption (extract leaf dependencies first)
- Enables incremental testing (validate each module before proceeding)

**Expected Outcome**: Validated sequence:
1. **Phase 1.1: validation_module** - Fixes critical bug (Issue #447), minimal dependencies, immediate value
2. **Phase 1.2: filtering_module** - Depends only on validation, can be tested independently
3. **Phase 1.3: aggregation_module** - Depends on filtering output, adds performance fixes (cache)
4. **Phase 1.4: formatting_module** - Final stage, depends on aggregation, completes migration

### 2. Interface Design Patterns

**Question**: What Python patterns best represent interfaces between modules while maintaining type safety and testability?

**Research Approach**: Evaluate options:
- **Dataclasses**: Built-in, immutable with frozen=True, excellent IDE support
- **TypedDict**: Lightweight, dict-compatible, less strict
- **Protocol**: Structural subtyping, more flexible but complex

**Expected Outcome**: Decision to use **dataclasses** for contracts because:
- Native Python 3.11 support (no additional dependencies)
- Strong type checking with mypy
- Immutability via `frozen=True` prevents accidental mutations
- Clear IDE autocomplete and documentation
- Well-understood by Python community

**Contracts to define**:
- `SearchRequest`: Input from API layer (raw request data)
- `ValidatedSearchInput`: Output from validation_module (sanitized, normalized)
- `FilteredRecipes`: Output from filtering_module (recipes after filters applied)
- `RankedResults`: Output from aggregation_module (scored, cached, paginated)
- `SearchResponse`: Output from formatting_module (final JSON structure)

### 3. Testing Strategy Per Module

**Question**: How can each module achieve ≥80% coverage with independent, maintainable tests?

**Research Approach**: Evaluate pytest patterns:
- Fixtures for test data (recipe samples, user samples)
- Parametrized tests for edge cases
- Mocking strategies for cross-module dependencies
- Contract testing between modules

**Expected Outcome**: Three-tier test strategy:
1. **Unit tests** (tests/unit/): Each module tested in isolation
   - Mock dependencies (e.g., mock filtering_module when testing aggregation_module)
   - Test all edge cases (None values, empty lists, boundary conditions)
   - Fast execution (<1s per module test suite)

2. **Integration tests** (tests/integration/): Full search pipeline
   - Real data flow through all modules
   - No mocks (except external dependencies like database)
   - Verifies modules work together correctly

3. **Contract tests** (tests/contract/): Interface validation
   - Verify dataclass contracts honored
   - Test that outputs match expected structure
   - Catch interface breaking changes early

### 4. Gradual Rollout Approach

**Question**: How can modules be rolled out incrementally to minimize risk while maintaining the ability to rollback?

**Research Approach**: Evaluate deployment strategies:
- Feature flags (per-module on/off switches)
- A/B testing (route % of traffic to new modules)
- Canary deployment (gradual traffic increase)
- Circuit breakers (automatic fallback on errors)

**Expected Outcome**: Gradual per-module rollout plan:

**Phase 1** (Week 1): Deploy validation_module with flag
- Feature flag: `USE_NEW_VALIDATION` (default: False)
- Route 10% of traffic to new validation_module
- Monitor: crash rate, error logs, latency
- Success criteria: Zero crashes for None dietary restrictions
- Rollback trigger: Any increase in error rate

**Phase 2** (Week 2): Deploy filtering_module with flag
- Feature flag: `USE_NEW_FILTERING` (default: False, requires USE_NEW_VALIDATION=True)
- Route 25% of traffic through validation + filtering modules
- Monitor: filter correctness, performance, edge cases
- Success criteria: Identical results to legacy filtering, latency maintained
- Rollback trigger: Incorrect filter results or >10% latency increase

**Phase 3** (Week 3): Deploy aggregation_module with flag
- Feature flag: `USE_NEW_AGGREGATION` (default: False, requires previous flags=True)
- Route 50% of traffic through first 3 modules
- Monitor: cache hit rate, memory usage, ranking correctness
- Success criteria: Cache hit rate ≥60%, memory ≤50MB, latency ≤100ms P50
- Rollback trigger: Memory leak detected or cache miss rate >40%

**Phase 4** (Week 4): Deploy formatting_module, complete migration
- Feature flag: `USE_NEW_SEARCH` (default: False, enables all new modules)
- Route 100% of traffic to new search/ package
- Monitor: Full pipeline metrics, error rates, user satisfaction
- Success criteria: All success criteria met (SC-001 through SC-016)
- Rollback trigger: Any production incident

**Phase 5** (Week 5+): Cleanup and deprecation
- Mark legacy search.py as deprecated
- Remove feature flags after 2 weeks of 100% traffic on new modules
- Delete search.py after validated stable

**Fallback Mechanism**: Each feature flag check includes automatic fallback:
```python
if USE_NEW_VALIDATION:
    try:
        result = new_validation_module.validate(...)
    except Exception as e:
        logger.error(f"New validation failed: {e}, falling back")
        result = legacy_validate(...)  # Automatic fallback
else:
    result = legacy_validate(...)
```

---

## Phase 1: Design & Contracts

**Goal**: Define interface contracts between modules, document module responsibilities, and create developer quickstart guide.

**Prerequisites**: research.md complete (module extraction strategy, interface patterns finalized)

**Outputs**:
1. `data-model.md` - Dataclass definitions for all inter-module contracts
2. `contracts/` directory - Per-module interface specifications
3. `quickstart.md` - Developer guide for working with new module architecture

### 1.1 Data Model (data-model.md)

**Entity: SearchRequest** (Input to validation_module)
```python
@dataclass(frozen=True)
class SearchRequest:
    """Raw search request from API layer (untrusted input)."""
    query: Optional[str] = None
    cuisine: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None
    prep_time_max: Optional[int] = None
    difficulty: Optional[str] = None
    min_rating: Optional[float] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 50
```

**Entity: ValidatedSearchInput** (Output from validation_module, input to filtering_module)
```python
@dataclass(frozen=True)
class ValidatedSearchInput:
    """Validated and normalized search parameters (trusted)."""
    query: str  # Empty string if None, max 500 chars
    cuisine: Optional[str]  # Validated against allowed cuisines or None
    dietary_restrictions: List[str]  # Never None, normalized to []
    prep_time_max: Optional[int]  # Positive integer or None
    difficulty: Optional[str]  # One of: easy, medium, hard, or None
    min_rating: float  # 0.0 to 5.0, default 0.0
    page: int  # ≥1, validated
    page_size: int  # 1 to 200, validated
    user_id: str  # For caching and logging
```

**Entity: FilteredRecipes** (Output from filtering_module, input to aggregation_module)
```python
@dataclass(frozen=True)
class FilteredRecipes:
    """Recipes after all filters applied."""
    recipes: List[Recipe]  # Recipes matching all filter criteria
    applied_filters: Dict[str, Any]  # Which filters were applied
    filter_duration_ms: float  # Performance metric
```

**Entity: RankedResults** (Output from aggregation_module, input to formatting_module)
```python
@dataclass(frozen=True)
class RankedResults:
    """Recipes ranked and paginated, with caching metadata."""
    recipes: List[Recipe]  # Ranked recipes for current page
    total_count: int  # Total recipes before pagination
    cache_hit: bool  # Whether result was served from cache
    ranking_duration_ms: float  # Performance metric
```

**Entity: SearchResponse** (Output from formatting_module, returned to API)
```python
@dataclass(frozen=True)
class SearchResponse:
    """Final search response structure."""
    recipes: List[Dict[str, Any]]  # Formatted recipe objects
    total: int  # Total matching recipes
    page: int  # Current page number
    page_size: int  # Recipes per page
    total_pages: int  # Total pages available
    cache_hit: bool  # Cache indicator for debugging
    duration_ms: float  # Total request duration
```

**Relationships**:
```
SearchRequest → validation_module → ValidatedSearchInput
                                   ↓
ValidatedSearchInput → filtering_module → FilteredRecipes
                                          ↓
FilteredRecipes → aggregation_module → RankedResults
                                       ↓
RankedResults → formatting_module → SearchResponse
```

### 1.2 Module Contracts (contracts/ directory)

**(See individual contract files for detailed specifications)**

**validation_module.py contract** (contracts/validation.md):
- **Responsibility**: Validate and normalize all input parameters, prevent TypeError from None values
- **Exposes**: `validate_search_request(request: SearchRequest, user: User) -> ValidatedSearchInput`
- **Never returns None**: All Optional fields normalized (e.g., None dietary_restrictions → [])
- **Enforces limits**: Query ≤500 chars, page_size ≤200, page ≥1, rating 0.0-5.0
- **Fails fast**: Raises `ValidationError` with clear message for invalid input

**filtering_module.py contract** (contracts/filtering.md):
- **Responsibility**: Apply all filters in optimal order, short-circuit when possible
- **Exposes**: `apply_filters(validated_input: ValidatedSearchInput, recipes: List[Recipe]) -> FilteredRecipes`
- **Filter order**: query → cuisine → dietary → prep_time → difficulty → rating
- **Short-circuits**: Stops when result set is empty (no need for remaining filters)
- **Performance**: Target ≤20ms for typical filter operations

**aggregation_module.py contract** (contracts/aggregation.md):
- **Responsibility**: Rank recipes, manage cache, paginate results
- **Exposes**: `aggregate_and_rank(filtered: FilteredRecipes, validated_input: ValidatedSearchInput) -> RankedResults`
- **Caching**: LRU cache with 1000-entry max, 300-second TTL, keyed by user_id + filters
- **Ranking**: hybrid_v3 algorithm (relevance 45% + rating 30% + popularity 25%)
- **Pagination**: Slice ranked results by page/page_size

**formatting_module.py contract** (contracts/formatting.md):
- **Responsibility**: Format results into API response structure
- **Exposes**: `format_response(ranked: RankedResults, validated_input: ValidatedSearchInput) -> SearchResponse`
- **Handles empty**: Returns valid structure even when recipes=[]
- **Includes metadata**: Cache hit indicator, duration metrics, pagination info

### 1.3 Quickstart Guide (quickstart.md)

Comprehensive developer guide covering:
- **Getting Started**: How to import and use new search modules
- **Module Overview**: Purpose and responsibility of each module
- **Testing**: How to run tests, add new tests, achieve ≥80% coverage
- **Migration**: How feature flags work, rollout process
- **Debugging**: How to enable DEBUG logging, interpret metrics
- **Contributing**: How to add new filters, modify ranking, extend functionality

---

## Phase 2: Implementation (NOT in this plan)

**Note**: Implementation tasks are generated by `/speckit.tasks` command AFTER Phase 1 design is complete.

Phase 2 will include:
- T001-T050: Detailed implementation tasks for each module
- Test-first approach: Write tests → verify failure → implement → verify pass
- Incremental rollout tasks: Deploy with feature flags, monitor, adjust
- Cleanup tasks: Remove deprecated code, delete magic numbers, update documentation

**DO NOT proceed to implementation until**:
- This plan is reviewed and approved
- Constitution Check validated (✅ already passed)
- All Phase 1 design artifacts reviewed (data-model.md, contracts/, quickstart.md)

---

## Risks and Mitigation

### High Risk: Breaking Changes During Migration

**Risk**: Subtle behavior differences between legacy and new modules cause incorrect search results.

**Mitigation**:
- Comprehensive contract tests verify interface compatibility
- Integration tests compare legacy vs new module outputs for 1000+ test cases
- Gradual rollout with A/B testing (side-by-side comparison)
- Automatic fallback on any Exception (catch-all in feature flag logic)
- Rollback plan: Flip feature flag off, restart services (≤5 minutes)

### Medium Risk: Performance Regression

**Risk**: Module boundaries introduce overhead, latency increases.

**Mitigation**:
- Benchmark each module independently (unit tests include timing)
- Load testing before each rollout phase (locust or similar tool)
- Module boundaries designed for minimum data copying (frozen dataclasses, pass by reference)
- Continuous monitoring of P50/P95 latency during rollout
- Rollback trigger: >10% latency increase at any rollout phase

### Medium Risk: Cache Behavior Changes

**Risk**: New caching implementation behaves differently (miss rate, staleness, memory usage).

**Mitigation**:
- Parallel cache warming: Run old and new cache side-by-side during A/B test
- Monitor cache hit rate (target ≥60%) vs baseline
- Memory profiler running in staging environment for 24 hours before production
- Gradual cache TTL increase (start with 60s, increase to 300s over time)
- Circuit breaker: Disable cache if memory exceeds 50MB or hit rate <40%

### Low Risk: Type Hint Compatibility

**Risk**: mypy strict mode catches issues only during development, runtime type errors possible.

**Mitigation**:
- CI/CD pipeline enforces mypy strict mode (blocks merge if type errors)
- Runtime validation at module boundaries (pydantic or dataclass validation)
- Comprehensive edge case testing (None, empty, malformed inputs)
- Python 3.11 provides better error messages for type mismatches

---

## Success Validation

After implementation complete and deployed to 100% of traffic, validate all 16 success criteria:

**Reliability** (SC-001 to SC-003):
- [ ] SC-001: Zero crashes for dietary_restrictions=None (100% success rate)
- [ ] SC-002: Zero TypeError/AttributeError/KeyError from search module
- [ ] SC-003: All edge cases return valid responses (even if empty results)

**Performance** (SC-004 to SC-007):
- [ ] SC-004: P50 latency ≤100ms (monitor DataDog/New Relic)
- [ ] SC-005: P95 latency ≤200ms under 1000 concurrent users
- [ ] SC-006: Cache hit rate ≥60% (measure over 24 hours)
- [ ] SC-007: Cache memory ≤50MB (monitor for 7 days)

**Code Quality** (SC-008 to SC-013):
- [ ] SC-008: All 4 modules ≥80% coverage (pytest-cov report)
- [ ] SC-009: Zero magic numbers (replaced with constants.py)
- [ ] SC-010: Zero deprecated functions (v1, v2 suffixes removed)
- [ ] SC-011: pylint ≥9.0/10, mypy strict passes with zero errors
- [ ] SC-012: All modules ≤300 lines (wc -l verification)
- [ ] SC-013: New developer understands modules in ≤15 minutes (onboarding survey)

**Backward Compatibility** (SC-014 to SC-016):
- [ ] SC-014: 100% API consumers work without code changes
- [ ] SC-015: Zero breaking changes to search_recipes() signature
- [ ] SC-016: Rollback capability validated (test in staging)

---

## Next Steps

1. **Review this plan**: Team reviews all sections, approves approach
2. **Create Phase 0 artifacts**: Generate research.md with findings from research topics
3. **Create Phase 1 artifacts**: Generate data-model.md, contracts/, quickstart.md
4. **Update agent context**: Run update-agent-context.ps1 to incorporate Python/pytest/mypy context
5. **Generate tasks**: Run `/speckit.tasks` to break down implementation into ordered tasks
6. **Begin implementation**: Execute tasks following test-first approach, gradual rollout strategy

**Estimated Timeline**:
- Phase 0 (Research): 2 days
- Phase 1 (Design): 3 days
- Phase 2 (Implementation): 2-3 weeks (includes testing, rollout, validation)
- Total: 3-4 weeks from plan approval to full deployment
