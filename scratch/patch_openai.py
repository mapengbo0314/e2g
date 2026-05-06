import re

with open("indexing/sequential_llm_prompter.py", "r") as f:
    content = f.read()

openai_init_old = """        self.client = openai.Client(api_key=api_key)
        
        self.model_name = model_name"""

openai_init_new = """        self.client = openai.Client(api_key=api_key)
        self.instructor_client = instructor.from_openai(self.client)
        self.model_name = model_name"""

content = content.replace(openai_init_old, openai_init_new)

def replace_openai_prompt(content):
    pattern = rf"(class OpenAiConversation:.*?    def prompt\(self, user_prompt: str\) -> PromptResult:\n)(.*?)(    def get_state)"
    match = re.search(pattern, content, re.DOTALL)
    if not match: return content
    prefix = match.group(1)
    suffix = match.group(3)
    
    new_prompt = """        start_time = time.time()
        self.history.append({"role": "user", "content": user_prompt})
        
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
            provider_response_id = getattr(response, "id", None)
            # Usage might not be directly on the instructor response depending on version, 
            # but usually it passes through _raw_response.
            if hasattr(response, "_raw_response") and hasattr(response._raw_response, "usage") and response._raw_response.usage:
                usage = {
                    "input_tokens": response._raw_response.usage.prompt_tokens,
                    "output_tokens": response._raw_response.usage.completion_tokens,
                    "total_tokens": response._raw_response.usage.total_tokens,
                }
        else:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.history,
            )
            latency_ms = int((time.time() - start_time) * 1000)
            text = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": text})
            self._last_response = text
            provider_response_id = response.id
            if response.usage:
                usage = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                
        return PromptResult(text=text, usage=usage, provider_response_id=provider_response_id, latency_ms=latency_ms)\n\n"""
        
    return content[:match.start()] + prefix + new_prompt + suffix + content[match.end():]

content = replace_openai_prompt(content)
with open("indexing/sequential_llm_prompter.py", "w") as f: f.write(content)
