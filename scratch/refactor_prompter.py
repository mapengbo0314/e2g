import re

with open("indexing/sequential_llm_prompter.py", "r") as f:
    content = f.read()

# Remove _coerce_for_schema
content = re.sub(r'    @staticmethod\n    def _coerce_for_schema\(.*?\n        # --- Phase 2: Patch known missing keys with field-specific defaults ---.*?return data\n', '', content, flags=re.DOTALL)

# Let's just do a manual replace for the coercion call in _execute_single_prompt
old_execute = """                if isinstance(parsed_output, dict) and pydantic is not None:
                    parsed_output = self._coerce_for_schema(parsed_output, output_schema)
                    if hasattr(output_schema, 'model_validate'):
                        return output_schema.model_validate(parsed_output)
                    return parsed_output"""

new_execute = """                if isinstance(parsed_output, dict) and pydantic is not None:
                    if hasattr(output_schema, 'model_validate'):
                        return output_schema.model_validate(parsed_output)
                    return parsed_output
                if parsed_output is not None and not isinstance(parsed_output, (dict, str)):
                    return parsed_output"""

content = content.replace(old_execute, new_execute)

with open("indexing/sequential_llm_prompter.py", "w") as f:
    f.write(content)
