# Exercise 4: Spec Kit — Plan & Tasks

> **Time:** ~7 minutes
> **Prerequisite:** Spec Kit installed, `constitution.md` and `specification.md` created (`exercise-3.md`, `exercise-4.md`)
> **Track:** 🟢 Mandatory — Required for Exercise 5

---

> **Note for participants:** This exercise depends on the outputs of Exercises 3 and 4. The `plan.md` and `tasks.md` files generated here are referenced during implementation in Exercise 5.

---

## Goal

Create a technical plan for how the refactor will be executed, then break it into concrete trackable tasks.

---

## Context

The specification defines **what** to build. This exercise creates:
- `plan.md` — **how** to build it (migration sequence, interfaces, testing strategy)
- `tasks.md` — the actionable backlog with acceptance criteria

---

## Steps

**1.** In Copilot Chat, run:

```
/speckit.plan

Create a technical implementation plan for the 4-module refactor.
Detail:
- Module extraction sequence (minimize disruption to the running system)
- Interface design between modules
- Testing strategy per module
- Rollout approach: gradual (one module per phase)
```

> Spec Kit creates `.specify/plan.md`.

---

**2.** Review `plan.md`. It should outline a phased migration sequence.

---

**3.** In Copilot Chat, run:

```
/speckit.tasks

Generate actionable implementation tasks from the plan.
For each phase include:
- Clear task description
- Acceptance criteria
- Dependencies

Prioritize by: fix NULL_DIETARY_BUG first (highest user impact).
```

> Spec Kit creates `.specify/tasks.md`.

---

**4.** Review `tasks.md`. This is your implementation backlog.

---

## Expected Output

`plan.md`:
```
5-Phase Migration Plan:
  Phase 1 — Extract validation_module  (fixes NULL_DIETARY_BUG)
  Phase 2 — Extract filtering_module   (clean up deprecated code)
  Phase 3 — Extract aggregation_module (fixes CACHE_LEAK_BUG)
  Phase 4 — Extract formatting_module  (remove XML support)
  Phase 5 — Integration and cleanup
```

`tasks.md`:
```
Phase 1 — Validation Module (Priority: CRITICAL)
  Task 1.1: Create validation_module.py skeleton
            Acceptance: File exists, imports cleanly
  Task 1.2: Migrate null-check logic from search.py line 447
            Acceptance: NULL_DIETARY_BUG regression test passes
  Task 1.3: Add type hints and unit tests
            Acceptance: >80% coverage

  ... (continues for phases 2–5)

Total: 22 tasks across 5 phases
```

## What you Did
| Item | Description |
|------|-------------|
| Plan Creation | You created a technical plan outlining the migration sequence, interfaces, and testing strategy
| Task Generation | You generated a detailed backlog of implementation tasks with acceptance criteria. |


