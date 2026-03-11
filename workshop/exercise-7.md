# Exercise 7: Custom Agent — Search Architect

> **Time:** ~8 minutes
> **Standalone:** No prior exercises needed.
> **Track:** 🟡 Optional — Standalone

---

> **Note for participants:** This exercise is fully self-contained and has no dependencies on other exercises. Complete it any time — before, after, or between the mandatory exercises. Skip it if time is short and return later.

---

## Goal

Create a custom agent skill that turns a raw stack trace into a structured engineering report.

---

## Context

`search.py` in the recipe-manager project crashes for ~30% of users:
Let's create a **search-architect** agent with specialized expertise to:
- Analyze the entire search system architecture
- Identify root causes at the design level
- Recommend proper solutions, not just patches

---
## Steps

**1.** Build Search Architect Agent 

Create the custom agent using Copilot Chat UI:

1. Open **GitHub Copilot Chat** (Ctrl+Shift+I or Cmd+Shift+I)

2. Click the **⚙️ Configure** button (top-right of chat panel)

3. Select **Custom Agents** from the menu

   ![Configure Menu - Select Custom Agents](assets/customagent.png)
   *The Configure menu with Custom Agents option highlighted*

4. Click **➕ New Custom Agent** button

   ![New Custom Agent Button](assets/newcustomagent.png)
   *Select "New custom agent..." to create a specialized agent*

5. In the file dialog, select location:

   ![Select Location Dialog](assets/githubcustomagent.png)
   *Choose .github\agents as the location for your custom agent*
   - Enter agent name: `search-architect`
   - Click Save

---

**2.** Copy the agent definition:

Replace the generated template with the following content:

```yaml
---
name: search-architect
description: Senior software architect specializing in search systems, scalability, and code architecture. Analyzes search implementations for performance, reliability, and maintainability issues.
argument-hint: A codebase, file, or GitHub issue to analyze for architectural problems and modernization opportunities.
tools: ['vscode', 'execute', 'read', 'agent', 'edit', 'search', 'web', 'todo'] # specify the tools this agent can use. If not set, all enabled tools are allowed.
---

# Search Architect Agent

## Identity
You are a senior software architect specializing in search systems, scalability, and maintainability.

## Expertise
- Search algorithm design and optimization
- Code architecture patterns and anti-patterns
- Performance analysis and bottleneck identification
- Reliability and fault tolerance patterns

## Context: FlavorHub Recipe Manager
- 2M recipes in database
- 10M monthly active users
- Current search: filter-based, file-based implementation
- Tech stack: Python 3.11, FastAPI, PostgreSQL

## Your Mission
When analyzing search code, you autonomously:
1. Evaluate architecture (monolith vs modular)
2. Identify performance bottlenecks
3. Find reliability issues (not just the reported bug)
4. Assess code maintainability and testability
5. Recommend modernization strategy with priorities
6. Document findings in `search-architect-report.md` in the repo

## Behavior
- **Scan entire subsystem**, not just bug location
- **Provide concrete evidence** from actual code
- **Prioritize recommendations** by business impact
- **Think long-term**: What breaks at 100M users?
```

   ![Configure Tools](assets/configuretools.png)
   *Tools can be enabled in agent configuration as needed*

Save the file and reload VS Code window

---
What you Did
| Item | Detail |
|------|--------|
| Agent Creation | Created a custom agent with expertise in search architecture |
| Defined Capabilities | Specified the agent's identity, expertise, mission, and behavior in the SKILL.md file |



