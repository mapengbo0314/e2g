# Token Efficiency Benchmark Utility Design

## 1. Overview
The `benchmark_efficiency.py` script is an isolated testing utility designed to measure the token savings achieved by the Superpowers Agentic Harness. It specifically targets "Delegation Efficiency"—the context savings gained when a parent Orchestrator delegates tasks to specialized subagents instead of a single monolithic agent handling the entire workflow.

## 2. Architecture & Execution Model
The script is a standalone Python utility located at `scripts/benchmark_efficiency.py`. It operates in a "CLI Simulation" mode, meaning it invokes the AI agents by executing real shell commands (e.g., `gemini run ...`) rather than making direct API calls. This ensures the benchmark accurately reflects the overhead and context loading of actual usage.

The script runs a designated task through two distinct execution paths:

### Path A: "No-Harness" (Monolith)
This simulates a traditional, single-agent approach.
- The script constructs a massive `monolith_prompt` that concatenates:
  - Core Workspace Mandates
  - Project Rules
  - The Full Task Prompt
- It executes a single, long-running CLI command to complete the task.
- The entire history of tool use and thought process remains in the monolithic context window.

### Path B: "Harness" (Hub-and-Spoke)
This simulates the optimized Superpowers workflow.
- The script acts as a "Mock Orchestrator".
- It delegates the task by invoking specific subagents defined in `.gemini/agents/` (e.g., `architect` then `implementer`).
- Crucially, it only passes the *summary* of the first agent's work to the second agent, simulating the context compression inherent in the Harness.

## 3. Supported Task Modes
The script supports two input methods to ensure both deterministic testing and real-world applicability.

- **Baseline Mode (`--baseline`):**
  - Executes a hardcoded, deterministic task: "Read a generated JSON payload, filter out users under 18, calculate the average age, and write a new file."
  - This ensures reliable A/B testing without variance introduced by the LLM choosing different paths.
- **Custom Mode (`--prompt "<task_string>"`):**
  - Allows the user to provide any arbitrary task string to measure the efficiency of specific real-world requests.

## 4. Token Measurement Strategy
Because the script uses CLI simulation, it will calculate token usage precisely using the `google-genai` SDK's tokenizer (or equivalent, like `tiktoken` if using OpenAI models).
- **Input Tokens:** Measured by counting the text of the prompt files and CLI arguments sent to the agents.
- **Output Tokens:** Measured by counting the text returned to STDOUT by the CLI commands.

## 5. Output and Reporting
The script will output a comparison table to the console and log details to `artifacts/benchmark_report.txt`.

Example Output:
```text
=== TOKEN EFFICIENCY BENCHMARK ===
Task: [Baseline / Custom Prompt]

[NO-HARNESS] (Monolithic Agent)
- Total Context Used: 14,500 tokens

[HARNESS] (Hub-and-Spoke Delegation)
- Orchestrator Context: 1,200 tokens
- Subagent A Context: 2,500 tokens
- Subagent B Context: 1,500 tokens
- Total Context Used: 5,200 tokens

=== RESULTS ===
Overall Token Savings: 64.1%
```
