# Exercise 3: Spec Kit — Constitution & Specification

> **Time:** ~8 minutes
> **Prerequisite:** Spec Kit installed and initialized (`exercise-2.md`)
> **Track:** 🟢 Mandatory — Required for Exercises 4 and 5

---

> **Note for participants:** This exercise builds on Exercise 2 and is required before you can do Exercises 4 and 5. The outputs (`constitution.md` and `specification.md`) are referenced in the planning and implementation steps.

---

## Goal

Define the governing principles for the refactor (constitution), then generate a detailed specification of what will be built.

---

## Context

`search.py` is a 1006-line God Object. The plan is to split it into 4 focused modules:

| Module | Responsibility |
|--------|---------------|
| `validation_module.py` | Input validation and null handling — **fixes the crash** |
| `filtering_module.py` | Clean filter logic, no deprecated code |
| `aggregation_module.py` | Ranking and caching — **fixes the memory leak** |
| `formatting_module.py` | Response formatting only |

---

## Steps

**1.** Open Copilot Chat and run:

```
/speckit.constitution

Context: Refactoring FlavorHub search.py into 4 clean modules.
Principles to capture:
1. Reliability — null-safe input validation
2. Architecture — 4 modules, each under 300 lines
3. Testability — >80% coverage, each module independently testable
4. Performance — fix caching memory leak, optimize filter ordering
5. Maintainability — remove 74 magic numbers and dead code
6. Quality Standards — tests + type hints
7. Observability & Operations — logging + guardrails
8. Deployment Safety — backward compatibility
```

> Spec Kit creates `.specify/constitution.md`.

---

**2.** Review `constitution.md`. It should define 4–5 principles every implementation decision must follow.

---

**3.** In Copilot Chat, run:

```
/speckit.specify

Break search.py into 4 modules following the constitution:
- validation_module.py: null-safe input handling, fixes the crash at line 447
- filtering_module.py: active filters only, remove deprecated code
- aggregation_module.py: ranking and caching, fix memory leak
- formatting_module.py: response formatting, remove legacy XML support
- Each module must be independently testable with >80% coverage.
- Maintain full API backward compatibility.
```

> Spec Kit creates `.specify/specification.md`.

---

**4.** Review `specification.md`. It defines **what** will be built — modules, responsibilities, and success criteria.

---

## Expected Output

`constitution.md`:
```
Mission: Transform 1006-line monolith into 4 clean modules

Principles:
  1. Modular Architecture  — 4 modules, each under 300 lines
  2. Reliability & Safety  — input validation, null-safe operations
  3. Clean Code Quality    — no dead code, fixed caching
  4. Quality Standards     — >80% test coverage, 100% type hints
  5. Deployment Safety     — backward-compatible API
```

`specification.md`:
```
4 Modules:
  1. validation_module.py  (~200 lines) — fixes NULL_DIETARY_BUG
  2. filtering_module.py   (~300 lines) — removes deprecated code
  3. aggregation_module.py (~250 lines) — fixes CACHE_LEAK_BUG
  4. formatting_module.py  (~150 lines) — removes legacy XML support

Success Criteria:
  - Each module under 300 lines
  - Both bugs fixed with regression tests
  - Test coverage above 80%
  - Existing API contracts unchanged
```

## What you Did
| Item | Description |
|------|-------------|
| Constitution | Defined the core principles guiding the refactor. |
| Specification | Created a detailed spec outlining the modules to be built and success criteria. |


