# Implementation Plan: Dynamic Dispatch Rules for DDD Agents

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modify the `minting_engine.py` to inject the dynamically discovered DDD agents into the `dispatch_rules.md` file during the workspace generation process.

**Architecture:** We will intercept the content replacement loop inside `mint_workspace` within `minting_engine.py`. When processing the `dispatch_rules.md` file, we will dynamically append a new routing rule referencing the `selected_agents` list just before the "**Negative Routing Rules**" section. This will instruct the Orchestrator to use these custom agents.

**Tech Stack:** Python

---

### Task 1: Update minting_engine.py to inject DDD agents

*   **Files:**
    *   Modify: `harness/minting_engine.py:100-110` (approximate lines)

*   [x] **Step 1: Write the failing test (Not applicable here, modifying existing logic)**
    *   *The test for `test_minting_engine.py` is passing with the updated logic.*

*   [x] **Step 2: Run test to verify it fails (Not applicable)**

*   [x] **Step 3: Write minimal implementation**
    I have already applied this change to `harness/minting_engine.py`:
    ```python
                        # Apply specialized agents injection specifically for dispatch_rules.md
                        if file == "dispatch_rules.md" and selected_agents:
                            agent_names = [agent['name'] for agent in selected_agents]
                            agents_str = ", ".join([f"`@{name}`" for name in agent_names])
                            injection = f"\n- **Domain Specific Routing**: You MUST delegate domain-specific tasks to the newly minted specialized agents: {agents_str}. Refer to their markdown files in the agents directory for their specific mandates.\n"
                            
                            # Inject right before the Negative Routing Rules section
                            if "**Negative Routing Rules" in new_content:
                                new_content = new_content.replace("**Negative Routing Rules", injection + "**Negative Routing Rules")
    ```

*   [x] **Step 4: Run test to verify it passes**
    Run: `PYTHONPATH=. pytest tests/test_minting_engine.py`
    Expected: PASS (Already verified)

*   [ ] **Step 5: Commit**

    ```bash
    git add harness/minting_engine.py
    git commit -m "feat(minting): inject DDD agents into dispatch rules during workspace generation"
    ```
