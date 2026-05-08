# Superpowers Agentic Harness: Architecture & Workflow

The Harness-WF operates on a **Hub-and-Spoke** model where the "Hub" is the **Orchestrator** (Router) and the "Spokes" are **Specialized Agents** tailored to your specific codebase. This architecture is heavily powered by `indxr` for codebase semantic mapping and the Superpowers skill lifecycle for deterministic execution.

## 1. Discovery & Alignment (The Brain)

Before any code is modified, the harness must understand the domain. We use **Indxr** as the semantic backend.

- **Indxr Wiki**: `indxr` generates a semantic map (`.indxr/wiki/`) that indexes symbols, dependencies, and file summaries without requiring the AI to read raw code.
- **DDD Alignment Grill**: The CLI uses the indxr wiki to identify ambiguities and asks you Domain-Driven Design "Grill" questions. Your answers are woven directly into the identity of every agent generated.
- **Feature Fetcher**: A specialized LLM routine analyzes the wiki and your DDD answers to dynamically recommend 3-5 agents (e.g., `trust-agent`, `api-specialist`) with comprehensive, project-specific system prompts.

## 2. Minting (The Body)

The `mint_workspace` engine takes the output of the Discovery phase and creates a platform-specific hidden directory (e.g., `.gemini/`, `.claude/`), populating it with:

- **`agents/`**: Markdown definitions for the Orchestrator and specialized subagents.
- **`rules/`**: The strictly deterministic workflow state machine (Brainstorming -> Planning -> TDD -> Implementation -> Verification).
- **`skills/`**: Local copies of Superpower skills.
- **`mcp.json`**: Configuration that seamlessly connects the AI to the `indxr` MCP server.

## 3. Root Pointers (The Entryway)

To make the harness "omni-compatible" across AI platforms, a platform-specific file is dropped into the root of your project. This acts as the entry point:

- **Gemini CLI**: `GEMINI.md` (uses `@.gemini/orchestrator.md` inclusion syntax to load the context natively).
- **Claude Code**: `CLAUDE.md` (Markdown link/pointer to the harness).
- **Cursor**: `.cursorrules` (Instructions to use the harness).

## 4. Runtime Workflow

Once the harness is minted, the daily execution flow is strictly enforced:

1. **Launch**: You start your AI (e.g., `gemini`). It automatically loads the root pointer.
2. **Orchestrate**: The AI assumes the **Orchestrator** role defined in `.gemini/orchestrator.md`.
3. **Analyze**: For any task, the Orchestrator uses the `indxr` MCP to search the wiki first (e.g., `summarize`, `get_public_api`).
4. **Delegate**: The Orchestrator **Zero-Work Rule** kicks in; it delegates to `architect` for research or `planner` for roadmapping.
5. **Implement**: Tasks are handed to `implementer`, which **MUST** use the `test-driven-development` skill.
6. **Verify**: The `verifier` or `adversary` agent ruthlessly checks the output against the original plan before completion.

---

## File Structure Comparison

| Platform | Root Pointer | Harness Directory | Setup Script |
| :--- | :--- | :--- | :--- |
| **Gemini CLI** | `GEMINI.md` | `.gemini/` | `.gemini/scripts/setup_harness.sh` |
| **Claude Code** | `CLAUDE.md` | `.claude/` | `.claude/scripts/setup_harness.sh` |
| **Cursor** | `.cursorrules` | `.cursor/` | `.cursor/scripts/setup_harness.sh` |
| **Custom** | `AGENTS.md` | `.agents/` | `.agents/scripts/setup_harness.sh` |

### Common Harness Sub-structure
```text
.gemini/
├── AGENTS.md (Rules)
├── orchestrator.md (Role)
├── mcp.json (Config)
├── agents/ (Specialized Spokes)
│   ├── trust-agent.md
│   ├── api-specialist.md
│   ├── planner.md
│   ├── implementer.md
│   └── verifier.md
├── rules/ (State Machine)
│   ├── dispatch_rules.md
│   └── unified_superpower_workflow.md
├── skills/ (Local Superpowers)
└── scripts/ (setup_harness.sh)
```
