"""MCP Server for the Unified Harness.

Exposes context fetching and background execution capabilities over stdio,
fully compliant with the Model Context Protocol (MCP).
"""

from typing import List, Dict, Any
import json
import sys
import asyncio
import traceback

from harness.tools import ContextTools

ACTIVE_TASKS = {}

def get_tool_schemas() -> list[dict]:
    return [
        {
            "name": "fetch_semantic_context",
            "description": "Retrieves verified IndexDocument sections for specified paths.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "paths": { "type": "array", "items": { "type": "string" } },
                    "sections": {
                        "type": "array",
                        "items": { "type": "string", "enum": ["overview", "key_dependencies", "key_interfaces", "deep_dive", "configurations", "testing_strategy"] }
                    },
                    "include_verification_status": { "type": "boolean", "default": True }
                },
                "required": ["paths"]
            }
        },
        {
            "name": "get_stale_context",
            "description": "Returns paths where the index is stale relative to the working tree.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "scope": { "type": "string", "enum": ["all", "modified", "staged"], "default": "modified" }
                }
            }
        },
        {
            "name": "trigger_harness_task",
            "description": "Starts the LangGraph orchestrator in the background to implement a feature or bugfix. Returns a thread_id immediately.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": { "type": "string", "description": "The request/prompt for the AI agent to implement." },
                    "thread_id": { "type": "string", "description": "Optional custom thread ID for tracking or resuming." }
                },
                "required": ["prompt"]
            }
        },
        {
            "name": "get_harness_status",
            "description": "Checks the status of a previously triggered harness task.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "thread_id": { "type": "string", "description": "The thread ID returned by trigger_harness_task." }
                },
                "required": ["thread_id"]
            }
        }
    ]

def _run_orchestrator_sync(orchestrator, prompt: str, thread_id: str):
    try:
        orchestrator.run(user_prompt=prompt, thread_id=thread_id)
        ACTIVE_TASKS[thread_id] = {"status": "completed"}
    except Exception as e:
        ACTIVE_TASKS[thread_id] = {"status": "failed", "error": str(e), "traceback": traceback.format_exc()}

async def run_mcp_server(orchestrator, workspace_root: str):
    """An async stdio-based MCP server loop."""
    tools = ContextTools(orchestrator.overlay_state, workspace_root)
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
            req = json.loads(line_str)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})
            
            # MCP Protocol standard endpoints
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "unified-harness",
                            "version": "1.0.0"
                        }
                    }
                }
                print(json.dumps(response), flush=True)
                continue
                
            elif method == "notifications/initialized":
                continue
                
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": get_tool_schemas()
                    }
                }
                print(json.dumps(response), flush=True)
                continue
                
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                
                result_data = None
                is_error = False
                
                try:
                    if tool_name == "get_stale_context":
                        result_data = tools.get_stale_context(args.get("paths", []))
                    elif tool_name == "fetch_semantic_context":
                        # Convert arguments
                        result_data = tools.get_verified_context(args.get("paths", [""])[0])
                    elif tool_name == "trigger_harness_task":
                        prompt = args.get("prompt")
                        import uuid
                        thread_id = args.get("thread_id", str(uuid.uuid4()))
                        
                        if thread_id in ACTIVE_TASKS and ACTIVE_TASKS[thread_id].get("status") == "running":
                            result_data = {"status": "already_running", "thread_id": thread_id}
                        else:
                            ACTIVE_TASKS[thread_id] = {"status": "running"}
                            asyncio.create_task(asyncio.to_thread(_run_orchestrator_sync, orchestrator, prompt, thread_id))
                            result_data = {"status": "started", "thread_id": thread_id}
                    elif tool_name == "get_harness_status":
                        thread_id = args.get("thread_id")
                        result_data = ACTIVE_TASKS.get(thread_id, {"status": "unknown_thread_id"})
                    else:
                        raise ValueError(f"Unknown tool: {tool_name}")
                except Exception as e:
                    is_error = True
                    result_data = f"Error executing {tool_name}: {str(e)}\n{traceback.format_exc()}"
                
                # Standard MCP tools/call response
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result_data, indent=2) if not isinstance(result_data, str) else result_data
                            }
                        ],
                        "isError": is_error
                    }
                }
                print(json.dumps(response), flush=True)
                continue
                
            # Legacy custom RPC fallback
            elif method in ["get_stale_context", "get_verified_context"]:
                result_data = None
                if method == "get_stale_context":
                    result_data = tools.get_stale_context(params.get("paths", []))
                elif method == "get_verified_context":
                    result_data = tools.get_verified_context(params.get("path", ""))
                
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result_data
                }
                print(json.dumps(response), flush=True)
                continue
                
            else:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
                print(json.dumps(error_response), flush=True)
                
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)}
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    from harness.orchestrator import HarnessOrchestrator
    orchestrator = HarnessOrchestrator(index_dir=".index_state")
    asyncio.run(run_mcp_server(orchestrator, "."))
