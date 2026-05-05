"""Unified Harness MCP Server using FastMCP.

Provides semantic context fetching, indexing, and agentic orchestration.
Uses FastMCP for robust protocol handling and IDE integration.
"""

import os
import json
import sys
import asyncio
import uuid
import logging
import traceback
import subprocess
from typing import List, Optional, Dict, Any

from mcp.server.fastmcp import FastMCP, Context
from mcp.types import SamplingMessage, TextContent

from harness.tools import ContextTools
from harness.state import OverlayState
from harness.task_registry import TaskRegistry, update_registry_from_result

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("harness-fastmcp")

# Initialize FastMCP
mcp = FastMCP("unified-harness")

# Global registry handle
_registry = TaskRegistry()

# --- Tool Definitions ---

@mcp.tool()
async def fetch_semantic_context(paths: List[str], index_dir: Optional[str] = None) -> str:
    """Retrieves verified IndexDocument sections for specified paths.
    
    Args:
        paths: List of file or directory paths to fetch context for.
        index_dir: Optional path to the index directory.
    """
    from indexing.fs_manager import RealFsManager
    
    target_dir = index_dir or ".index_state"
    fs_manager = RealFsManager()
    state = OverlayState(
        state_dir=target_dir,
        current_diffs={},
        provisional_summaries={},
        fs_manager=fs_manager
    )
    tools = ContextTools(state, os.getcwd())
    
    results = []
    for path in paths:
        results.append(tools.get_verified_context(path))
    
    return json.dumps({"results": results}, indent=2)

@mcp.tool()
async def get_stale_context(index_dir: Optional[str] = None, scope: str = "all") -> str:
    """Returns paths where the index is stale relative to the working tree.
    
    Args:
        index_dir: Optional path to the index directory.
        scope: Filter for staleness (all, modified, staged).
    """
    # Placeholder for actual staleness logic
    return json.dumps({"stale_paths": [], "scope": scope}, indent=2)

@mcp.tool()
async def trigger_harness_task(prompt: str, index_dir: Optional[str] = None, thread_id: Optional[str] = None, ctx: Context = None) -> str:
    """Starts the LangGraph orchestrator in the background.
    
    Args:
        prompt: The request/prompt for the AI agent.
        index_dir: Optional path to the index directory.
        thread_id: Optional custom thread ID.
    """
    t_id = thread_id or str(uuid.uuid4())
    target_dir = index_dir or ".index_state"
    
    _registry.register(t_id, target_dir)
    _registry.update(t_id, target_dir, status="running")
    
    main_loop = asyncio.get_running_loop()

    async def sampling_callback(system_msg: str, user_msg: str) -> str:
        if not ctx:
            return "Error: No MCP context available for sampling."
        
        try:
            result = await ctx.create_message(
                messages=[SamplingMessage(role="user", content=TextContent(type="text", text=user_msg))],
                system_prompt=system_msg
            )
            return result.content.text if hasattr(result.content, "text") else str(result.content)
        except Exception as e:
            logger.error(f"Sampling failed: {e}")
            return f"Error during sampling: {str(e)}"

    def _run_in_thread():
        from harness.orchestrator import HarnessOrchestrator
        
        # Helper to bridge sync orchestrator to the main async loop for sampling
        def sync_sampling(sys_m, usr_m):
            future = asyncio.run_coroutine_threadsafe(sampling_callback(sys_m, usr_m), main_loop)
            return future.result()
            
        try:
            orchestrator = HarnessOrchestrator(
                index_dir=target_dir,
                sampling_callback=sync_sampling
            )
            result = orchestrator.run(user_prompt=prompt, thread_id=t_id)
            update_registry_from_result(t_id, target_dir, result)
        except Exception as e:
            logger.error(f"Orchestrator thread failed: {e}")
            _registry.update(t_id, target_dir, status="failed", error=str(e))

    # Trigger background execution
    asyncio.create_task(asyncio.to_thread(_run_in_thread))
    
    return json.dumps({"status": "started", "thread_id": t_id}, indent=2)

@mcp.tool()
async def get_harness_status(thread_id: str, index_dir: Optional[str] = None) -> str:
    """Checks the status of a previously triggered harness task.
    
    Args:
        thread_id: The thread ID of the task.
        index_dir: Optional path to the index directory.
    """
    target_dir = index_dir or ".index_state"
    record = _registry.get(thread_id, target_dir)
    if not record:
        return json.dumps({"status": "not_found", "thread_id": thread_id}, indent=2)
        
    result = {
        "thread_id": record.thread_id,
        "status": record.status,
        "current_step": record.current_step,
        "updated_at": record.updated_at
    }
    
    if record.artifacts_produced:
        try:
            result["artifacts"] = json.loads(record.artifacts_produced)
        except:
            result["artifacts"] = record.artifacts_produced
            
    return json.dumps(result, indent=2)

@mcp.tool()
async def list_harness_tasks(index_dir: Optional[str] = None, status_filter: Optional[str] = None) -> str:
    """Lists all tracked harness tasks.
    
    Args:
        index_dir: Optional filter for a specific index directory.
        status_filter: Optional filter for status (running, completed, failed, etc).
    """
    tasks = _registry.list(index_dir=index_dir, status_filter=status_filter)
    return json.dumps({
        "tasks": [
            {
                "thread_id": t.thread_id,
                "status": t.status,
                "current_step": t.current_step,
                "updated_at": t.updated_at
            } for t in tasks
        ]
    }, indent=2)

@mcp.tool()
async def trigger_reindex(index_dir: Optional[str] = None) -> str:
    """Triggers the semantic indexing process for the repository.
    
    Args:
        index_dir: Optional path to the index directory.
    """
    target_dir = index_dir or ".index_state"
    
    try:
        # We don't use a guard here as per user feedback
        subprocess.Popen(
            [sys.executable, "-m", "harness.indexing.main", "--index_dir", target_dir],
            stdout=sys.stderr,
            stderr=sys.stderr,
            start_new_session=True
        )
        return json.dumps({"status": "indexing_started", "index_dir": target_dir}, indent=2)
    except Exception as e:
        return json.dumps({"status": "failed", "error": str(e)}, indent=2)

@mcp.tool()
async def reload_agents() -> str:
    """Regenerates .gemini/agents/*.md documentation and clears agent caches.
    
    This synchronizes the formal agent definitions in _agents/agents/ with 
    the rendered documentation used by the system.
    """
    try:
        from _agents.reload_agents import reload_agents as run_reload
        run_reload()
        return json.dumps({"status": "success", "message": "Agents reloaded and documentation updated."}, indent=2)
    except Exception as e:
        logger.error(f"Reload failed: {e}")
        return json.dumps({"status": "failed", "error": str(e)}, indent=2)

if __name__ == "__main__":
    # FastMCP handles the stdio server setup automatically
    mcp.run()
