import os
import argparse
import sys
from harness.token_utils import count_tokens
from harness.cli_runner import run_gemini_command, CLIRunnerError

BASELINE_TASK = "Generate a JSON with 10 user objects (id, name, age). Filter those > 18. Output the result."

def run_monolith_benchmark(task_prompt: str, rules_content: str):
    # Construct massive prompt
    full_prompt = f"{rules_content}\n\nTASK: {task_prompt}"
    
    # Create temp agent file
    agent_file = "temp_monolith_agent.md"
    with open(agent_file, "w") as f:
        f.write(f"---\nname: monolith\ndescription: test\n---\n{full_prompt}")
    
    print("Running Monolith Benchmark...")
    # Since we want to measure tokens, we calculate input tokens manually
    input_tokens = count_tokens(full_prompt)
    
    try:
        # Execute (Simulating execution)
        output = run_gemini_command(["run", "--agent", agent_file, "--input", "Complete the task."])
        output_tokens = count_tokens(output)
    finally:
        if os.path.exists(agent_file):
            os.remove(agent_file)
            
    return input_tokens + output_tokens

def run_harness_benchmark(task_prompt: str, rules_content: str):
    # Hub (Orchestrator) only sees a lean pointer
    hub_prompt = f"@.gemini/rules/core_mandates.md\n\nTASK: {task_prompt}"
    
    # Step 1: Architect (Research)
    print("Running Harness Step 1: Architect...")
    architect_input = count_tokens(hub_prompt)
    arch_output = run_gemini_command(["run", "--agent", ".gemini/agents/architect.md", "--input", task_prompt])
    arch_out_tokens = count_tokens(arch_output)
    
    # Step 2: Implementer (Action) - passing summary
    print("Running Harness Step 2: Implementer...")
    impl_prompt = f"Summary of research: {arch_output}\n\nTask: {task_prompt}"
    impl_input_tokens = count_tokens(impl_prompt)
    impl_output = run_gemini_command(["run", "--agent", ".gemini/agents/implementer.md", "--input", "Implement it."])
    impl_out_tokens = count_tokens(impl_output)
    
    total_tokens = architect_input + arch_out_tokens + impl_input_tokens + impl_out_tokens
    return total_tokens

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
    try:
        with open(rules_path, "r") as f:
            rules = f.read()
    except FileNotFoundError:
        # Fallback for testing environment if rules don't exist
        rules = "# Core Rules\n1. Do good code."

    try:
        monolith_total = run_monolith_benchmark(task, rules)
        harness_total = run_harness_benchmark(task, rules)
        
        print("\n" + "="*30)
        print("BENCHMARK RESULTS")
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
