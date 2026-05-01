import json
from indexing import schema

print(json.dumps(schema.IndexDocument.model_json_schema(), indent=2))

