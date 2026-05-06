import re

with open("indexing/sequential_llm_prompter.py", "r") as f:
    content = f.read()

ollama_init_old = """    def __init__(
        self,
        system_prompt: str,
        model_name: str,
        output_schema_type: type[Any] | None = None,
    ):
        if ollama is None:
            raise ImportError("ollama library not found. Install ollama.")
        self.model_name = model_name
        
        self.output_schema_type = output_schema_type
        self.history = [{"role": "system", "content": system_prompt}] if system_prompt else []
        self._last_response: Any = None"""

ollama_init_new = """    def __init__(
        self,
        system_prompt: str,
        model_name: str,
        output_schema_type: type[Any] | None = None,
    ):
        if ollama is None:
            raise ImportError("ollama library not found. Install ollama.")
        
        from openai import OpenAI
        import instructor
        self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self.instructor_client = instructor.from_openai(self.client, mode=instructor.Mode.JSON)
        
        self.model_name = model_name
        self.output_schema_type = output_schema_type
        self.history = [{"role": "system", "content": system_prompt}] if system_prompt else []
        self._last_response: Any = None"""

content = content.replace(ollama_init_old, ollama_init_new)

def replace_ollama_prompt(content):
    pattern = rf"(class OllamaConversation:.*?    def prompt\(self, user_prompt: str\) -> PromptResult:\n)(.*?)(    def get_state)"
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
            
            if hasattr(response, "_raw_response") and hasattr(response._raw_response, "usage") and response._raw_response.usage:
                usage = {
                    "input_tokens": response._raw_response.usage.prompt_tokens,
                    "output_tokens": response._raw_response.usage.completion_tokens,
                    "total_tokens": response._raw_response.usage.total_tokens,
                }
        else:
            kwargs = {
                "model": self.model_name,
                "messages": self.history,
                "options": {
                    "num_ctx": 131072,
                },
            }
            response = ollama.chat(**kwargs)
            latency_ms = int((time.time() - start_time) * 1000)
            text = response['message']['content']
            self.history.append({"role": "assistant", "content": text})
            self._last_response = text
                
        return PromptResult(text=text, usage=usage, latency_ms=latency_ms)\n\n"""
        
    return content[:match.start()] + prefix + new_prompt + suffix + content[match.end():]

content = replace_ollama_prompt(content)
with open("indexing/sequential_llm_prompter.py", "w") as f: f.write(content)
