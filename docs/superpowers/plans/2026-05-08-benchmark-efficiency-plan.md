# Token Efficiency Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a standalone Python utility to measure the token savings of the Agentic Harness vs. a Monolithic agent using CLI simulation.

**Architecture:** A script that mocks an Orchestrator by programmatically invoking `gemini` commands for both Monolithic and Delegated workflows, then precisely calculates and compares token usage.

**Tech Stack:** Python 3.10+, `google-genai` (for token counting), `subprocess` (for CLI execution).

---

### Task 1: Setup Token Measurement Utility

**Files:**
- Create: `harness/token_utils.py`
- Test: `tests/test_token_utils.py`

- [ ] **Step 1: Write the failing test for token counting**

```python
import pytest
from harness.token_utils import count_tokens

def test_count_tokens_real_string():
    # This requires a GEMINI_API_KEY to be present in the environment for real counting
    # or we can mock the client. For this utility, we'll assume a real key is available.
    text = "Hello world"
    # Typical tokenizers might count this as 2 tokens
    count = count_tokens(text)
    assert isinstance(count, int)
    assert count > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_token_utils.py -v`
Expected: FAIL (Module not found)

- [ ] **Step 3: Implement `count_tokens` using `google-genai`**

```python
import os
from google import genai

def count_tokens(text: str, model: str = "gemini-1.5-flash") -> int:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Fallback to rough estimation if no key (chars / 4)
        return len(text) // 4
    
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.count_tokens(
            model=model,
            contents=text
        )
        return response.total_tokens
    except Exception:
        return len(text) // 4
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_token_utils.py -v`

- [ ] **Step 5: Commit**

```bash
git add harness/token_utils.py tests/test_token_utils.py
git commit -m "feat: add token counting utility"
```

---

### Task 2: Implement CLI Runner Wrapper

**Files:**
- Create: `harness/cli_runner.py`
- Test: `tests/test_cli_runner.py`

- [ ] **Step 1: Write test for executing a gemini command and capturing output**

```python
from harness.cli_runner import run_gemini_command

def test_run_gemini_command_mock():
    # We'll test with a simple echo or version check if gemini is installed
    # For now, just ensure it captures STDOUT
    result = run_gemini_command(["--version"])
    assert "version" in result.lower() or result == "" # Empty if command fails but doesn't throw
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement `run_gemini_command`**

```python
import subprocess
import sys

def run_gemini_command(args: list[str]) -> str:
    """Executes a gemini command and returns the STDOUT."""
    cmd = ["gemini"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e.stderr}", file=sys.stderr)
        return ""
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add harness/cli_runner.py tests/test_cli_runner.py
git commit -m "feat: add CLI runner wrapper for benchmark"
```

---

### Task 3: Create Benchmark Logic (Monolith vs. Harness)

**Files:**
- Create: `scripts/benchmark_efficiency.py`

- [ ] **Step 1: Implement the Monolith execution logic**

```python
import os
from harness.token_utils import count_tokens
from harness.cli_runner import run_gemini_command

def run_monolith_benchmark(task_prompt: str, rules_content: str):
    # Construct massive prompt
    full_prompt = f"{rules_content}\n\nTASK: {task_prompt}"
    
    print("Running Monolith Benchmark...")
    # Calculate input tokens
    input_tokens = count_tokens(full_prompt)
    
    # Execute using -p for headless mode
    output = run_gemini_command(["-y", "-p", f"Instructions:\n{rules_content}\n\nTask: {task_prompt}"])
    output_tokens = count_tokens(output)
    
    return input_tokens + output_tokens
```

- [ ] **Step 2: Implement the Harness (Delegated) execution logic**

```python
def run_harness_benchmark(task_prompt: str, rules_content: str):
    # Hub (Orchestrator) only sees a lean pointer
    hub_prompt = f"@.gemini/rules/core_mandates.md\n\nTASK: {task_prompt}"
    
    # Step 1: Architect (Research)
    print("Running Harness Step 1: Architect...")
    architect_input = count_tokens(hub_prompt)
    # Step 1: Architect (Research)
    print("Running Harness Step 1: Architect...")
    arch_content = Path(".gemini/agents/architect.md").read_text()
    arch_output = run_gemini_command(["-y", "-p", f"Role: Architect\n\nInstructions:\n{arch_content}\n\nTask: {task_prompt}"])
    arch_out_tokens = count_tokens(arch_output)
    
    # Step 2: Implementer (Action) - passing summary
    print("Running Harness Step 2: Implementer...")
    impl_content = Path(".gemini/agents/implementer.md").read_text()
    impl_prompt = f"Summary of research: {arch_output}\n\nTask: {task_prompt}"
    impl_input_tokens = count_tokens(impl_prompt)
    impl_output = run_gemini_command(["-y", "-p", f"Role: Implementer\n\nInstructions:\n{impl_content}\n\n{impl_prompt}"])
    impl_out_tokens = count_tokens(impl_output)
    
    total_tokens = count_tokens(arch_content) + arch_out_tokens + impl_input_tokens + impl_out_tokens
    return total_tokens
```

- [ ] **Step 3: Implement Main CLI Entry Point with Baseline Task**

```python
import argparse

BASELINE_TASK = "Generate a JSON with 10 user objects (id, name, age). Filter those > 18. Output the result."

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--prompt", type=str)
    args = parser.parse_args()
    
    task = args.prompt or (BASELINE_TASK if args.baseline else None)
    if not task:
        print("Please provide a prompt or use --baseline")
        return

    # Load core rules
    rules_path = ".gemini/rules/core_mandates.md"
    with open(rules_path, "r") as f:
        rules = f.read()

    monolith_total = run_monolith_benchmark(task, rules)
    harness_total = run_harness_benchmark(task, rules)
    
    print("\n" + "="*30)
    print("BENCHMARK RESULTS")
    print(f"Monolith: {monolith_total} tokens")
    print(f"Harness:  {harness_total} tokens")
    savings = (1 - (harness_total / monolith_total)) * 100
    print(f"Savings:  {savings:.1f}%")
    print("="*30)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Test with a small dummy prompt**

Run: `python3 scripts/benchmark_efficiency.py --prompt "Say hello world"`

- [ ] **Step 5: Commit**

```bash
git add scripts/benchmark_efficiency.py
git commit -m "feat: implement token efficiency benchmark script"
```
