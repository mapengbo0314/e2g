"""Helpers for generating repair or error-analysis prompts."""

from typing import List, Union, Dict


class IndexerErrorPromptGenerator:
    """Generates repair prompts for indexing failures, including verification issues."""

    def generate_error_prompt(self, error_message: str, issues: List[Union[str, Dict]] | None = None) -> str:
        """Generates a prompt explaining what failed and asking the LLM to fix it.
        
        Args:
            error_message: The raw error message from the pipeline or LLM.
            issues: A list of verification issues. Can be raw strings or structured dicts.
        """
        
        prompt = (
            "Your previous attempt to generate the index failed validation or verification.\n"
            "You MUST fix the following errors in your next response. Do not hallucinate claims.\n\n"
        )
        
        is_schema_failure = False
        if issues:
            # Check if any issues look like schema violations (syntactic)
            is_schema_failure = any("Schema violation" in str(i) or "Syntactic" in str(i) for i in issues)
            
            if is_schema_failure:
                prompt += "=== SCHEMA / SYNTACTIC ISSUES ===\n"
                prompt += "Your JSON structure is invalid or missing required nested objects.\n"
            else:
                prompt += "=== VERIFICATION / SEMANTIC ISSUES ===\n"
            
            for idx, issue in enumerate(issues, 1):
                if isinstance(issue, dict):
                    category = issue.get("category", "General")
                    msg = issue.get("message", str(issue))
                    prompt += f"{idx}. [{category}] {msg}\n"
                else:
                    prompt += f"{idx}. {issue}\n"
            prompt += "\n"
            
        prompt += f"=== CONTEXTUAL ERROR ===\n{error_message}\n\n"
        
        # Conclude with a clear directive.
        if issues and is_schema_failure:
            prompt += (
                "Please fix the structural issues first. Ensure all wrapper objects like "
                "'key_dependencies' are present even if their internal lists are empty. "
                "Do NOT include a top-level 'properties' key.\n"
            )
        else:
            prompt += (
                "Please try again. Focus on fixing the reported issues. "
                "Ensure every claim is grounded in the provided source code.\n"
            )
        
        return prompt
