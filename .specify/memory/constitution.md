<!--
SYNC IMPACT REPORT
==================
Version Change: TEMPLATE → 1.0.0 (Initial Ratification)
Ratification Date: 2026-03-11
Last Amendment: 2026-03-11

Changes Applied:
  ✅ Initial constitution created for FlavorHub Recipe Manager refactoring
  ✅ 8 core principles defined (expanded from 5-principle template)
  ✅ Added Code Quality Standards section
  ✅ Added Development Workflow section
  ✅ Governance rules established

Principles Defined:
  1. I. Reliability Engineering (null-safe input validation)
  2. II. Modular Architecture (4 modules, <300 lines each)
  3. III. Testability (>80% coverage, independently testable)
  4. IV. Performance Optimization (fix caching leaks, optimize filters)
  5. V. Maintainability (remove magic numbers & dead code)
  6. VI. Quality Standards (tests + type hints)
  7. VII. Observability & Operations (logging + guardrails)
  8. VIII. Deployment Safety (backward compatibility)

Templates Requiring Updates:
  ✅ spec-template.md - aligned with testability requirements
  ✅ plan-template.md - Constitution Check references all 8 principles
  ✅ tasks-template.md - task categorization reflects principles
  
Follow-up TODOs:
  - None (all fields completed)

Compliance Notes:
  - All future features MUST comply with the 8 core principles
  - Any principle violation requires explicit justification in Complexity Tracking section of plan.md
  - Constitution amendments follow semantic versioning: MAJOR for breaking changes, MINOR for new principles, PATCH for clarifications
-->

# FlavorHub Recipe Manager Constitution

## Core Principles

### I. Reliability Engineering
**MANDATORY: Null-Safe Input Validation**

Every function MUST validate inputs before processing:
- Check for None/null values before iteration or attribute access
- Use Optional type hints to signal nullable parameters
- Provide sensible defaults (e.g., empty list `[]` instead of None) where semantically appropriate
- Fail fast with clear error messages for invalid inputs

**Rationale**: The production bug (Issue #447) affected 30% of users due to missing null checks. This principle prevents similar reliability issues by mandating defensive programming upfront.

**Quality Gate**: Code review MUST verify null safety; automated tests MUST include None/empty/edge case scenarios.

---

### II. Modular Architecture
**MANDATORY: Four Modules, Each Under 300 Lines**

The search.py monolith (847 lines) MUST be refactored into exactly 4 modules:
1. **search_filters.py** - Filter logic (query, cuisine, dietary, time, difficulty, rating)
2. **search_ranking.py** - Ranking algorithms and relevance scoring
3. **search_cache.py** - Caching layer with proper memory management
4. **search_core.py** - Public API and orchestration

**Module Constraints**:
- Each module MUST be ≤300 lines (excluding comments/blanks)
- Each module MUST have single, clear responsibility
- No circular dependencies allowed
- Each module MUST export explicit public interface

**Rationale**: Large files reduce maintainability and increase cognitive load. Modular design enables parallel development, easier testing, and better separation of concerns.

**Quality Gate**: Pre-commit hook enforces line count; architecture diagram MUST be updated with module boundaries.

---

### III. Testability
**MANDATORY: 80%+ Coverage, Independently Testable Modules**

Every module MUST achieve ≥80% code coverage:
- Unit tests for each public function
- Integration tests for module interactions
- Contract tests for public APIs
- Each module MUST be testable in isolation (no implicit dependencies)

**Test Organization**:
```
tests/
├── unit/
│   ├── test_search_filters.py
│   ├── test_search_ranking.py
│   ├── test_search_cache.py
│   └── test_search_core.py
├── integration/
│   └── test_search_flow.py
└── contract/
    └── test_search_api.py
```

**Rationale**: Zero test coverage contributed to the production incident going undetected. High coverage with independent tests enables confident refactoring and prevents regressions.

**Quality Gate**: pytest coverage report MUST show ≥80%; CI pipeline blocks merge if coverage drops.

---

### IV. Performance Optimization
**MANDATORY: Fix Memory Leak, Optimize Filter Ordering**

Performance improvements MUST include:
1. **Cache Memory Leak**: Fix unbounded cache growth in search_cache.py
   - Implement LRU eviction policy
   - Set max cache size (e.g., 1000 entries)
   - Add cache metrics (hit rate, size, evictions)

2. **Filter Ordering Optimization**: Apply cheapest filters first
   - Query match → Cuisine → Dietary → Prep time → Difficulty → Rating
   - Short-circuit when filter reduces results to zero
   - Document filter costs in search_filters.py

**Performance Targets**:
- Average search latency: ≤100ms (down from 280ms)
- P95 latency: ≤200ms
- Cache hit rate: ≥60%
- Memory usage: ≤50MB for cache

**Rationale**: Current system has degraded performance (280ms average) and unbounded memory growth. Addressing these issues improves user experience and system stability.

**Quality Gate**: Load testing MUST verify latency targets; memory profiling MUST show bounded cache.

---

### V. Maintainability
**MANDATORY: Eliminate Magic Numbers & Dead Code**

Code cleanup MUST include:
1. **Remove Magic Numbers** (74 identified):
   - Extract to named constants in module-level CONSTANTS section
   - Use enums for related groups (e.g., DifficultyLevel, CuisineType)
   - Document meaning and rationale for each constant

2. **Remove Dead Code**:
   - Delete unused functions (e.g., deprecated filter_by_dietary_v1)
   - Remove commented-out code blocks
   - Clean up unused imports

**Example**:
```python
# Before: Magic numbers
if score > 4.5: ...

# After: Named constant
EXCELLENT_RECIPE_THRESHOLD = 4.5  # Top 10% quality recipes
if score > EXCELLENT_RECIPE_THRESHOLD: ...
```

**Rationale**: Magic numbers obscure intent and make updates error-prone. Dead code increases cognitive load and maintenance burden.

**Quality Gate**: Code review MUST verify no naked literals; static analysis (pylint) flags unused code.

---

### VI. Quality Standards
**MANDATORY: Tests + Type Hints for All Code**

Every module MUST include:
1. **Type Hints**: All function signatures MUST have complete type annotations
   - Parameters: specify types (no bare parameters)
   - Return values: explicit return type (including None)
   - Use typing module for complex types (List, Dict, Optional, Union, etc.)

2. **Tests**: Every public function MUST have tests
   - Minimum 3 test cases per function (happy path, edge case, error case)
   - Use pytest fixtures for common setup
   - Clear test names: `test_<function>_<scenario>_<expected_outcome>`

**Example**:
```python
from typing import List, Optional

def filter_recipes(
    recipes: List[Recipe],
    restrictions: Optional[List[str]] = None
) -> List[Recipe]:
    """Filter recipes by dietary restrictions."""
    ...
```

**Rationale**: Type hints enable static analysis, catch bugs early, and improve IDE support. Comprehensive tests ensure correctness and enable confident refactoring.

**Quality Gate**: mypy strict mode MUST pass with zero errors; test coverage ≥80%.

---

### VII. Observability & Operations
**MANDATORY: Structured Logging + Operational Guardrails**

Observability requirements:
1. **Structured Logging**: Use Python logging module with structured format
   - Log levels: DEBUG (development), INFO (key operations), WARNING (degraded state), ERROR (failures)
   - Include context: user_id, request_id, operation, duration
   - Log search performance metrics (filter times, cache hits)

2. **Operational Guardrails**:
   - Request timeout: 5 seconds (prevent runaway queries)
   - Max result size: 1000 recipes (prevent memory exhaustion)
   - Circuit breaker for database calls
   - Health check endpoint

**Example Log Entry**:
```json
{
  "timestamp": "2026-03-11T15:42:10Z",
  "level": "INFO",
  "user_id": "uuid-123",
  "operation": "search_recipes",
  "query": "pasta",
  "results": 12,
  "duration_ms": 87,
  "cache_hit": true
}
```

**Rationale**: Production issues require observability to diagnose. Guardrails prevent resource exhaustion and cascading failures.

**Quality Gate**: All key operations MUST emit structured logs; load tests MUST verify guardrails trigger correctly.

---

### VIII. Deployment Safety
**MANDATORY: Backward Compatibility**

All changes MUST maintain backward compatibility:
- Public API signatures MUST NOT change (search_recipes function interface)
- Database schema changes MUST be additive only (no column drops/renames)
- Configuration changes MUST support old and new formats during migration
- Deprecation warnings MUST precede removals by at least one release

**Migration Strategy**:
1. Deploy new code with old and new interfaces
2. Monitor for errors/performance regressions
3. Gradually migrate clients to new interface
4. Remove old interface after migration complete

**Rollback Plan**:
- Feature flags for new modules (can disable individually)
- Database migrations MUST be reversible
- Monitoring dashboards for key metrics (error rate, latency, cache hit rate)

**Rationale**: Production system serves 70% of users successfully. Changes must be incremental and reversible to minimize risk.

**Quality Gate**: Integration tests MUST verify old interface still works; deployment checklist MUST include rollback procedure.

---

## Code Quality Standards

### Static Analysis
- **Linter**: pylint with score ≥9.0/10
- **Type Checker**: mypy in strict mode (zero errors)
- **Formatter**: black (automatic formatting)
- **Import Sorting**: isort (automatic)

### Code Review Requirements
All code changes MUST:
- Pass automated quality gates (tests, coverage, linting, type checking)
- Be reviewed by at least one other engineer
- Include updated documentation for public APIs
- Include migration guide for breaking changes (if any - should be rare per Principle VIII)
- Verify compliance with all 8 core principles

### Pull Request Template
```markdown
## Description
[What changed and why]

## Constitution Compliance Checklist
- [ ] I. Reliability: Null checks added
- [ ] II. Architecture: Module stays under 300 lines
- [ ] III. Testability: Tests added, coverage ≥80%
- [ ] IV. Performance: No performance regressions
- [ ] V. Maintainability: No magic numbers, no dead code
- [ ] VI. Quality: Type hints + tests included
- [ ] VII. Observability: Logging added for key operations
- [ ] VIII. Deployment Safety: Backward compatible

## Testing
[How was this tested?]

## Rollback Plan
[How to revert if needed]
```

---

## Development Workflow

### Feature Development Process
1. **Specification** (`/speckit.specify`): Define user stories and requirements
2. **Planning** (`/speckit.plan`): Design architecture, run Constitution Check
3. **Task Breakdown** (`/speckit.tasks`): Create ordered, dependency-aware task list
4. **Implementation**: TDD - write tests first, then implement
5. **Review**: Verify constitution compliance, pass quality gates
6. **Deployment**: Monitor metrics, ready to rollback if needed

### Constitution Check (Mandatory Gate)
Before implementation begins, run Constitution Check in plan.md:
- [ ] I. Reliability: Null safety plan documented
- [ ] II. Architecture: Module boundaries defined, line counts estimated
- [ ] III. Testability: Test strategy defined, coverage target set
- [ ] IV. Performance: Performance targets specified, optimization plan clear
- [ ] V. Maintainability: Refactoring scope identified (magic numbers, dead code)
- [ ] VI. Quality: Type hint strategy defined, test framework chosen
- [ ] VII. Observability: Logging plan documented, guardrails specified
- [ ] VIII. Deployment Safety: Migration strategy documented, rollback plan ready

**If ANY check fails**: Document in Complexity Tracking section of plan.md with explicit justification.

### CI/CD Pipeline Gates
All commits MUST pass:
1. Unit tests (pytest)
2. Coverage check (≥80%)
3. Type checking (mypy strict)
4. Linting (pylint ≥9.0)
5. Formatting (black --check)
6. Integration tests
7. Performance benchmarks (no >10% regression)

### Emergency Hotfix Process
For production incidents:
1. **Immediate**: Apply minimal fix to restore service
2. **Short-term** (within 1 week): Add tests, improve error handling
3. **Long-term** (next sprint): Root cause analysis, principle updates if needed

---

## Governance

### Authority
This constitution supersedes all other development practices, style guides, and conventions. When in doubt, constitution principles take precedence.

### Amendment Process
Constitution amendments require:
1. **Proposal**: Document proposed change with rationale
2. **Review**: Team discussion and consensus (or tech lead approval for urgent updates)
3. **Version Bump**: Follow semantic versioning
   - **MAJOR**: Backward-incompatible governance changes, principle removals/redefinitions
   - **MINOR**: New principles added, materially expanded guidance
   - **PATCH**: Clarifications, wording fixes, non-semantic refinements
4. **Migration Plan**: Document impact on existing code and templates
5. **Propagation**: Update all dependent templates (spec, plan, tasks, commands)

### Compliance Enforcement
- All pull requests MUST include constitution compliance checklist
- Code reviews MUST verify adherence to all 8 principles
- Principle violations MUST be explicitly justified in Complexity Tracking section
- CI/CD pipeline enforces automated quality gates
- Quarterly constitution review to ensure relevance and effectiveness

### Living Document
This constitution is a living document. As we learn from the FlavorHub refactoring and future work, we will:
- Capture lessons learned in memory files (`.specify/memory/`)
- Update principles based on what works and what doesn't
- Evolve quality gates to match project maturity
- Balance rigor with pragmatism

**Version**: 1.0.0 | **Ratified**: 2026-03-11 | **Last Amended**: 2026-03-11
