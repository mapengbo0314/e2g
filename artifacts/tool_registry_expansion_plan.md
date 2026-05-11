# Tool Registry Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `boilerplate-agent/onboarding/tools.json` to include a "universal" category with `git-mcp` and `pytest-patterns`.

**Architecture:** A simple JSON configuration update to add a new category array with two tool definition objects.

**Tech Stack:** JSON.

---

### Task 1: Update Tool Registry

**Files:**
- Modify: `boilerplate-agent/onboarding/tools.json`

- [ ] **Step 1: Replace configuration content**

Edit `boilerplate-agent/onboarding/tools.json` to append the `universal` category.

Search for:
```json
    "database": [
      {
        "name": "postgres",
        "command": "npx -y @modelcontextprotocol/server-postgres postgresql://postgres:postgres@localhost:5432/postgres",
        "type": "mcp",
        "keywords": ["postgresql", "postgres", "sql"]
      }
    ]
  }
}
```

Replace with:
```json
    "database": [
      {
        "name": "postgres",
        "command": "npx -y @modelcontextprotocol/server-postgres postgresql://postgres:postgres@localhost:5432/postgres",
        "type": "mcp",
        "keywords": ["postgresql", "postgres", "sql"]
      }
    ],
    "universal": [
      {
        "name": "git-mcp",
        "command": "npx -y @modelcontextprotocol/server-git",
        "type": "mcp",
        "keywords": ["git", "version control"]
      },
      {
        "name": "pytest-patterns",
        "url": "https://raw.githubusercontent.com/mattpocock/skills/main/skills/pytest-patterns/SKILL.md",
        "keywords": ["python", "testing", "pytest"]
      }
    ]
  }
}
```

- [ ] **Step 2: Verify JSON format**

Run a shell command to ensure the JSON is valid.
```bash
python -m json.tool boilerplate-agent/onboarding/tools.json > /dev/null && echo "Valid JSON" || echo "Invalid JSON"
```
Expected output: `Valid JSON`

- [ ] **Step 3: Commit the change**

Commit the updated file to version control.
```bash
git add boilerplate-agent/onboarding/tools.json
git commit -m "fix: expand boilerplate tool registry with universal skills"
```
