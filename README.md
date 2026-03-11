# Agent-Driven Spec Development: The FlavorHub Crisis

> **Production Emergency:** Fix a critical bug and modernize the system using GitHub agents.

## The Crisis

**Monday, 3:00 PM.** FlavorHub's search feature is crashing for 30% of users.
500+ error reports. CTO demands a fix AND a lasting solution.

This workshop walks you through exactly that — using GitHub's agent ecosystem to go from chaos to production-ready.

---

## What You'll Learn

| Tool | What You Do |
|------|-------------|
| **Agent Skills** | Diagnose production errors automatically |
| **Custom Agents** | Build specialist agents with domain expertise |
| **Spec Kit** | Drive governance, planning, and code generation from a specification |
| **Copilot CLI** | Run compliance checks and quality gates |
| **GitHub MCP** | Integrate agents directly into your repo for continuous improvement |

---

## Prerequisites

- **Python 3.11+** installed  
- **Valid GitHub Copilot subscription** (Individual, Business, or Enterprise)
- [VS Code](https://code.visualstudio.com/download) with GitHub Copilot Chat extension
- [Git CLI](https://git-scm.com/install/) for version control  
- [Speckit](https://github.com/github/spec-kit?tab=readme-ov-file#-get-started) installed and configured
- [Copilot CLI](https://github.com/features/copilot/cli)
- [GitHub CLI](https://cli.github.com/) for MCP interactions 
- [Node.js 18+](https://nodejs.org/en/download) (for Copilot CLI)  
- [GitHub MCP](https://github.com/github/github-mcp-server?tab=readme-ov-file)
- [Python 3.11+](https://www.python.org/downloads/) (for running the recipe-manager app)
- [UV](https://docs.astral.sh/uv/getting-started/installation/) (for installing Spec Kit)

> **Starter Code Provided:** FlavorHub Recipe Manager brownfield application with intentional issues for learning

---

## Workshop Structure

The workshop is designed with **flexible learning paths**:

### 🟢 Mandatory Core Path (~29 minutes)
Complete this path to experience the full Spec Kit workflow — from bug reproduction to a working fix:

| Step | Exercise | Topic | Time |
|------|----------|-------|------|
| 1 | [Exercise 1 — Part 1](workshop/exercise-1.md#part-1--reproduce-the-bug--mandatory) | Reproduce the Bug | ~2 min |
| 2 | [Exercise 2](workshop/exercise-2.md) | Spec Kit Setup | ~5 min |
| 3 | [Exercise 3](workshop/exercise-3.md) | Constitution & Specification | ~8 min |
| 4 | [Exercise 4](workshop/exercise-4.md) | Plan & Tasks | ~7 min |
| 5 | [Exercise 5 — Part 1](workshop/exercise-5.md#part-1--implement-validation-module--mandatory) | Implement Validation Module | ~7 min |
| — | **Total** | **Everyone should complete this** | **~29 min** |

### 🟡 Optional Exploration (~38 minutes)
Explore these exercises in any order. They are fully self-contained with no dependencies on each other:

| Exercise | Topic | Time | Focus |
|----------|-------|------|-------|
| [Exercise 1 — Part 2](workshop/exercise-1.md#part-2--create-issue-analyzer-skill--optional) | Issue Analyzer Skill | ~3 min | Error diagnosis |
| [Exercise 5 — Part 2](workshop/exercise-5.md#part-2--remaining-modules--optional) | Implement Remaining Modules | ~5 min | Complete refactor |
| [Exercise 6](workshop/exercise-6.md) | Validation & Quality Gates + Code Review | ~15 min | Pre-deployment checks |
| [Exercise 7](workshop/exercise-7.md) | Custom Agent — Search Architect | ~8 min | Domain expertise |
| [Exercise 8](workshop/exercise-8.md) | Agent Skills — GitHub MCP | ~7 min | Issue automation |

> **Pro Tip:** Complete the mandatory core path first (~29 min), then pick optional exercises based on what interests you most. If time is short, you can revisit them after the workshop.

---
> The workshop has been tested with the following AI models on GitHub Copilot: `Claude Sonnet 4.6`, `GPT-5.3-codex`. Results may vary with different models. If you encounter issues, try switching to one of these models in your Copilot settings.

---

## Get Started

[![Use this Template](https://img.shields.io/badge/Use%20this%20Template-%E2%86%92-1f883d?style=for-the-badge&logo=github&labelColor=197935)](https://github.com/new?template_owner=CanarysAutomations&template_name=speckit-and-beyond&owner=%40me&name=speckit-and-beyond&description=Agent-Driven+Spec+Development:+The+FlavorHub+Crisis&visibility=public)

Once your repo is created, start here: [Exercise 1 — Reproduce the Bug](workshop/exercise-1.md)

## Resources

- [Spec Kit Documentation](https://github.github.io/spec-kit/)
- [GitHub Repository](https://github.com/github/spec-kit)
- [Video Overview](https://www.youtube.com/watch?v=a9eR1xsfvHg)
- [GitHub Copilot CLI Best Practices](https://docs.github.com/en/copilot/how-tos/copilot-cli/cli-best-practices)
