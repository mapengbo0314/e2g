import json
from indexing.schema import IndexDocument
import pydantic

try:
    doc = IndexDocument.model_validate_json('{"overview": {"content": "foo"}, "key_dependencies": {}}')
    print("Success IndexDocument")
except pydantic.ValidationError as e:
    for err in e.errors():
        print(f"Error IndexDocument at {err['loc']}: {err['msg']}")

