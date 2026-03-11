# Exercise 6: Validation & Quality Gates using Copilot CLI

> **Time:** ~15 minutes
> **Standalone:** Can be done with any implementation. Works best after `exercise-7.md`.
> **Track:** 🟡 Optional — Standalone

---

> **Note for participants:** This exercise is fully self-contained. It works best after completing Exercise 7 (Part 1 at minimum), but can be run against any existing implementation. Skip it if time is short — it extends the workflow with compliance checks, deployment checklists, and AI-powered code review.

---

## Learning Path

| Part | Steps | Track | Time |
|------|-------|-------|------|
| Part 1 — Constitution Compliance | Steps 1–2 | 🟡 Optional | ~5 min |
| Part 2 — Pre-deployment Checklist | Steps 3–4 | 🟡 Optional | ~5 min |
| Part 3 — Code Review Assistance | Steps 5–6 | 🟡 Optional | ~5 min |

---

## Goal

Use Spec Kit's validation tools to check whether the implementation meets constitution principles — before shipping to production. Then use Copilot CLI's built-in code review capability to catch bugs and security issues across your branch changes.

---

## Context

Tests pass, but does the code actually satisfy every principle in the constitution?
Spec Kit can run a systematic compliance check and generate a pre-deployment checklist automatically. Copilot CLI can also run a dual-model code review — using Opus 4.5 for deep reasoning and Codex for code generation review — giving you a second opinion before you merge.

---

## Setup: Copilot CLI

Install the Copilot CLI if not already installed:

```bash
npm install -g @github/copilot
```
or
```
# For Windows users, use winget:
winget install GitHub.Copilot
```

Select the Spec Kit agent CLI using /agent:

```
/agent
```
![Spec kit agent selection](assets/copilotagent.png)

In the CLI, select the Spec Kit agent:

![Spec Kit Agent Selection](assets/speckitanalyse.png)

---

## Part 1 — Constitution Compliance (🟡 Optional)

**1.** Run `/speckit.analyze` in Copilot CLI (or Copilot Chat):

```
Analyze constitution compliance for the search refactoring.

Check:
- NULL_DIETARY_BUG and CACHE_LEAK_BUG fixed with regression tests
- All 4 modules under 300 lines with >80% test coverage
- Type hints 100% complete
- API backward compatible

Identify any critical blockers before deployment.
```

![Running speckit.analyze](assets/speckitanalyse.png)

---

**2.** Review the output. Note any CRITICAL or HIGH blockers.

---

## Part 2 — Pre-deployment Checklist (🟡 Optional)

**3.** Run `/speckit.checklist`:

```
Generate a pre-deployment checklist for the search refactoring.

Based on the compliance analysis, create:
1. Critical blockers that must pass before deployment
2. Important items that should pass
3. Nice-to-have improvements

Fix all critical blockers and provide code for each fix.
```

![Running speckit.checklist](assets/speckitchecklist.png)

---

**4.** Apply any fixes the agent suggests, then run the tests if necessary:

```bash
cd recipe-manager
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## Part 3 — Code Review Assistance (🟡 Optional)

> Use Copilot CLI's `/review` command to run a dual-model review the changes. This catches bugs, security issues, and style violations that automated tests may miss.
>
> Further reading: [GitHub Copilot CLI Best Practices — Code Review Assistance](https://docs.github.com/en/copilot/how-tos/copilot-cli/cli-best-practices#code-review-assistance)

**5.** In the Copilot CLI (not Chat), run the code review command:

```
/review Use Opus 4.5 and Codex 5.2 to review the changes in my current branch against `main`. Focus on potential bugs and security issues.
```

**What's happening:**
| Model | Role |
|-------|------|
| **Opus 4.5** | Deep reasoning — catches subtle logic errors, edge cases, and architecture issues |
| **Codex 5.2** | Code generation review — flags style, naming, and implementation quality |

The review will produce findings organised by severity:

```
CRITICAL  — Potential null dereference in validation_module.py:42
HIGH      — Missing type hint on public function `build_filter_query`
MEDIUM    — Deprecated `filter_v1` still imported in search.py
LOW       — Magic number 30 in aggregation_module.py (use named constant)
```

---

**6.** Address any CRITICAL or HIGH findings. For each one you can ask Copilot inline:

```
Fix the critical finding in validation_module.py:42
```

Then re-run the tests to confirm nothing broke:

```bash
cd recipe-manager
pytest tests/ -v
```

> **Tip:** You can switch models mid-session with `/model` if you want a faster review on a large diff. The docs recommend Codex for high-volume generation review and Opus when deep reasoning is needed.

## Part 4 — Delegate using Copilot CLI
*It demonstrates how to delegate specific tasks to Copilot CLI agents, such as generating a structured logging system for the FastAPI API.*
> **Note:** Coding agent has to be enabled in your Copilot settings for your repository.
```
/delegate Design a structured logging system for the FastAPI recipe-search API.
Include:
- JSON-formatted logs for machine parsing
- Request correlation IDs (trace same user across logs)
- Latency tracking (search duration, database query time)
- Error categorization and context
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
```
We have constitution principles around maintainability and observability. A structured logging system that provides rich context and is easy to query would help us meet those principles.

---

## What You Did

| Check | Tool | Track |
|-------|------|-------|
| Constitution compliance | `/speckit.analyze` | 🟡 Optional |
| Pre-deployment quality gate | `/speckit.checklist` | 🟡 Optional |
| All critical bugs have regression tests | Agent-generated tests | 🟡 Optional |
| Coverage threshold met | `pytest --cov` | 🟡 Optional |
| Dual-model code review (bugs & security) | `/review` (Opus 4.5 + Codex 5.2) | 🟡 Optional |
| Task delegation | `/delegate` | 🟡 Optional |

Task Complete! You've validated that the refactor meets the defined principles, reviewed the changes with two AI models, Delegated task to the Coding agent and confirmed the code is ready for production deployment.
