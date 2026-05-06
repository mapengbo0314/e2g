import json
import sys

def query_llm(prompt: str, llm_provider: str, api_key: str) -> str:
    """Stub for querying the LLM. In production, this uses genai/openai clients."""
    # For this iteration, we will rely on a mocked response or basic API call.
    # We'll use a simple fallback if no real client is wired yet.
    return '{"agents": [{"name": "Architect", "role": "Design lead", "zone": "Core"}, {"name": "Implementer", "role": "Code writer", "zone": "Development"}]}'

def prune_context(index_data: dict) -> dict:
    """Prunes the full index JSON to just a structural map to save context window."""
    if "files" in index_data:
        # Assuming indxr json has a 'files' array or similar structure
        # Just extracting paths to provide a structural overview
        if isinstance(index_data["files"], list):
            return {"files": [f.get("path", "") if isinstance(f, dict) else str(f) for f in index_data["files"]][:100]}
    return index_data

def discover_agents(index_data: dict, llm_provider: str, api_key: str) -> list[dict]:
    """Sends pruned context to LLM and returns recommended agents."""
    pruned_map = prune_context(index_data)
    
    prompt = f"""
    Analyze this project structure:
    {json.dumps(pruned_map, indent=2)}
    
    Identify 3-5 logical "specialization zones" unique to this architecture.
    Recommend an AI agent for each zone.
    
    Return EXACTLY this JSON format:
    {{
      "agents": [
        {{"name": "AgentName", "role": "Brief description of responsibilities", "zone": "The specialization zone"}}
      ]
    }}
    """
    
    response_text = query_llm(prompt, llm_provider, api_key)
    
    try:
        # Strip markdown code blocks if present
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        return data.get("agents", [])
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse LLM response as JSON: {e}")
        # Fallback to default agents if LLM fails
        return [{"name": "Architect", "role": "General architecture and design", "zone": "Core"}]
