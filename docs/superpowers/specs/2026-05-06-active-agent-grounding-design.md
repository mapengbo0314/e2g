# Design Document: Active Agent Grounding

**Status**: Finalized (Approved by User)
**Date**: 2026-05-06
**Topic**: Breaking the disconnect between generated artifacts and agent reasoning.

## 1. Problem Statement
The Harness initialization process generates local skills and DDD context files, but standard LLM tools do not automatically "absorb" these files upon startup. This creates a "Competency Illusion" where the workspace looks ready, but the agent operates without the specific guidance provided in those artifacts.

## 2. Proposed Solution
Inject explicit diagnostic and operational mandates into each agent's `config.yaml` to force active engagement with local artifacts at the start of a session.

### 2.1 Active Skill Discovery
Agents are commanded to physically list the local skills directory to ensure they know which tools are available.
- **Directive**: "You MUST run `list_directory` on `.gemini/skills/` at the start of your session to discover available local skills."

### 2.2 Active DDD Context Loading (Option A: Per Session)
Agents are commanded to read the Domain-Driven Design (DDD) context once per session to align their vocabulary.
- **Directive**: "At the beginning of any new session or task involving domain logic, you MUST use the `read_file` tool to load `.gemini/ddd/context.md`."

## 3. Implementation Details
The changes are localized to `harness/minting_engine.py`.

### 3.1 Template Updates
The `config_yaml_content` string will be updated to include the following prompt sections:
- **Core Mandates**: Includes the `list_directory` command for skills.
- **DDD Context**: Includes the `read_file` command for `context.md`.

## 4. Sphinch Marks (Readiness Assertions)
- [ ] Minted `config.yaml` contains the literal string "run `list_directory` on `.gemini/skills/`".
- [ ] Minted `config.yaml` contains the literal string "use the `read_file` tool to load `.gemini/ddd/context.md`".
- [ ] The paths in the mandates dynamically adapt to the user's platform choice (e.g., `.agents` vs `.gemini`).

## 5. Implementation Roadmap
1. Update `harness/minting_engine.py` string templates.
2. Verify via manual minting test.
