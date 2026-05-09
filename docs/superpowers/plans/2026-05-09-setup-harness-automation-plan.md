# Setup Harness Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automate the installation of the 'superpowers' extension and 'mattpocock/skills' within the `setup_harness.sh` script, prioritizing non-interactive local (workspace) installation where supported.

**Architecture:** We will replace the manual installation echoes with non-interactive `gemini extensions install` (global scope, using `--consent`) and `gemini skills install` (workspace scope, using `--consent`). We append `|| true` to ensure the script does not halt on network or installation failures, allowing subsequent steps (like MCP configuration) to proceed.

**Tech Stack:** Bash, Gemini CLI

---

### Task 1: Update setup_harness.sh with Installation Commands

**Files:**
- Modify: `.gemini/scripts/setup_harness.sh`

- [ ] **Step 1: Replace manual instructions with automated commands**

Modify `.gemini/scripts/setup_harness.sh`. Replace the current installation section with the automated commands.

```bash
sed -i '' 's/gemini extensions install https:\/\/github.com\/obra\/superpowers || true/gemini extensions install https:\/\/github.com\/obra\/superpowers --consent || true/g' .gemini/scripts/setup_harness.sh
sed -i '' 's/gemini extensions install https:\/\/github.com\/mattpocock\/skills || true/gemini skills install https:\/\/github.com\/mattpocock\/skills --scope workspace --consent || true/g' .gemini/scripts/setup_harness.sh
```
*Note: We are replacing the `extensions install` for mattpocock with `skills install`.*

- [ ] **Step 2: Verify the file modifications**

Run: `cat .gemini/scripts/setup_harness.sh`
Expected: You should see the updated `gemini extensions install` and `gemini skills install` commands with the `--consent` flags and correct scopes.

- [ ] **Step 3: Test the setup script**

Run: `bash .gemini/scripts/setup_harness.sh`
Expected: The script executes without prompting for user input and outputs the installation progress. It should not fail.

- [ ] **Step 4: Commit**

```bash
git add .gemini/scripts/setup_harness.sh
git commit -m "chore: automate skill and extension installation in setup script"
```
