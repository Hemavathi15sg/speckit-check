# Exercise 5: Spec Kit — Implement

> **Time:** ~10 minutes
> **Prerequisite:** Spec Kit initialized, `specification.md` and `plan.md` created (`exercise-4.md`)
> **Track:** 🟢 Mandatory — Part 1 | 🟡 Optional — Part 2

---

## Learning Path

| Part | Steps | Track | Time |
|------|-------|-------|------|
| Part 1 — Implement Validation Module | Steps 1–3 | 🟢 Mandatory | ~7 min |
| Part 2 — Remaining Modules | Step 4 | 🟡 Optional | ~5 min |

> **Mandatory participants:** Complete Steps 1–3. Part 2 extends the same pattern to the other 3 modules — do it if time allows.

---

## Goal

Use `/speckit.implement` to generate the validation module that fixes the null crash, wire it into the existing codebase, and verify the fix.

---

## Context

Highest priority task: fix the `NULL_DIETARY_BUG`  by extracting input validation into a dedicated `validation_module.py`.

---

## Part 1 — Implement Validation Module (🟢 Mandatory)

**1.** In Copilot Chat, run:

```
/speckit.implement

Implement validation_module.py following the specification and plan.
Requirements:
- Fix the NULL_DIETARY_BUG
- Add input validation for all search parameters
- Full type hints
- Unit tests with >80% coverage
- Importable by search.py without breaking the existing API

Reference: tasks.md Phase 1
```

> Copilot generates `validation_module.py` and a corresponding test file.

---

**2.** Wire the new module into `search.py` using @workspace:

```
@workspace
I have created validation_module.py.
Update search.py to import and use it instead of the inline logic at line 447.
Make sure api/routes.py continues to work without any changes.
```

---

**3.** Run the tests to confirm the fix:

```bash
cd recipe-manager
python test_bug.py
```

Expected:

```
Testing with Alice (has dietary restrictions)...
Search succeeded!

Testing search with user who has dietary_restrictions=None...
Search succeeded!   ← NULL_DIETARY_BUG is now fixed

Testing with Bob (SAMPLE_USERS[1])...
Search succeeded!
```

---

## Part 2 — Remaining Modules (🟡 Optional)

> Repeat the same implement-and-wire pattern for the 3 remaining modules if time allows.

**4.** Repeat for the remaining modules using the same prompt pattern:

```
/speckit.implement

Implement filtering_module.py following the specification and plan.
Requirements:
- Extract all active filter functions from search.py
- Remove the 3 deprecated filter versions
- Unit tests for each filter function
- Same function signatures for backward compatibility

Reference: tasks.md Phase 2
```

Use the same approach for `aggregation_module.py` (Phase 3) and `formatting_module.py` (Phase 4).



## What You Did

| Item | Detail |
|------|--------|
| Validation Module | Implemented and integrated validation_module.py to fix the null crash |
| Remaining Modules | (Optional) Implemented filtering, aggregation, and formatting modules following the same pattern |


