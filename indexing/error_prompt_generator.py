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
        
        if issues:
            prompt += "=== VERIFICATION ISSUES ===\n"
            for idx, issue in enumerate(issues, 1):
                if isinstance(issue, dict):
                    # Structured issue reporting
                    category = issue.get("category", "General")
                    msg = issue.get("message", str(issue))
                    prompt += f"{idx}. [{category}] {msg}\n"
                else:
                    prompt += f"{idx}. {issue}\n"
            # Add spacing after the list of verification issues.
            prompt += "\n"
            
        prompt += f"=== CONTEXTUAL ERROR ===\n{error_message}\n\n"
        # Conclude the prompt with an explicit directive for grounded re-generation.
        prompt += (
            "Please try again. Focus on the 'VERIFICATION ISSUES' above. "
            "Ensure every claim is grounded in the provided source code.\n"
        )
        
        return prompt
