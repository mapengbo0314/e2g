import re

with open("indexing/sequential_llm_prompter.py", "r") as f:
    content = f.read()

def replace_prompt_method(class_name, content):
    pattern = rf"(class {class_name}.*?    def prompt\(self, user_prompt: str\) -> PromptResult:\n)(.*?)(    def get_state)"
    
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print(f"Could not find prompt for {class_name}")
        return content
        
    prefix = match.group(1)
    suffix = match.group(3)
    
    new_prompt = """        start_time = time.time()
        self.history.append({"role": "user", "content": user_prompt})
        
        latency_ms = 0
        usage = {}
        
        if self.output_schema_type:
            response = self.instructor_client.chat.completions.create(
                model=self.model_name,
                messages=self.history,
                response_model=self.output_schema_type,
            )
            latency_ms = int((time.time() - start_time) * 1000)
            text = response.model_dump_json()
            self._last_response = response
        else:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
            )
            latency_ms = int((time.time() - start_time) * 1000)
            text = response.text
            self._last_response = text
            if hasattr(response, "usage_metadata"):
                usage_metadata = response.usage_metadata
                usage = {
                    "input_tokens": getattr(usage_metadata, "prompt_token_count", 0),
                    "output_tokens": getattr(usage_metadata, "candidates_token_count", 0),
                    "total_tokens": getattr(usage_metadata, "total_token_count", 0),
                }

        return PromptResult(text=text, usage=usage, latency_ms=latency_ms)\n\n"""
        
    return content[:match.start()] + prefix + new_prompt + suffix + content[match.end():]

content = replace_prompt_method("VertexAiConversation", content)
content = replace_prompt_method("GoogleAiConversation", content)

with open("indexing/sequential_llm_prompter.py", "w") as f:
    f.write(content)
