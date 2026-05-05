import re

with open("indexing/sequential_llm_prompter.py", "r") as f:
    content = f.read()

# 1. Add PromptResult
prompt_result = """
@dataclasses.dataclass
class PromptResult:
    text: str
    usage: dict[str, Any]
    provider_response_id: str | None = None

"""
content = re.sub(
    r'(@dataclasses\.dataclass\nclass _SimpleConversation:)',
    prompt_result + r'\1',
    content
)

# 2. Update _SimpleConversation
content = re.sub(
    r'def prompt\(self, user_prompt: str\) -> str:\n        if self\.state is None:\n            payload = self\._build_default_output\(user_prompt\)\n            self\.state = payload\n        if hasattr\(self\.state, "model_dump_json"\):\n            # Use Pydantic\'s optimized JSON serialization if available\.\n            return self\.state\.model_dump_json\(indent=2\)\n        return json\.dumps\(self\.state, indent=2, default=str\)',
    'def prompt(self, user_prompt: str) -> PromptResult:\n        if self.state is None:\n            payload = self._build_default_output(user_prompt)\n            self.state = payload\n        text = self.state.model_dump_json(indent=2) if hasattr(self.state, "model_dump_json") else json.dumps(self.state, indent=2, default=str)\n        return PromptResult(text=text, usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})',
    content
)

with open("indexing/sequential_llm_prompter.py", "w") as f:
    f.write(content)
