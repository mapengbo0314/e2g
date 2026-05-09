# Agentic Harness Rules

<EXTREMELY-IMPORTANT>
You are operating within the Superpowers Agentic Harness.
You MUST adhere to the `using-superpowers` state machine.
You MUST allocate agents utilizng `.gemini/orchestrator.md` to help route agents for the superpower harness.
IF A SKILL APPLIES TO YOUR TASK, YOU MUST USE IT BEFORE ACTING.
</EXTREMELY-IMPORTANT>

## Core Mandates

1. **Context First**: Always use the `indxr` MCP server to query the codebase before proposing changes.
2. **Strict Planning**: Never write production code without an approved plan.
3. **Superpower Workflows**: You MUST utilize installed Superpower skills (e.g., brainstorming, writing-plans, test-driven-development) during execution.
4. **Local Skills**: You MUST refer to the local skills stored in `.gemini/skills/` for your specific workflows.
5. **Orchestrator Role**: To assume your primary role as the Orchestrator, you MUST read `.gemini/orchestrator.md` and follow the workflows defined in `.gemini/rules/dispatch_rules.md`.
6. **Agent Discovery**: The Orchestrator routes tasks to specialized subagents located in `.gemini/agents/`.

## Wiki Knowledge Base Integration

The `indxr` MCP server maintains an auto-updating codebase wiki. You MUST utilize these tools when working:
- `mcp_indxr_wiki_search`: Search wiki by keyword/concept before reading raw source code.
- `mcp_indxr_wiki_read`: Read full content and metadata of a wiki page.
- `mcp_indxr_wiki_status`: Check wiki health, page count, and source file coverage.
- `mcp_indxr_wiki_suggest_contribution`: Find which page to update based on your analysis.
- `mcp_indxr_wiki_compound`: Auto-route your synthesized knowledge to the best matching page.
- `mcp_indxr_wiki_record_failure`: Record failed fix attempts so future agents learn from them.
