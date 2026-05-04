"""LangGraph node implementations for the Unified Harness."""

import os
import json
from typing import Dict, Any
from harness.state import HarnessState
from harness.prompter import UnifiedPrompter

from indexing.sequential_llm_prompter import GeminiLlmPrompter, GeminiLlmPrompterConfig

class HarnessNodes:
    """Encapsulates the agentic nodes for the LangGraph workflow."""
    
    def __init__(self, prompter: UnifiedPrompter, tools: Any, sampling_callback=None):
        self.prompter = prompter
        self.tools = tools
        self.sampling_callback = sampling_callback
        
    def _call_llm(self, agent_name: str, state: HarnessState) -> str:
        """Invokes the actual LLM configuration for the agent.
        
        This uses the real configuration rather than hardcoded mock facades.
        In environments without API keys, allow_mock_fallback safely degrades.
        """
        system_msg = self.prompter.build_system_message(agent_name)
        user_msg = self.prompter.build_user_message(state)
        
        # If MCP sampling is enabled, delegate generation to the IDE client
        if self.sampling_callback:
            try:
                res = self.sampling_callback(system_msg, user_msg)
                if res:
                    return res
            except Exception as e:
                import sys
                print(f"Sampling failed, falling back to local prompter: {e}", file=sys.stderr)

        provider = os.getenv("HARNESS_LLM_PROVIDER", "gemini")
        model = os.getenv("HARNESS_LLM_MODEL", "gemini-1.5-flash")
        
        # Determine the correct API key for the selected provider
        api_key = None
        if provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")

        config = GeminiLlmPrompterConfig(
            bundle_name="harness", 
            provider=provider, 
            research_gemini_model=model,
            synthesis_gemini_model=model,
            api_key=api_key,
            allow_mock_fallback=(provider == "gemini" and not api_key)
        )
        llm_prompter = GeminiLlmPrompter(config=config, fs_manager=None)
        
        conversation = llm_prompter._create_single_conversation(
            system_prompt=system_msg,
            agent_name=agent_name,
            output_schema_type=None
        )
        return conversation.prompt(user_msg)
        
    def planner_node(self, state: HarnessState) -> Dict[str, Any]:
        """Planner node: Decomposes the user prompt into milestones.
        
        Calls the planner LLM and attempts to parse a structured
        milestone list from the response. Falls back to a single
        milestone wrapping the user prompt on parse failure.
        """
        response = self._call_llm("planner", state)

        # Attempt to parse structured milestone list from LLM output
        milestones = [{"id": 1, "task": state.get("user_prompt", "Complete task")}]
        try:
            parsed = json.loads(response)
            if isinstance(parsed, list) and parsed:
                milestones = parsed
            elif isinstance(parsed, dict) and "milestones" in parsed:
                milestones = parsed["milestones"]
        except (json.JSONDecodeError, TypeError):
            pass  # Fall back to single-milestone default

        return {
            "milestones": milestones,
            "status": "planned",
            "step_history": (state.get("step_history") or []) + ["planner:planned"]
        }

    def architect_node(self, state: HarnessState) -> Dict[str, Any]:
        """Architect node: Develops strategy and identifies context."""
        response = self._call_llm("architect", state)
        
        # Heuristic: Extract file paths from the architect's response
        words = response.split()
        paths_to_fetch = [w for w in words if "." in w and ("/" in w or w.endswith(".py") or w.endswith(".md"))]
        
        verified_context = []
        for path in set(paths_to_fetch):
            clean_path = path.strip(".,()[]'\"")
            # Only fetch if it looks like a real path in the workspace
            if os.path.exists(clean_path):
                ctx = self.tools.get_verified_context(clean_path)
                verified_context.append(ctx)
        
        return {
            "implementation_strategy": response,
            "verified_context": verified_context,
            "status": "architected",
            "step_history": (state.get("step_history") or []) + ["architect:architected"]
        }

    def adversarial_verifier_node(self, state: HarnessState) -> Dict[str, Any]:
        """Adversarial Verifier node: Audits the architect's plan (Goldfish Protocol).
        
        Parses the adversary's response for risk_level and logical_flaws.
        Falls back to "low" risk if the response is unstructured.
        """
        response = self._call_llm("adversary", state)

        # Parse structured audit output from the adversary LLM
        logical_flaws = []
        risk_level = "low"
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict):
                logical_flaws = parsed.get("logical_flaws", [])
                risk_level = parsed.get("risk_level", "low")
        except (json.JSONDecodeError, TypeError):
            pass  # Unstructured response defaults to low risk

        return {
            "logical_flaws": logical_flaws,
            "risk_level": risk_level,
            "status": "audit_passed" if risk_level != "high" else "audit_flagged",
            "step_history": (state.get("step_history") or []) + [
                f"adversary:{'audit_passed' if risk_level != 'high' else 'audit_flagged'}"
            ]
        }

    def implementer_node(self, state: HarnessState) -> Dict[str, Any]:
        """Implementer node: Writes the actual code and generates diffs.
        
        Parses the implementer's response for generated_diffs and
        provisional_summaries. Falls back to empty dicts if the
        response is unstructured text.
        """
        response = self._call_llm("implementer", state)

        # Parse structured implementation output from LLM
        generated_diffs = {}
        provisional_summaries = {}
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict):
                generated_diffs = parsed.get("generated_diffs", {})
                provisional_summaries = parsed.get("provisional_summaries", {})
        except (json.JSONDecodeError, TypeError):
            pass  # Unstructured response — no diffs to extract

        return {
            "generated_diffs": generated_diffs,
            "provisional_summaries": provisional_summaries,
            "status": "implemented",
            "step_history": (state.get("step_history") or []) + ["implementer:implemented"]
        }

    def reviewer_node(self, state: HarnessState) -> Dict[str, Any]:
        """Reviewer node: 10-line mean code review.
        
        When review_retry_count >= max_retries, emits escalation_reason so
        the data exists in state BEFORE interrupt_before fires on the human node.
        """
        response = self._call_llm("reviewer", state)
        
        passed = False
        review_findings = []
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict):
                passed = parsed.get("passed", False)
                review_findings = parsed.get("review_findings", [])
            else:
                review_findings = [{"issue": "Reviewer response was not a JSON object."}]
        except json.JSONDecodeError:
            review_findings = [{"issue": "Failed to parse reviewer response as JSON."}]
            
        # If the review fails, increment retry counter. On max retries,
        # emit escalation_reason — the interrupt fires BEFORE the human node,
        # so this data must already be in state when the graph pauses.
        if not passed:
            retry_count = state.get("review_retry_count", 0) + 1
            max_retries = state.get("max_retries", 3)
            result = {
                "review_findings": review_findings,
                "status": "review_failed",
                "review_retry_count": retry_count,
                "step_history": (state.get("step_history") or []) + ["reviewer:review_failed"]
            }
            if retry_count >= max_retries:
                findings_summary = "; ".join(
                    f.get("issue", str(f)) if isinstance(f, dict) else str(f)
                    for f in review_findings[:5]
                )
                result["escalation_reason"] = (
                    f"Review loop exhausted after {retry_count} retries. "
                    f"Findings: {findings_summary}"
                )
            return result
            
        return {
            "review_findings": [],
            "status": "review_passed",
            "review_retry_count": 0,
            "step_history": (state.get("step_history") or []) + ["reviewer:review_passed"]
        }

    def verifier_node(self, state: HarnessState) -> Dict[str, Any]:
        """Verifier node: Final QA and regression testing.
        
        When verify_retry_count >= max_retries, emits escalation_reason so
        the data exists in state BEFORE interrupt_before fires on the human node.
        """
        response = self._call_llm("verifier", state)
        
        passed = False
        issues = []
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict):
                passed = parsed.get("passed", False)
                issues = parsed.get("issues", [])
            else:
                issues = ["Verifier response was not a JSON object."]
        except json.JSONDecodeError:
            issues = ["Failed to parse verifier response as JSON."]
            
        # If QA fails, increment retry counter. On max retries,
        # emit escalation_reason for the human interrupt.
        if not passed:
            retry_count = state.get("verify_retry_count", 0) + 1
            max_retries = state.get("max_retries", 3)
            result = {
                "verification_verdict": {"passed": False, "issues": issues},
                "status": "verification_failed",
                "verify_retry_count": retry_count,
                "step_history": (state.get("step_history") or []) + ["verifier:verification_failed"]
            }
            if retry_count >= max_retries:
                issues_summary = "; ".join(str(i) for i in issues[:5])
                result["escalation_reason"] = (
                    f"Verification loop exhausted after {retry_count} retries. "
                    f"Issues: {issues_summary}"
                )
            return result
            
        return {
            "verification_verdict": {"passed": True, "issues": []},
            "status": "verification_passed",
            "verify_retry_count": 0,
            "step_history": (state.get("step_history") or []) + ["verifier:verification_passed"]
        }

    def human_node(self, state: HarnessState) -> Dict[str, Any]:
        """Human-in-the-loop node: Runs AFTER resume injects human_feedback.
        
        Resets both retry counters so the human can iterate without
        artificial barriers. The interrupt fires BEFORE this node on
        every visit — this node only executes once the caller resumes.
        """
        return {
            "status": "human_reviewed",
            "human_feedback": state.get("human_feedback", ""),
            "review_retry_count": 0,
            "verify_retry_count": 0,
            "step_history": (state.get("step_history") or []) + ["human:reviewed"]
        }
