"""Unified Prompter and Agent Configuration Loader."""

import os
import yaml
import json
from typing import Dict, Any, Optional

class AgentConfigLoader:
    """Loads agent configuration from YAML files."""
    
    def __init__(self, agents_dir: str = "_agents/agents"):
        self.agents_dir = agents_dir
        self._configs: Dict[str, Dict[str, Any]] = {}
        
    def load(self, agent_name: str) -> Dict[str, Any]:
        """Loads and caches the configuration for a specific agent.
        
        By caching configs in `self._configs`, we prevent redundant file I/O 
        across multiple LangGraph steps. If parsing fails, we raise a RuntimeError 
        to halt execution rather than propagating malformed YAML.
        """
        if agent_name in self._configs:
            return self._configs[agent_name]
            
        config_path = os.path.join(self.agents_dir, agent_name, "config.yaml")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Agent config not found: {config_path}")
            
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                config = yaml.safe_load(f)
                if config is None:
                    raise RuntimeError(f"Failed to parse agent config for {agent_name}: config is empty.")
            except yaml.YAMLError as e:
                raise RuntimeError(f"Failed to parse agent config for {agent_name}. Check YAML syntax. Error: {e}")
            
        self._configs[agent_name] = config
        return config
        
    def get_system_prompt(self, agent_name: str) -> str:
        """Extracts the system prompt from the agent configuration."""
        config = self.load(agent_name)
        return config.get("prompts", {}).get("system_prompt", "")
        
    def get_role_mandate(self, agent_name: str) -> str:
        """Extracts the role mandate from the agent configuration."""
        config = self.load(agent_name)
        return config.get("prompts", {}).get("role_mandate", "")

class UnifiedPrompter:
    """Constructs prompts for agents using their configuration and the current state."""
    
    def __init__(self, config_loader: AgentConfigLoader):
        self.config_loader = config_loader
        
    def build_system_message(self, agent_name: str) -> str:
        """Builds the complete system message for the agent."""
        sys_prompt = self.config_loader.get_system_prompt(agent_name)
        role_mandate = self.config_loader.get_role_mandate(agent_name)
        
        parts = []
        if sys_prompt:
            parts.append(sys_prompt)
        if role_mandate:
            parts.append(f"ROLE MANDATE:\n{role_mandate}")
            
        return "\n\n".join(parts)
        
    def build_user_message(self, state: Dict[str, Any]) -> str:
        """Builds the user message based on the current state."""
        # Filter out verbose LangGraph messages to avoid hitting token limits
        
        # Filter out verbose LangGraph messages to avoid hitting token limits
        filtered_state = {k: v for k, v in state.items() if k != "messages" and v}
        
        # We leverage a multi-line f-string to cleanly format the user prompt, 
        # injecting the strategic milestones, architectural context, and a raw state dump.
        # This replaces procedural appending with a declarative template.
        user_prompt = filtered_state.get("user_prompt", "None")
        milestones = "\n".join(f" - [{m.get('id')}] {m.get('task')}" for m in filtered_state.get("milestones", []))
        strategy = filtered_state.get("implementation_strategy", "None")
        verified_context = "\n".join(f" - {ctx['path']}: {ctx['summary']}" for ctx in filtered_state.get("verified_context", []))
        
        template = f"""Current Task Context:
User Prompt: {user_prompt}

Milestones:
{milestones if milestones else "None"}

Implementation Strategy:
{strategy}

Verified Context:
{verified_context if verified_context else "None"}

State Dump:
{json.dumps(filtered_state, indent=2)}

Please proceed with your task based on your role mandate.
"""
        return template
