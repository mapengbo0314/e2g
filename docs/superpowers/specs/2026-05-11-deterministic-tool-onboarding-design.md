# Design Spec: Deterministic Onboarding Tool Injection

## Goal
Ensure that specific tools (like Playwright Interactive skill and MCP) are automatically included in the `ONBOARDING_DOMAIN.md` for projects matching certain tech stack keywords (e.g., "frontend").

## Proposed Changes

### 1. `boilerplate-agent/onboarding/tools.json`
Update the schema to include a `force_if_keywords` property.
- Add `playwright-interactive` skill.
- Add `playwright` MCP.
- Mark both with `force_if_keywords: ["frontend"]`.

### 2. `harness/discovery_engine.py`
Modify `generate_onboarding_domain_doc` to:
- Identify "forced" tools by checking if any value in `force_if_keywords` matches the detected `tech_stack` (substring match).
- Ensure these tools are included in `recommended_skills` and `recommended_mcps` regardless of LLM output.
- Avoid duplication if the LLM also recommends them.

## Success Criteria
- Running the harness on a project with "package.json" (Node.js) results in an `ONBOARDING_DOMAIN.md` that contains the Playwright skill and MCP by default.
- Non-frontend projects do NOT include these tools unless the LLM recommends them for other reasons.

## Trade-offs
- **Pros**: Deterministic, scalable, easy to add new "mandatory" tools.
- **Cons**: Slightly more complex selection logic in the discovery engine.
