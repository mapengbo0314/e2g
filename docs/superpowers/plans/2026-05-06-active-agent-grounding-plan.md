# Active Agent Grounding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Inject explicit diagnostic and operational mandates into the minted agent `config.yaml` to ensure they actively discover local skills and read DDD context at the start of every session.

**Architecture:** Modifying the string templates in `harness/minting_engine.py` that generate the agent `config.yaml` content.

**Tech Stack:** Python 3.11+, String templates.

---

### Task 1: Update Agent Config Templates in Minting Engine

**Files:**
- Modify: `harness/minting_engine.py`

- [ ] **Step 1: Update Core Mandates template**

Locate the `config_yaml_content` string and update the `Core Mandates` prompt section.

```python
# OLD
        config_yaml_content = f"""coding_agent: true
agentic_mode: true
# Load the full brain from the generated markdown file
system_prompt_file: system_prompt.md
prompt_section_customization:
  add_prompt_sections:
  - prompt_section:
      title: Core Mandates
      content: |
        You are a specialized subagent operating within this repository's agent ecosystem.
        You have been delegated a specific task by the Orchestrator.
        1. Security & System Integrity: Protect secrets.
        2. Context Efficiency: Be strategic in tool usage.
        3. Superpower Workflows: You MUST utilize local skills from `{target_path.name}/skills/`.
    insert_before_sections: artifacts
...
"""

# NEW
        config_yaml_content = f"""coding_agent: true
agentic_mode: true
# Load the full brain from the generated markdown file
system_prompt_file: system_prompt.md
prompt_section_customization:
  add_prompt_sections:
  - prompt_section:
      title: Core Mandates
      content: |
        You are a specialized subagent operating within this repository's agent ecosystem.
        You have been delegated a specific task by the Orchestrator.
        1. Security & System Integrity: Protect secrets.
        2. Context Efficiency: Be strategic in tool usage.
        3. Superpower Workflows: You MUST run `list_directory` on `{target_path.name}/skills/` at the start of your session to discover available local skills.
    insert_before_sections: artifacts
...
"""
```

- [ ] **Step 2: Update DDD Context template**

Locate the `ddd_section` string and update the `Domain-Driven Design (DDD) Context` prompt section.

```python
# OLD
        if ddd_context:
            ddd_section = f"""  - prompt_section:
      title: Domain-Driven Design (DDD) Context
      content: |
        This project uses Domain-Driven Design principles.
        You MUST refer to the following DDD documentation in the `.gemini/ddd/` directory:
        - `context.md`: Defines the core domain terms and their meanings.
        - `translation_map.json`: Maps domain concepts to implementation details.
        
        Ensure your implementation aligns with these definitions.
    insert_after_sections: 'Role: {agent["name"]}'"""

# NEW
        if ddd_context:
            ddd_section = f"""  - prompt_section:
      title: Domain-Driven Design (DDD) Context
      content: |
        This project uses Domain-Driven Design principles.
        At the beginning of any new session or task involving domain logic, you MUST use the `read_file` tool to load `{target_path.name}/ddd/context.md`.
        
        You MUST refer to the following DDD documentation:
        - `context.md`: Defines the core domain terms and their meanings.
        - `translation_map.json`: Maps domain concepts to implementation details.
        
        Ensure your implementation aligns with these definitions.
    insert_after_sections: Core Mandates"""
```

- [ ] **Step 3: Commit**

```bash
git add harness/minting_engine.py
git commit -m "feat: inject active grounding mandates into agent config templates"
```

### Task 2: Manual Verification

**Files:**
- Manual Test

- [ ] **Step 1: Run Harness Init on a test directory**

Run: `python -m harness.cli init --project-path ./test_workspace --llm gemini --ddd`
(Answer the interactive prompts)

- [ ] **Step 2: Verify generated config.yaml**

Check `test_workspace/.gemini/agents/specialized/<any_agent>/config.yaml`.
Verify it contains the `list_directory` and `read_file` directives with the correct paths.

- [ ] **Step 3: Verify GEMINI.md in root**

Check `test_workspace/GEMINI.md`.
Verify it contains the `<EXTREMELY-IMPORTANT>` section.

- [ ] **Step 4: Cleanup**

Run: `rm -rf test_workspace`

- [ ] **Step 5: Final Push**

```bash
git push origin main
```
