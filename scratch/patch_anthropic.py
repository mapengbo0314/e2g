import re

with open("indexing/sequential_llm_prompter.py", "r") as f:
    content = f.read()

anthropic_init_old = """        self.client = anthropic.Anthropic(api_key=api_key)
        
        self.model_name = model_name"""

anthropic_init_new = """        self.client = anthropic.Anthropic(api_key=api_key)
        self.instructor_client = instructor.from_anthropic(self.client)
        self.model_name = model_name"""

content = content.replace(anthropic_init_old, anthropic_init_new)

def replace_anthropic_prompt(content):
    pattern = rf"(class AnthropicConversation:.*?    def prompt\(self, user_prompt: str\) -> PromptResult:\n)(.*?)(    def get_state)"
    match = re.search(pattern, content, re.DOTALL)
    if not match: return content
    prefix = match.group(1)
    suffix = match.group(3)
    
    new_prompt = """        start_time = time.time()
        self.history.append({"role": "user", "content": user_prompt})
        
        usage = {}
        if self.output_schema_type:
            response = self.instructor_client.messages.create(
                model=self.model_name,
                max_tokens=16384,
                system=self.system_prompt,
                messages=self.history,
                response_model=self.output_schema_type,
            )
            latency_ms = int((time.time() - start_time) * 1000)
            text = response.model_dump_json()
            self._last_response = response
            
            if hasattr(response, "_raw_response") and hasattr(response._raw_response, "usage"):
                usage_obj = response._raw_response.usage
                usage = {
                    "input_tokens": getattr(usage_obj, "input_tokens", 0),
                    "output_tokens": getattr(usage_obj, "output_tokens", 0),
                    "total_tokens": getattr(usage_obj, "input_tokens", 0) + getattr(usage_obj, "output_tokens", 0),
                }
        else:
            response = self.client.messages.create(
                model=self.model_name,
                system=self.system_prompt,
                messages=self.history,
                max_tokens=16384
            )
            latency_ms = int((time.time() - start_time) * 1000)
            text = response.content[0].text
            self.history.append({"role": "assistant", "content": text})
            self._last_response = text
            if hasattr(response, "usage"):
                usage_obj = response.usage
                usage = {
                    "input_tokens": getattr(usage_obj, "input_tokens", 0),
                    "output_tokens": getattr(usage_obj, "output_tokens", 0),
                    "total_tokens": getattr(usage_obj, "input_tokens", 0) + getattr(usage_obj, "output_tokens", 0),
                }
                
        return PromptResult(text=text, usage=usage, latency_ms=latency_ms)\n\n"""
        
    return content[:match.start()] + prefix + new_prompt + suffix + content[match.end():]

content = replace_anthropic_prompt(content)
with open("indexing/sequential_llm_prompter.py", "w") as f: f.write(content)
