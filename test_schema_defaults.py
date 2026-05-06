from indexing.schema import KeyComponentsDocument, strip_defaults_for_gemini
import json

Stripped = strip_defaults_for_gemini(KeyComponentsDocument)
schema = Stripped.model_json_schema()
print("Does schema contain 'default'? ", "default" in json.dumps(schema))
