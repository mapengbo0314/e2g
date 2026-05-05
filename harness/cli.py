"""CLI entry point for the Unified Harness.

Supports interactive human-in-the-loop, thread resumption, and task listing.
"""

import asyncio
import logging
import argparse
import os
import sys

from harness.orchestrator import HarnessOrchestrator
from harness.state import RunResult
from harness.task_registry import TaskRegistry, update_registry_from_result


def _handle_suspension(
    orchestrator: HarnessOrchestrator,
    result: RunResult,
    index_dir: str,
    feedback_text: str = None,
) -> RunResult:
    """Interactive loop for handling graph suspension at human node.

    If feedback_text is provided (--feedback flag), uses it directly once.
    Otherwise, prompts via stdin in a loop until the user provides input
    or the graph completes/fails.
    """
    while result["status"] == "suspended":
        # Display suspension context to the operator
        print("\n" + "=" * 60)
        print("⚠️  HUMAN INPUT REQUIRED")
        print("=" * 60)
        print(f"\nEscalation Reason:\n  {result['escalation_reason']}")
        print(f"\nLast Step: {result['final_step']}")
        print(f"Thread ID: {result['thread_id']}")
        print("-" * 60)

        if feedback_text:
            # Non-interactive mode: use provided feedback once, then go interactive
            human_input = feedback_text
            feedback_text = None
            print(f"\nUsing provided feedback: {human_input}")
        else:
            # Interactive mode: prompt the user for guidance
            print("\nEnter your feedback (or 'quit' to abort):")
            try:
                human_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nAborted by user.")
                return result

            if human_input.lower() == "quit":
                print("Aborting. Thread remains suspended for later --resume.")
                return result

        if not human_input:
            print("Empty feedback. Please provide input or type 'quit'.")
            continue

        # Update registry to reflect the resumption attempt
        update_registry_from_result(
            result["thread_id"], index_dir,
            {"status": "running", "final_step": "human:resuming"}
        )

        # Resume the graph with the human's feedback
        result = orchestrator.resume(
            thread_id=result["thread_id"],
            human_feedback=human_input
        )

        # Persist the new result status in the global registry
        update_registry_from_result(result["thread_id"], index_dir, result)

    return result


def _print_final_result(result: RunResult) -> None:
    """Prints the final workflow result summary."""
    print("\n" + "=" * 60)
    if result["status"] == "completed":
        print("✅ Workflow completed successfully!")
    elif result["status"] == "failed":
        print("❌ Workflow failed.")
        if result.get("escalation_reason"):
            print(f"   Reason: {result['escalation_reason']}")
    elif result["status"] == "suspended":
        print("⏸️  Workflow suspended (use --resume to continue).")
        print(f"   Thread ID: {result['thread_id']}")
    print(f"   Final step: {result['final_step']}")
    print("=" * 60)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Argument definitions for all CLI modes
    parser = argparse.ArgumentParser(description="Unified AI Harness CLI")
    parser.add_argument("--prompt", type=str, help="The user prompt to execute.")
    parser.add_argument("--thread-id", type=str, default="default",
                        help="The LangGraph thread ID to resume or start.")
    parser.add_argument("--index-dir", type=str, default=".index_state",
                        help="Directory containing the indexing artifacts.")
    parser.add_argument("--mcp", action="store_true",
                        help="Run the MCP stdio server instead of the agent graph.")
    parser.add_argument("--resume", type=str, metavar="THREAD_ID",
                        help="Resume a suspended thread by ID.")
    parser.add_argument("--feedback", type=str,
                        help="Non-interactive feedback for --resume (scripted usage).")
    parser.add_argument("--list-threads", action="store_true",
                        help="List all tracked threads from the registry.")
    parser.add_argument("--prune", action="store_true",
                        help="Prune old terminal task records (>24h).")
    parser.add_argument("--reload-agents", action="store_true",
                        help="Regenerate agent documentation and clear caches.")
    args = parser.parse_args()

    # Reload mode: sync agent docs and exit
    if args.reload_agents:
        from _agents.reload_agents import reload_agents as run_reload
        run_reload()
        return

    # MCP mode: delegate to the FastMCP server and exit
    if args.mcp:
        from harness.mcp_server import mcp
        mcp.run()
        return

    # List mode: query registry and print table
    if args.list_threads:
        with TaskRegistry() as registry:
            # Filter by repo if a non-default index_dir was given
            filter_dir = os.path.abspath(args.index_dir) if args.index_dir != ".index_state" else None
            tasks = registry.list(index_dir=filter_dir)
            if not tasks:
                print("No tracked threads found.")
            else:
                # Fixed-width column headers for terminal readability
                print(f"\n{'Thread ID':<40} {'Status':<12} {'Step':<30} {'Updated'}")
                print("-" * 100)
                for t in tasks:
                    print(f"{t.thread_id:<40} {t.status:<12} {t.current_step:<30} {t.updated_at}")
        return

    # Prune mode: remove old terminal records
    if args.prune:
        with TaskRegistry() as registry:
            count = registry.prune()
            print(f"Pruned {count} old task records.")
        return

    # Resume mode: reconnect to a suspended thread
    if args.resume:
        index_dir = os.path.abspath(args.index_dir)
        with HarnessOrchestrator(index_dir=index_dir) as orchestrator:
            # Validate the thread exists and is actually suspended
            config = {"configurable": {"thread_id": args.resume}}
            state_snapshot = orchestrator.graph.get_state(config)

            if not state_snapshot.values:
                print(f"Error: Thread '{args.resume}' not found in checkpointer.")
                sys.exit(1)

            next_nodes = state_snapshot.next or ()
            if "human" not in next_nodes:
                print(f"Thread '{args.resume}' is not suspended at human node. "
                      f"Current next: {next_nodes}")
                sys.exit(1)

            # Reconstruct a RunResult-like dict to enter the suspension handler
            values = state_snapshot.values
            step_history = values.get("step_history") or []
            result: RunResult = {
                "status": "suspended",
                "thread_id": args.resume,
                "escalation_reason": values.get("escalation_reason",
                                                 "No escalation reason recorded."),
                "final_step": step_history[-1] if step_history else "unknown",
                "human_prompt": values.get("escalation_reason", "")
            }

            final_result = _handle_suspension(
                orchestrator, result, index_dir, feedback_text=args.feedback
            )
            _print_final_result(final_result)
        return

    # Normal run mode: execute a new task
    if not args.prompt:
        logging.error("--prompt is required when not running in MCP or --resume mode.")
        sys.exit(1)

    index_dir = os.path.abspath(args.index_dir)

    # Register task in global registry before starting
    with TaskRegistry() as registry:
        registry.register(args.thread_id, index_dir)

    with HarnessOrchestrator(index_dir=index_dir) as orchestrator:
        result = orchestrator.run(user_prompt=args.prompt, thread_id=args.thread_id)

        # Persist initial result to registry via shared helper
        update_registry_from_result(args.thread_id, index_dir, result)

        # If suspended, enter interactive human feedback loop
        if result["status"] == "suspended":
            result = _handle_suspension(orchestrator, result, index_dir)

        _print_final_result(result)


if __name__ == "__main__":
    main()
