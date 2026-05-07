# Agent Format Reference

## Gemini CLI Format (Strict)

The Gemini CLI uses a strict YAML frontmatter schema for its agent definition `.md` files.

**Allowed Keys in Frontmatter:**
- `name`: Must be a valid URL-safe slug (e.g., `architecture-deepener`, NOT `ArchitectureDeepener` or `architecture_deepener`).
- `description`: A brief description of the agent's role and capabilities.
- `tools`: (Optional) An array of tools the agent has access to.

**Invalid Keys:**
Keys like `skills`, `related_agents`, or arbitrary metadata will cause validation errors upon parsing (e.g., `Unrecognized key(s) in object: 'skills', 'related_agents'`).

**Metadata Placement:**
Any additional metadata that provides context but is not part of the strict schema must be moved into the markdown body, ideally under a `## Metadata` section at the end of the file.

### Example Gemini CLI Format
```markdown
---
name: architecture-deepener
description: The specialized tool for codebase analysis and architectural mapping.
---
# Core Mandates
You are an architectural analysis agent...

## Metadata
**Skills:** architecture, analysis
**Related Agents:** implementer, reviewer
```

---

## Claude Code Format (Comparison)

Claude Code often accepts a looser YAML frontmatter schema or parses metadata differently depending on the specific project configuration.

- **Naming:** Often allows CamelCase, TitleCase, or strings with spaces as names.
- **Custom Keys:** Typically ignores unrecognized frontmatter keys or passes them through as extended configuration (e.g., accepting `skills` or `related_agents` natively in the frontmatter without throwing errors).
- **Tools:** May use different structures or naming conventions for tools compared to Gemini CLI.

For cross-compatibility or when migrating agents to Gemini CLI, the strict schema must be followed. All non-standard keys must be extracted and placed into the markdown content.