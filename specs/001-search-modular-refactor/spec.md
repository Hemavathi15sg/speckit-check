# Feature Specification: Search Module Refactoring

**Feature Branch**: `001-search-modular-refactor`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "Break search.py into 4 modules with 80%+ coverage and backward compatibility"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reliable Search for All Users (Priority: P1) 🎯 MVP

When any user searches for recipes (regardless of dietary preferences), the search must complete successfully and return relevant results. Currently, 30% of users experience crashes due to null handling bugs in the dietary restrictions filter.

**Why this priority**: This fixes a critical production bug (Issue #447) affecting 30% of users. Search is the core feature of FlavorHub - when it''s broken, the product is unusable for affected users. This must be fixed immediately.

**Independent Test**: Create a test user with `dietary_restrictions=None`, execute a search for "pasta", verify results are returned without TypeError. Success metric: Zero crashes for null dietary restrictions.

**Acceptance Scenarios**:

1. **Given** a user with `dietary_restrictions=None`, **When** they search for any recipe, **Then** search completes successfully with appropriate results (all recipes matching query regardless of dietary tags)
2. **Given** a user with `dietary_restrictions=[]` (empty list), **When** they search for recipes, **Then** behavior is identical to None case (all recipes returned)
3. **Given** a user with specific dietary restrictions like `[''vegan'']`, **When** they search for recipes, **Then** only recipes with matching dietary tags are returned
4. **Given** malformed input (invalid types, unexpected structures), **When** validation runs, **Then** system fails fast with clear error message rather than crashing during search

---

### User Story 2 - Maintainable Codebase for Developers (Priority: P2)

Developers can understand, modify, and test individual search components without navigating a 1000+ line monolithic file. Each module has a single, clear responsibility and can be modified independently without fear of breaking unrelated functionality.

**Why this priority**: Current 1006-line search.py is unmaintainable. Developers waste hours navigating dead code, deprecated functions, and tangled dependencies. Refactoring reduces cognitive load and enables parallel development.

**Independent Test**: Verify each of the 4 modules (validation, filtering, aggregation, formatting) is ≤300 lines, has no circular dependencies, and can be imported and tested independently. Success metric: All modules pass independent unit tests with >80% coverage.

**Acceptance Scenarios**:

1. **Given** a developer needs to modify filter logic, **When** they open filtering_module.py, **Then** they see only filter-related code (no validation, ranking, or formatting logic mixed in)
2. **Given** a developer wants to add a new filter, **When** they modify filtering_module.py, **Then** changes don''t require modifications to validation, aggregation, or formatting modules
3. **Given** a new developer joins the team, **When** they read module interfaces, **Then** they can understand each module''s purpose and contract within 15 minutes
4. **Given** test suite runs, **When** each module is tested, **Then** each module achieves ≥80% code coverage independently

---

### User Story 3 - Fast and Reliable Search Results (Priority: P3)

Users receive search results quickly (≤100ms average, ≤200ms P95) with intelligent caching that doesn''t leak memory or serve stale data. The system gracefully handles high load without degradation.

**Why this priority**: Current system has 280ms average latency and a cache memory leak (Issue #183). Improving performance enhances user experience and reduces infrastructure costs. However, this is lower priority than fixing crashes and improving maintainability.

**Independent Test**: Run load test with 1000 concurrent searches, measure latency distribution and memory usage over 1 hour. Success metric: P95 latency ≤200ms, memory usage remains bounded below 50MB for cache.

**Acceptance Scenarios**:

1. **Given** a search request is received, **When** processing completes, **Then** response time is ≤100ms on average (down from 280ms)
2. **Given** identical search requests are made within cache TTL, **When** second request is processed, **Then** results are served from cache (cache hit rate ≥60%)
3. **Given** cache has been running for 24 hours, **When** memory usage is measured, **Then** cache size remains bounded (≤50MB, using LRU eviction)
4. **Given** 1000 concurrent users searching, **When** load is sustained for 5 minutes, **Then** P95 latency remains ≤200ms with zero errors

---

### User Story 4 - Clean, Modern Codebase (Priority: P4)

The codebase is free of technical debt: no magic numbers, no dead code, no deprecated functions, and all configuration is externalized. Code follows modern Python best practices with complete type hints and clear documentation.

**Why this priority**: While not blocking functionality, technical debt slows development and increases bug risk. This work makes future changes safer and faster. It''s the lowest priority because the system can function with technical debt, but cleaning it up pays dividends long-term.

**Independent Test**: Run static analysis tools (pylint, mypy) on all modules, verify no magic numbers remain, confirm all deprecated functions are removed. Success metric: pylint score ≥9.0/10, mypy strict mode passes with zero errors.

**Acceptance Scenarios**:

1. **Given** code uses numeric or string literals, **When** developer reviews code, **Then** all literals are replaced with named constants (eliminate all 74 magic numbers)
2. **Given** deprecated functions exist in old code, **When** refactoring completes, **Then** all deprecated functions (v1, v2 variants) are removed from codebase
3. **Given** code file is analyzed, **When** type checker runs, **Then** all functions have complete type hints (parameters and return types)
4. **Given** configuration is needed, **When** system initializes, **Then** config is loaded from environment variables (no hardcoded DB credentials)

---

### Edge Cases

- **Null/None inputs**: What happens when `user=None`, `request=None`, `dietary_restrictions=None`? System must handle gracefully without crashes.
- **Empty datasets**: What if no recipes match filters? Return empty result set with clear message, not an error.
- **Malformed requests**: What if request contains invalid JSON, unexpected fields, or wrong types? Validation layer must reject early with clear error messages.
- **Cache edge cases**: What happens when cache is full? LRU eviction must trigger. What if cached data becomes stale? TTL expiration must invalidate.
- **Concurrent access**: What if multiple threads access cache simultaneously? Thread-safe operations required.
- **Extreme inputs**: What if query is 10,000 characters long? Validation must enforce reasonable limits. What if user has 1000 dietary restrictions? System must handle or reject with clear limit message.
- **Backward compatibility**:What if existing API consumers send legacy request formats? Module must support old and new formats during migration period.

## Requirements *(mandatory)*

### Functional Requirements

**Module Structure & Architecture**

- **FR-001**: System MUST refactor search.py monolith into exactly 4 modules: `validation_module.py`, `filtering_module.py`, `aggregation_module.py`, and `formatting_module.py`
- **FR-002**: Each module MUST be ≤300 lines of code (excluding comments and blank lines) per Constitution Principle II
- **FR-003**: Each module MUST have a single, clearly defined responsibility with no overlapping concerns between modules
- **FR-004**: Modules MUST have no circular dependencies; only unidirectional dependencies allowed (validation → filtering → aggregation → formatting)

**Validation Module (null-safe input handling)**

- **FR-005**: validation_module.py MUST validate all inputs before processing (user object, request dict, query strings, filter parameters)
- **FR-006**: Validation MUST check for None/null values on all optional fields before iteration or attribute access
- **FR-007**: When `user.dietary_restrictions` is None or empty list, validation MUST normalize to empty list `[]` to prevent TypeError at line 447
- **FR-008**: Validation MUST enforce input constraints (query length ≤500 chars, page size ≤200, reasonable limits on all parameters)
- **FR-009**: Invalid inputs MUST fail fast with descriptive error messages indicating which field failed validation and why

**Filtering Module (active filters only)**

- **FR-010**: filtering_module.py MUST implement all active filter functions: query match, cuisine, dietary restrictions, prep time, difficulty, rating
- **FR-011**: Filtering MUST remove all deprecated code (filter_by_dietary_v1, filter_by_dietary_v2, parse_search_request_v1, parse_search_request_v2, etc.)
- **FR-012**: Filters MUST be applied in optimal order (cheapest first): query → cuisine → dietary → prep time → difficulty → rating
- **FR-013**: Filtering MUST short-circuit when result set is reduced to zero (no need to apply remaining filters)
- **FR-014**: Each filter function MUST handle edge cases (empty input lists, None values, malformed data) gracefully

**Aggregation Module (ranking and caching)**

- **FR-015**: aggregation_module.py MUST implement recipe ranking with hybrid_v3 algorithm (relevance, rating, and popularity components)
- **FR-016**: Caching MUST implement LRU eviction policy with configurable max size (default 1000 entries) to fix memory leak
- **FR-017**: Cache keys MUST incorporate user_id and request parameters to prevent serving wrong user''s cached results
- **FR-018**: Cache MUST respect TTL (default 300 seconds) and automatically invalidate stale entries
- **FR-019**: Aggregation MUST remove all dead code from failed A/B tests and unused ranking algorithms

**Formatting Module (response formatting)**

- **FR-020**: formatting_module.py MUST format search results into response structure with recipes array, total count, pagination metadata
- **FR-021**: Formatting MUST remove all legacy XML support code (incomplete feature never used in production)
- **FR-022**: Response format MUST support pagination (page number, page size, total results, total pages)
- **FR-023**: Formatting MUST handle empty result sets gracefully (return valid response structure with empty recipes array)

**Quality & Testing**

- **FR-024**: Each module MUST achieve ≥80% code coverage with independent unit tests per Constitution Principle III
- **FR-025**: All functions MUST have complete type hints (parameters and return types) per Constitution Principle VI
- **FR-026**: All 74 magic numbers MUST be replaced with named constants per Constitution Principle V
- **FR-027**: All code MUST pass static analysis: pylint score ≥9.0/10, mypy strict mode with zero errors per Constitution Principle VI

**Backward Compatibility & Deployment**

- **FR-028**: Public API MUST maintain backward compatibility - existing `search_recipes(request, user)` function signature unchanged per Constitution Principle VIII
- **FR-029**: System MUST support gradual migration - all modules must be importable and testable independently before full integration
- **FR-030**: Original search.py MUST remain available during migration as fallback until new modules are verified in production per Constitution Principle VIII

### Key Entities

- **SearchRequest**: Input structure containing query string, optional filters (cuisine, dietary restrictions, prep time, difficulty, min rating), pagination parameters (page, page_size)

- **SearchFilters**: Validated and normalized filter parameters extracted from SearchRequest, including boundary checks and type coercion

- **Recipe**: Core entity with attributes: name, ingredients list, dietary_tags list, cuisine string, prep_time_minutes integer, difficulty string, avg_rating float

- **User**: Entity with attributes: id UUID, name string, email string, dietary_restrictions Optional[List[str]] (this is where None-handling bug occurs)

- **SearchResult**: Output structure containing filtered and ranked recipes list, total count, pagination metadata, cache hit indicator, processing time metrics

- **CacheEntry**: Internal structure for caching with cache_key string, cached_result SearchResult, timestamp datetime, TTL integer, hit_count integer for LRU

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Reliability**

- **SC-001**: Zero crashes due to null dietary restrictions - 100% of searches with `dietary_restrictions=None` complete successfully (currently 0% due to TypeError)
- **SC-002**: Zero production errors from search module - eliminate all TypeError, AttributeError, and KeyError exceptions currently logged
- **SC-003**: 100% of edge cases handled gracefully - system returns valid responses (even if empty) for all tested edge case scenarios

**Performance**

- **SC-004**: Average search latency ≤100ms (down from current 280ms) measured at 50th percentile
- **SC-005**: P95 search latency ≤200ms under normal load (1000 concurrent users) measured over 24 hour period
- **SC-006**: Cache hit rate ≥60% for repeated searches within 5-minute window
- **SC-007**: Memory usage for cache remains bounded ≤50MB over 24 hours (currently unbounded growth)

**Code Quality & Maintainability**

- **SC-008**: All 4 modules individually achieve ≥80% code coverage (currently 0% for entire search.py)
- **SC-009**: Zero magic numbers remain - all 74 numeric/string literals replaced with named constants
- **SC-010**: All deprecated code removed - zero functions with v1, v2 suffixes or commented-out code blocks
- **SC-011**: Static analysis scores: pylint ≥9.0/10, mypy strict mode passes with zero type errors
- **SC-012**: Each module ≤300 lines - all 4 modules comply with constitution line limit
- **SC-013**: Time to understand each module ≤15 minutes for new developer (measured via onboarding survey)

**Backward Compatibility**

- **SC-014**: 100% of existing API consumers continue working without code changes during migration period
- **SC-015**: Zero breaking changes to public `search_recipes()` function signature or response format
- **SC-016**: Ability to rollback to original search.py within 5 minutes in case of issues

## Scope & Boundaries

### In Scope

- Refactoring search.py into 4 modules (validation, filtering, aggregation, formatting)
- Fixing null-handling bug at line 447 (dietary restrictions)
- Removing all 74 magic numbers and dead/deprecated code
- Adding comprehensive test coverage (≥80% per module)
- Adding complete type hints to all functions
- Implementing proper LRU cache with bounded memory
- Optimizing filter ordering for performance
- Removing legacy XML formatting code
- Externalizing configuration (DB credentials, feature flags)
- Maintaining full backward compatibility with existing API

### Out of Scope

- Database schema changes (use existing Recipe and User models as-is)
- Frontend changes (API contract remains unchanged)
- Adding new search features (semantic search, ML ranking, etc.)
- Changes to authentication/authorization
- Modifications to other modules (models.py, api/routes.py remain unchanged)
- Infrastructure changes (deployment, scaling, monitoring services)
- Database connection pooling (can be added later as separate feature)
- Migration of feature flags to feature flag service (keep in config for now)

### Dependencies

- Python 3.11+ (existing requirement)
- pytest for testing framework (existing)
- mypy for type checking (existing)
- pylint for linting (existing)
- Existing models.py (User, Recipe, SAMPLE_RECIPES) - no changes required
- Existing database schema - no migrations needed

### Assumptions

- Current search.py API contract is considered stable and correct (backward compatibility required)
- Hybrid_v3 ranking algorithm is the correct production algorithm (as indicated by RANKING_ALGORITHM constant)
- Cache TTL of 300 seconds (5 minutes) is appropriate for recipe search
- Maximum cache size of 1000 entries provides good hit rate without excessive memory
- All deprecated code (v1, v2 variants) can be safely removed (no hidden dependencies)
- Database connection pattern can remain the same initially (connection pooling is future enhancement)
- Feature flags currently in code are accurate (ENABLE_CACHE=True, ENABLE_FUZZY_SEARCH=True, etc.)

## Notes

### Technical Debt Being Addressed

This refactoring eliminates significant technical debt:
- **1006 lines → 4 modules of ≤300 lines each**: Improves readability and maintainability
- **74 magic numbers → named constants**: Improves code clarity and reduces error risk
- **0% test coverage → 80%+ coverage**: Enables confident refactoring and reduces regression risk
- **3 deprecated functions → 0**: Eliminates dead code and reduces confusion
- **Unbounded cache → LRU with limit**: Fixes memory leak (Issue #183)
- **Hardcoded config → externalized**: Follows 12-factor app principles
- **No type hints → complete type hints**: Enables stat analysis and IDE support

### Risk Mitigation

**High Risk**: Breaking backward compatibility
- *Mitigation*: Keep original search.py as fallback, extensive integration testing, gradual rollout

**Medium Risk**: Performance regression during refactoring
- *Mitigation*: Benchmark each module, load testing before production, rollback plan ready

**Medium Risk**: Missing edge cases in validation
- *Mitigation*: Comprehensive test suite, fuzz testing, staged rollout to catch issues early

**Low Risk**: Module boundaries incorrect (need to refactor refactoring)
- *Mitigation*: Review module interfaces with team, validate each module can be tested independently

### Compliance with Constitution

This specification aligns with all 8 FlavorHub Constitution principles:

✅ **I. Reliability Engineering**: FR-005 through FR-009 mandate null-safe input validation  
✅ **II. Modular Architecture**: FR-001 and FR-002 enforce 4 modules ≤300 lines each  
✅ **III. Testability**: FR-024 requires ≥80% coverage, each module independently testable  
✅ **IV. Performance Optimization**: FR-015 through FR-018 fix cache leak and optimize filters  
✅ **V. Maintainability**: FR-026 removes all 74 magic numbers, FR-011 removes deprecated code  
✅ **VI. Quality Standards**: FR-025 and FR-027 mandate type hints and static analysis passing  
✅ **VII. Observability & Operations**: Existing DEBUG logging preserved, metrics maintained  
✅ **VIII. Deployment Safety**: FR-028 through FR-030 ensure backward compatibility and rollback capability

---

**Next Steps**: Run `/speckit.clarify` if any requirements need clarification, or proceed directly to `/speckit.plan` to generate implementation plan with Constitution Check.