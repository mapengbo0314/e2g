# Design Spec: Tool Registry Expansion

## Overview
Update the boilerplate tool registry to include universal tools that are applicable across various development contexts, starting with `git-mcp` and `pytest-patterns`.

## Requirements
- Add a new "universal" category to `boilerplate-agent/onboarding/tools.json`.
- Include `git-mcp` (MCP server for Git) in the universal category.
- Include `pytest-patterns` (Skill for Pytest) in the universal category.
- Exclude `using-superpowers` from this registry as it is handled by the engine.

## Proposed Changes
### Configuration Update
Modify `boilerplate-agent/onboarding/tools.json` to add the `universal` key under `categories`.

```json
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
```

## Verification Plan
1. **JSON Validation**: Ensure the resulting file is valid JSON.
2. **Schema Check**: Confirm the "universal" category exists and contains the two new entries.
3. **Commit Verification**: Confirm the change is committed with the specific message: "fix: expand boilerplate tool registry with universal skills".
