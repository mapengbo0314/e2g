"""MCP Server for the Unified Harness.

Exposes context fetching and reindexing capabilities over stdio.
"""

from typing import List, Dict, Any
import json
import sys
import asyncio

from harness.tools import ContextTools
from harness.state import OverlayState

async def run_mcp_server(overlay_state: OverlayState, workspace_root: str):
    """An async stdio-based MCP server loop.
    
    Using asyncio.StreamReader prevents blocking the main thread and allows
    cleaner connection handling and graceful degradation during large payloads.
    """
    tools = ContextTools(overlay_state, workspace_root)
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        try:
            line = await reader.readline()
        except asyncio.exceptions.IncompleteReadError:
            break
        if not line:
            break
            
        line_str = line.decode('utf-8').strip()
        if not line_str:
            continue
            
        req_id = None
        try:
            # 1. Parse JSON-RPC payload
            req = json.loads(line_str)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})
            
            # 2. Route to the appropriate context fetching tool
            result = None
            if method == "get_stale_context":
                paths = params.get("paths", [])
                result = tools.get_stale_context(paths)
            elif method == "get_verified_context":
                path = params.get("path", "")
                result = tools.get_verified_context(path)
            else:
                raise ValueError(f"Unknown method: {method}")
                
            # 3. Format and output the successful JSON-RPC response
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            }
            print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            # -32000 is the standard JSON-RPC code for generic Server Error
            error_response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)}
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    from indexing.fs_manager import RealFsManager
    fs_manager = RealFsManager()
    state = OverlayState(
        state_dir=".index_state",
        current_diffs={},
        provisional_summaries={},
        fs_manager=fs_manager
    )
    asyncio.run(run_mcp_server(state, "."))
