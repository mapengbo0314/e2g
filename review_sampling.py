import sys
import json
import asyncio
from harness.orchestrator import HarnessOrchestrator
from harness.task_registry import TaskRegistry

def run_review():
    prompt = """
    Review the recent changes made to `harness/mcp_server.py`, `harness/orchestrator.py`, and `harness/nodes.py` that implement MCP Sampling (using `sampling/createMessage`).
    Create a detailed design document analyzing:
    1. What went wrong or what is technically inaccurate about this implementation.
    2. Why testing this MCP server might fail (e.g., blocking the event loop, stdio collisions, thread safety).
    3. Why MCP Sampling is potentially bad or risky for this architecture.
    4. What was good about the approach.
    5. What needs to be changed for a robust production architecture.
    
    Output a comprehensive markdown document with these sections.
    """
    
    # We use a dummy directory or the current one
    tool_index_dir = "/Users/pengbolicious/pengbo-apps/e-2-g/local_outputs/span_landing_index_v2"
    
    with HarnessOrchestrator(index_dir=tool_index_dir) as orch:
        result = orch.run(user_prompt=prompt, thread_id="sampling-review")
        
    print("--- RESULT ---")
    print(json.dumps(result, indent=2))
    
    artifacts = result.get("artifacts_produced", [])
    if artifacts:
        with open("sampling_review_design.md", "w") as f:
            for art in artifacts:
                f.write(f"## {art.get('type')}\n\n")
                f.write(art.get('content', ''))
                f.write("\n\n")
        print("Wrote review to sampling_review_design.md")
    else:
        print("No artifacts produced.")

if __name__ == "__main__":
    run_review()
