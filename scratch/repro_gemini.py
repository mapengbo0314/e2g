import asyncio
from indexing.sequential_llm_prompter import GoogleAiConversation
from indexing.schema import ResearchPlan
import os

def test():
    # If the workspace has GEMINI_API_KEY we'll use it
    # Otherwise this might fail with auth error, but we want to see if there's a Pydantic/Instructor schema error
    api_key = os.environ.get("GEMINI_API_KEY", "dummy_key")
    
    conv = GoogleAiConversation(
        system_prompt="You are a test agent.",
        model_name="gemini-2.5-flash",
        api_key=api_key,
        output_schema_type=ResearchPlan
    )
    
    try:
        res = conv.prompt("Give me a research plan.")
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
