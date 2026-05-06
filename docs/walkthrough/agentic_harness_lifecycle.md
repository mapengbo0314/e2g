# The Universal Agentic Harness Lifecycle

This document provides a comprehensive walkthrough of the two distinct stages of the Universal Agentic Harness: **Stage 0: Bootstrap & Minting** and **Stage 1: Usage (The Developer Experience)**.

The harness acts as a strict state machine, enforcing best practices (like TDD and fresh indexing) while providing a specialized environment for AI agents to work within.

---

## Stage 0: Bootstrap & Minting (The "Factory Setup")

This stage occurs *before* any feature development begins. It creates the specialized workspace that the agents will operate in.

### 1. Initial Indexing
The human developer runs the repository indexing pipeline. This parses the codebase and generates an `indexing_bundle.json` along with a root-level `metadata.json` (which tracks the freshness of the index).

### 2. Feature Fetching & Discovery
The human invokes a discovery agent (e.g., the `feature-fetcher`).
*   **Input**: The agent reads the `indexing_bundle.json`.
*   **Action**: It analyzes the architecture and proposes 2-3 specialized agent profiles tailored to this specific project (e.g., "Auth-Expert", "Database-Specialist").

### 3. Minting the Workspace
The human approves the specialized agents and runs the cloning script to mint the workspace:
```bash
python boilerplate-agent/scripts/clone_harness.py new-feature-agents
```
*   **Platform Selection**: The script asks the user which AI platform they are using (Gemini CLI, Claude Code, etc.) to tailor the setup.
*   **Safe Cloning**: It copies the `boilerplate-agent` directory, stripping out caches, old logs, and git artifacts.
*   **Environment Audit**: The script scans the parent project for runtime markers (like `requirements.txt`, `.venv`, `package.json`) and outputs a checklist reminding the human to activate their environment.

---

## Stage 1: Usage (The Developer Experience)

With the specialized `new-feature-agents/` directory created, the human (let's call them Alex) enters it and begins feature development.

### Phase 1: Setup & Initialization
Alex navigates into the minted directory and activates the required environment.
```bash
cd new-feature-agents
source ../.venv/bin/activate  # (Based on the clone_harness.py reminder)
```
Alex launches the AI agent (e.g., `gemini`).

### Phase 2: Brainstorming (The Superpowers State Machine)
The harness enforces the `using-superpowers` state machine. The agent cannot write code yet.
*   **Human Input**: "I need to add a rate-limiter feature."
*   **Collaboration**: The agent asks clarifying questions.
*   **Approval**: The agent presents a short design document. Alex reviews and approves it.

### Phase 3: Planning & The Stale Index Gate
The agent attempts to transition to the Planning phase.
*   **Guardrail Hit (Stale Index)**: The `check_index_freshness.py` gate intercepts. It reads `metadata.json`. If the index is older than 7 days, it halts: *"ERROR: The indexing bundle is too old."*
*   **Recovery**: If blocked, Alex manually runs the indexer to refresh the context.
*   **Continuation**: With a fresh index, the agent writes a step-by-step implementation plan (`workspace/artifacts/plan.md`). Alex approves it.

### Phase 4: Execution & The Strict TDD Gate
The agent attempts to execute the plan.
*   **Guardrail Hit (Strict TDD)**: The agent tries to write production code. The harness intercepts it via `verify_tdd_gate.sh`. The gate checks `workspace/artifacts/tdd_failing_test.log`. If it's missing, empty, or older than the plan, execution is blocked.
*   **Pivot**: The agent writes a test file first.
*   **Human Action**: Alex runs the test (e.g., `pytest tests/test_feature.py`), sees it fail, and pastes the log into the chat.
*   **Unlock**: The gate confirms the log contains a failure signature (e.g., `FAILED`, `AssertionError`) and allows production coding to begin.

### Phase 5: Implementation & Verification
*   **Coding**: The agent implements the production code to satisfy the test.
*   **Verification**: Alex runs the test again. It passes. Alex pastes the success log.
*   **Wrap Up**: The agent performs a final code-quality review. Alex runs `git diff`. If it's correct, Alex commits the feature. If it spun out of control, Alex runs `git restore .` and restarts from the plan.

---

## Appendix A: Superpower Skill Mapping

The Agentic Harness is the "Engine" that drives the `using-superpowers` skills in a strictly deterministic order. Here is exactly where every skill fits into the lifecycle:

### Phase 1: Setup & Initialization
*   **`using-superpowers`**: The master gate. It forces the agent to check for relevant skills before every single turn.
*   **`using-git-worktrees`**: Creates a strictly isolated workspace for the current feature, ensuring zero contamination.

### Phase 2: Brainstorming
*   **`brainstorming`**: Forces the agent into a "No Code" dialogue to explore trade-offs, edge cases, and design patterns before a single line is written.

### Phase 3: Planning
*   **`writing-plans`**: Generates the component-level `workspace/artifacts/plan.md`.
*   **`subagent-driven-development`**: Breaks massive tasks into smaller, independent sub-tasks.
*   **`dispatching-parallel-agents`**: Runs multiple implementation threads at once for independent modules.

### Phase 4: Execution
*   **`test-driven-development`**: The strict Red-Green-Refactor mandate. Physically enforced by `verify_tdd_gate.sh`.
*   **`executing-plans`**: Tracks progress through the `plan.md` checklist.
*   **`systematic-debugging`**: Triggered if tests fail unexpectedly, providing a scientific method for recovery.

### Phase 5: Verification & Wrap-up
*   **`verification-before-completion`**: Forbids the agent from declaring success without executing the full test suite.
*   **`requesting-code-review`**: Prepares the PR and initiates the adversarial review.
*   **`receiving-code-review`**: Protocol for handling feedback securely.
*   **`finishing-a-development-branch`**: Handles squashing, artifact cleanup, and the final merge.

### Stage 0 (Meta Skills)
*   **`skill-creator` / `writing-skills`**: Used during Factory Setup if a project requires a bespoke skill (e.g., a custom database migration protocol).

---

## Appendix B: Quick Start Guide (Setting up ANY Repo)

Want to use the Universal Agentic Harness in a brand new, completely unrelated project (like a React web app or a Rust CLI)? Here is the exact setup sequence.

### Prerequisites
Assume your codebase is located at `/path/to/my-awesome-project`.
Assume the `boilerplate-agent` directory lives somewhere on your machine (e.g., `~/tools/boilerplate-agent`).

### Step 1: Generate the Index
The harness needs to know what your code looks like.
1. Navigate to your project: `cd /path/to/my-awesome-project`
2. Run your indexer to generate `indexing_bundle.json` and the `metadata.json`.
3. *(The `metadata.json` will be used to enforce the 7-day freshness gate).*

### Step 2: Discover & Generate Agents
Use the newly created index to generate specialized experts for your project.
1. Launch your AI and invoke the discovery agent (e.g., using Gemini CLI):
   ```bash
   gemini "@feature-fetcher Please analyze the workspace/artifacts/indexing_bundle.json and recommend 2-3 specialized agents for this repo."
   ```
2. The agent reads the index, identifies your architecture (e.g., React, Python API), and proposes tailored agent profiles.
3. Approve the suggestions, and the agent will physically generate the `config.yaml` and `agent.json` definitions for these new experts.

### Step 3: Mint the Harness Workspace
Do not let the AI loose in your root directory. Mint a specialized workspace for these newly created agents to live in.
1. Run the clone script, pointing it at a new directory name:
   ```bash
   python ~/tools/boilerplate-agent/scripts/clone_harness.py .agents
   ```
2. The script will ask what AI platform you use (e.g., Gemini CLI).
3. The script will detect your project type (e.g., `package.json`) and remind you to run your environment setup (like `npm install`).

### Step 4: Enter the Harness
1. Navigate into the isolated workspace: `cd .agents`
2. Activate your environment: `nvm use` or `source .venv/bin/activate`
3. Launch your AI: `gemini`

### Step 5: Build Features
You are now in the Harness. 
* Tell the AI: *"I need to build a new login component."*
* The Harness will immediately force the AI into the **Brainstorming** phase.
* When it tries to write code, it will hit the **TDD Gate**.
* You are now developing with 100% verified, strictly-planned execution.
