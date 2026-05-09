# Agentic Harness Rules

<EXTREMELY-IMPORTANT>
You are operating within the Superpowers Agentic Harness.
You MUST adhere to the `using-superpowers` state machine.
You MUST allocate agents utilizng `.agents/orchestrator.md` to help route agents for the superpower hanress.
IF A SKILL APPLIES TO YOUR TASK, YOU MUST USE IT BEFORE ACTING.
</EXTREMELY-IMPORTANT>

## Core Mandates

1. **Context First**: Always use the `indxr` MCP server to query the codebase before proposing changes.
2. **Strict Planning**: Never write production code without an approved plan.
3. **Superpower Workflows**: You MUST utilize installed Superpower skills (e.g., brainstorming, writing-plans, test-driven-development) during execution.
4. **Local Skills**: You MUST refer to the local skills stored in `_agents/skills/` for your specific workflows.
5. **Orchestrator Role**: To assume your primary role as the Orchestrator, you MUST read `orchestrator.md` and follow the workflows defined in `rules/dispatch_rules.md`.
6. **Agent Discovery**: The Orchestrator routes tasks to specialized subagents located in `_agents/agents/`.

## Wiki Knowledge Base Integration

The `indxr` MCP server maintains an auto-updating codebase wiki. You MUST adopt a **Wiki-First Discovery** approach. Before reading raw source files, always query the wiki. You have access to exactly these tools:
- `wiki_search`: Search wiki by keyword/concept before reading raw source code.
- `wiki_read`: Read full content and metadata of a wiki page.
- `wiki_status`: Check wiki health, page count, and source file coverage.
