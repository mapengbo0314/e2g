import json
import subprocess
import time
import urllib.request
import os

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

def fetch_remote_skill(skill_url: str) -> str:
    """Fetches a skill definition from a raw GitHub URL."""
    try:
        req = urllib.request.Request(skill_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to fetch required skill from {skill_url}")
        print(f"Details: {e}")
        import sys
        sys.exit(1) # Fail hard as requested

def query_llm(prompt: str, llm_provider: str, api_key: str, model: str = None) -> str:
    """Dispatches to the real LLM providers."""
    if llm_provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        use_model = model or "gpt-4o"
        response = client.chat.completions.create(
            model=use_model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
        
    elif llm_provider == "anthropic":
        import urllib.request
        import json
        use_model = model or "claude-3-5-sonnet-20241022"
        data = {
            "model": use_model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(data).encode("utf-8"),
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["content"][0]["text"]
            
    elif llm_provider == "gemini":
        from google import genai
        client = genai.Client(api_key=api_key)
        use_model = model or "gemini-2.5-flash"
        response = client.models.generate_content(
            model=use_model,
            contents=prompt
        )
        return response.text
        
    raise ValueError(f"Unsupported LLM provider: {llm_provider}")

def discover_agents(context_str: str, feature_fetcher_yaml_path: str, llm_provider: str, api_key: str, model: str = None) -> list[dict]:
    """Loads the system prompt and queries the LLM."""
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
        # Find JSON boundaries if LLM included conversational text
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}") + 1
        if start_idx != -1 and end_idx != 0:
            cleaned = cleaned[start_idx:end_idx]
            
        data = json.loads(cleaned)
        return data.get("agents", [])
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse LLM response as JSON: {e}\nResponse:\n{response_text}")
        return [{"name": "Architect", "role": "General architecture and design", "zone": "Core"}]

def discover_ddd_context(context_str: str, llm_provider: str, api_key: str, model: str = None) -> dict:
    """Extracts DDD context using remote skills."""
    print("Fetching remote skills for DDD alignment...")
    grill_me_skill = fetch_remote_skill("https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/grill-me/SKILL.md")
    grill_with_docs_skill = fetch_remote_skill("https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/grill-with-docs.md")
    
    prompt = (
        "You are a strict Domain-Driven Design architect. Analyze the following project context and execute the provided skills.\n\n"
        "=== GRILL-WITH-DOCS SKILL ===\n"
        f"{grill_with_docs_skill}\n\n"
        "=== GRILL-ME SKILL ===\n"
        f"{grill_me_skill}\n\n"
        "Your task:\n"
        "1. Draft a context definition (context.md style) based on the codebase.\n"
        "2. Identify ambiguities or missing domain definitions.\n"
        "3. Use the 'grill-me' approach to generate 3-5 sharp, critical questions to align the user on these ambiguities.\n\n"
        "Your response MUST be in JSON format with exactly these keys:\n"
        "- 'context_draft': A string containing the drafted domain context.\n"
        "- 'questions': A list of strings representing alignment questions.\n"
        "- 'legacy_hints': A dictionary containing hints about legacy components.\n\n"
        f"PROJECT CONTEXT:\n{context_str}"
    )
    
    response_text = query_llm(prompt, llm_provider, api_key, model)
    
    try:
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}") + 1
        if start_idx != -1 and end_idx != 0:
            cleaned = cleaned[start_idx:end_idx]
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse DDD LLM response as JSON: {e}")
        return {"context_draft": "", "questions": [], "legacy_hints": {}}
