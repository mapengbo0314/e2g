#!/usr/bin/env python3
"""
Token Efficiency Benchmark Utility

This script measures the token savings of the Agentic Harness (Hub-and-Spoke model)
vs. a Monolithic agent. It operates by simulating the actual CLI execution of the
agents and calculating the precise token usage for each phase.

Usage:
  python scripts/benchmark_efficiency_test.py --baseline
  python scripts/benchmark_efficiency_test.py --prompt "Your custom task here"
"""

import os
import argparse
import sys
import subprocess
from pathlib import Path
from google import genai

# ==========================================
# 1. Token Utilities
# ==========================================

_CLIENT_CACHE = {}

def get_client(api_key: str) -> genai.Client:
    """Returns a cached genai.Client instance for the given API key."""
    if api_key not in _CLIENT_CACHE:
        _CLIENT_CACHE[api_key] = genai.Client(api_key=api_key)
    return _CLIENT_CACHE[api_key]

def count_tokens(text: str, model: str = "gemini-1.5-flash") -> int:
    if not text:
        return 0

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Fallback to rough estimation if no key (chars / 4, min 1 for non-empty)
        return max(1, len(text) // 4)
    
    try:
        client = get_client(api_key)
        response = client.models.count_tokens(
            model=model,
            contents=text
        )
        return response.total_tokens
    except Exception:
        return max(1, len(text) // 4)

# ==========================================
# 2. CLI Runner
# ==========================================

class CLIRunnerError(Exception):
    """Exception raised when a CLI command fails."""
    pass

def run_gemini_command(args: list[str]) -> str:
    """
    Executes a gemini command and returns the STDOUT.
    """
    cmd = ["gemini"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except FileNotFoundError:
        error_msg = "The 'gemini' executable was not found in the system PATH."
        print(error_msg, file=sys.stderr)
        raise CLIRunnerError(error_msg)
    except subprocess.CalledProcessError as e:
        error_msg = f"Command '{' '.join(cmd)}' failed with exit code {e.returncode}: {e.stderr.strip()}"
        print(error_msg, file=sys.stderr)
        raise CLIRunnerError(error_msg) from e

# ==========================================
# 3. Benchmark Logic
# ==========================================

BASELINE_TASK = "Generate a JSON with 10 user objects (id, name, age). Filter those > 18. Output the result."

def run_monolith_benchmark(task_prompt: str, rules_content: str):
    full_prompt = f"{rules_content}\n\nTASK: {task_prompt}"
    agent_file = "temp_monolith_agent.md"
    
    with open(agent_file, "w") as f:
        f.write(f"---\nname: monolith\ndescription: test\n---\n{full_prompt}")
    
    print("Running Monolith Benchmark...")
    input_tokens = count_tokens(full_prompt)
    
    try:
        # We simulate the run without interactive prompts to measure output
        output = run_gemini_command(["run", "--agent", agent_file, "--input", "Complete the task."])
        output_tokens = count_tokens(output)
    finally:
        if os.path.exists(agent_file):
            os.remove(agent_file)
            
    return input_tokens + output_tokens

def run_harness_benchmark(task_prompt: str, harness_dir: Path):
    # Determine correct include pointer based on directory name
    include_str = f"@{harness_dir.name}/rules/core_mandates.md"
    hub_prompt = f"{include_str}\n\nTASK: {task_prompt}"
    
    architect_agent = str(harness_dir / "agents" / "architect.md")
    implementer_agent = str(harness_dir / "agents" / "implementer.md")
    
    print("Running Harness Step 1: Architect...")
    architect_input = count_tokens(hub_prompt)
    arch_output = run_gemini_command(["run", "--agent", architect_agent, "--input", task_prompt])
    arch_out_tokens = count_tokens(arch_output)
    
    print("Running Harness Step 2: Implementer...")
    impl_prompt = f"Summary of research: {arch_output}\n\nTask: {task_prompt}"
    impl_input_tokens = count_tokens(impl_prompt)
    impl_output = run_gemini_command(["run", "--agent", implementer_agent, "--input", "Implement it."])
    impl_out_tokens = count_tokens(impl_output)
    
    total_tokens = architect_input + arch_out_tokens + impl_input_tokens + impl_out_tokens
    return total_tokens

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true", help="Run the deterministic baseline task")
    parser.add_argument("--prompt", type=str, help="Run a custom task")
    args = parser.parse_args()
    
    task = args.prompt or (BASELINE_TASK if args.baseline else None)
    if not task:
        print("Please provide a prompt or use --baseline")
        return

    # Determine harness directory relative to this script
    script_dir = Path(__file__).parent.resolve()
    harness_dir = script_dir.parent
    
    # Extract rules content
    rules_path = harness_dir / "rules" / "core_mandates.md"
    try:
        with open(rules_path, "r") as f:
            rules = f.read()
    except FileNotFoundError:
        rules = "# Core Rules\n1. Do good code."
        print(f"Warning: {rules_path} not found. Using fallback rules.")

    try:
        monolith_total = run_monolith_benchmark(task, rules)
        harness_total = run_harness_benchmark(task, harness_dir)
        
        print("\n" + "="*30)
        print("BENCHMARK RESULTS")
        print(f"Task: {task[:50]}...")
        print(f"Monolith: {monolith_total} tokens")
        print(f"Harness:  {harness_total} tokens")
        if monolith_total > 0:
            savings = (1 - (harness_total / monolith_total)) * 100
            print(f"Savings:  {savings:.1f}%")
        else:
            print("Savings:  N/A (Monolith total is 0)")
        print("="*30)
    except CLIRunnerError as e:
        print(f"\nBenchmark failed due to CLI error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
