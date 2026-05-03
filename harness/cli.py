"""CLI entry point for the Unified Harness.

Handles process locking, checkpointer resumption, and triggering the orchestrator.
"""

import asyncio
import logging
import argparse
import fcntl
import os
import sys

from harness.orchestrator import HarnessOrchestrator

def acquire_lock(workspace_root: str):
    """Acquires a non-blocking fcntl lock to ensure single instance."""
    lock_file = os.path.join(workspace_root, ".harness.lock")
    fd = os.open(lock_file, os.O_CREAT | os.O_RDWR)
    try:
        # Attempt to grab an exclusive lock. Fails immediately if already locked.
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except BlockingIOError:
        # Prevent file descriptor leak if we fail to acquire the lock
        os.close(fd)
        logging.error(f"Another instance of the harness is running (lockfile: {lock_file}).")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Unified AI Harness CLI")
    parser.add_argument("--prompt", type=str, help="The user prompt to execute.")
    parser.add_argument("--thread-id", type=str, default="default", help="The LangGraph thread ID to resume or start.")
    parser.add_argument("--index-dir", type=str, default=".index_state", help="Directory containing the indexing artifacts.")
    parser.add_argument("--mcp", action="store_true", help="Run the MCP stdio server instead of the agent graph.")
    args = parser.parse_args()

    lock_fd = acquire_lock(".harness.lock")

    try:
        if args.mcp:
            from harness.mcp_server import run_mcp_server
            from harness.state import OverlayState
            from indexing.fs_manager import RealFsManager
            state = OverlayState(
                state_dir=args.index_dir,
                current_diffs={},
                provisional_summaries={},
                fs_manager=RealFsManager()
            )
            asyncio.run(run_mcp_server(state, "."))
        else:
            if not args.prompt:
                logging.error("--prompt is required when not running in MCP mode.")
                sys.exit(1)
                
            orchestrator = HarnessOrchestrator(index_dir=args.index_dir)
            orchestrator.run(user_prompt=args.prompt, thread_id=args.thread_id)
            
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)

if __name__ == "__main__":
    main()
