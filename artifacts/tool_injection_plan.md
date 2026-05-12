# Deterministic Onboarding Tool Injection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically include Playwright Interactive skill and MCP in `ONBOARDING_DOMAIN.md` for frontend projects via a `force_if_keywords` field in `tools.json`.

**Architecture:** Enhance the tools registry with a `force_if_keywords` property and update the discovery engine to deterministically inject tools that match the detected tech stack.

**Tech Stack:** Python, JSON

---

### Task 1: Update Tools Registry

**Files:**
- Modify: `boilerplate-agent/onboarding/tools.json`

- [x] **Step 1: Add Playwright Interactive skill and update MCP entry**
Update `tools.json` to include the `playwright-interactive` skill and add `force_if_keywords` to both Playwright entries.

```json
{
  "categories": {
    "frontend": [
      {
        "name": "nextjs",
        "url": "https://raw.githubusercontent.com/PatrickJS/awesome-cline-prompts/main/prompts/nextjs.md",
        "keywords": ["react", "nextjs", "next.js", "frontend"]
      },
      {
         "name": "playwright",
         "command": "npx -y @modelcontextprotocol/server-playwright",
         "type": "mcp",
         "force_if_keywords": ["frontend"],
         "keywords": ["react", "nextjs", "frontend", "vue", "svelte"]
      },
      {
         "name": "playwright-interactive",
         "url": "https://github.com/openai/skills/blob/main/skills/.curated/playwright-interactive/SKILL.md",
         "type": "skill",
         "force_if_keywords": ["frontend"],
         "keywords": ["react", "nextjs", "frontend", "vue", "svelte"]
      }
    ],
    ...
  }
}
```

- [x] **Step 2: Commit**
```bash
git add boilerplate-agent/onboarding/tools.json
git commit -m "feat(discovery): add force_if_keywords to tools registry for playwright"
```
