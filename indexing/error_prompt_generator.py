"""Helpers for generating repair or error-analysis prompts."""

from typing import List


class IndexerErrorPromptGenerator:
    """Generates repair prompts for indexing failures, including verification issues."""

    def generate_error_prompt(self, error_message: str, issues: List[str] | None = None) -> str:
        """Generates a prompt explaining what failed and asking the LLM to fix it."""
        
        prompt = (
            "Your previous attempt to generate the index failed validation.\n"
            "You MUST fix the following errors to proceed. Do not hallucinate claims or hallucinate dependencies.\n\n"
        )
        
        if issues:
            prompt += "=== VERIFICATION ISSUES ===\n"
            for idx, issue in enumerate(issues, 1):
                prompt += f"{idx}. {issue}\n"
            prompt += "\n"
            
        prompt += f"=== ERROR MESSAGE ===\n{error_message}\n\n"
        prompt += "Please try again, paying close attention to the errors above and ONLY using facts supported by the source context.\n"
        
        return prompt
