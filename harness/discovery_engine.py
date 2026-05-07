import json
import subprocess
import time

def acquire_mcp_context(project_path: str) -> str:
    """Spawns indxr serve and fetches the project summary via MCP."""
    print(f"Starting indxr MCP server for dynamic analysis on {project_path}...")
    
    proc = subprocess.Popen(
        ["indxr", "serve", project_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, # Prevent deadlock from stderr buffer
        text=True,
        bufsize=1 # Line buffered
    )
    
    try:
        # 1. Initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "harness-wf", "version": "1.0.0"}
            }
        }
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
        
        # Read response loop with id matching
        def read_response(expected_id):
            while True:
                line = proc.stdout.readline()
                if not line:
                    raise RuntimeError("MCP server died unexpectedly.")
                line = line.strip()
                if not line or not line.startswith("{"):
                    continue
                try:
                    resp = json.loads(line)
                    if resp.get("id") == expected_id:
                        return resp
                except json.JSONDecodeError:
                    continue

        read_response(1) # Wait for init response
                
        # Send initialized notification
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        proc.stdin.flush()
        
        # 2. Call summarize tool
        call_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "summarize",
                "arguments": {"path": "."}
            }
        }
        proc.stdin.write(json.dumps(call_req) + "\n")
        proc.stdin.flush()
        
        # Read call response
        resp = read_response(2)
        if "error" in resp:
            raise RuntimeError(f"MCP summarize failed: {resp['error']}")
        if "result" in resp and "content" in resp["result"]:
            return resp["result"]["content"][0]["text"]
                
        return "No context available."
        
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()

def query_llm(prompt: str, llm_provider: str, api_key: str, model: str = None) -> str:
    """Stub for querying the LLM."""
    # Hardcoded stub for initial development
    return '{"agents": [{"name": "API Handler", "role": "Manages Express routes", "zone": "Handler Category"}, {"name": "DB Modeler", "role": "Manages schemas", "zone": "Data Structure Category"}]}'

def discover_agents(project_path: str, feature_fetcher_yaml_path: str, llm_provider: str, api_key: str, model: str = None) -> list[dict]:
    """Uses MCP to get context, loads the system prompt, and queries the LLM."""
    context_str = acquire_mcp_context(project_path)
    
    # Load system prompt
    system_prompt = "You are the Feature Fetcher."
    try:
        import yaml
        with open(feature_fetcher_yaml_path, 'r') as f:
            config = yaml.safe_load(f)
            if "system_prompt" in config:
                system_prompt = config["system_prompt"]
    except Exception as e:
        print(f"Warning: Could not load feature-fetcher prompt: {e}")

    full_prompt = f"{system_prompt}\n\nPROJECT CONTEXT:\n{context_str}\n\nBased on the mandate above, output the required JSON."
    
    print(f"Querying {llm_provider} for specialized agents...")
    response_text = query_llm(full_prompt, llm_provider, api_key, model)
    
    try:
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        return data.get("agents", [])
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse LLM response as JSON: {e}")
        return [{"name": "Architect", "role": "General architecture and design", "zone": "Core"}]

def discover_ddd_context(index_data: dict, llm_provider: str, api_key: str) -> dict:
    """Extracts DDD context based on index data."""
    prompt = (
        "Analyze the following index data and draft a Ubiquitous Language, identify conflicts, "
        "and generate 3-5 alignment questions.\n\n"
        "Your response MUST be in JSON format with the following keys:\n"
        "- 'ul_draft': A string containing the drafted Ubiquitous Language.\n"
        "- 'questions': A list of strings representing alignment questions.\n"
        "- 'legacy_hints': A dictionary containing hints about legacy components.\n\n"
        f"Index Data:\n{json.dumps(index_data, indent=2)}"
    )
    response_text = query_llm(prompt, llm_provider, api_key)
    
    try:
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse LLM response as JSON: {e}")
        return {"ul_draft": "", "questions": [], "legacy_hints": {}}
