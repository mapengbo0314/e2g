import json
from indexing.schema import KeyComponentsDocument, KeyDependencies
import pydantic

try:
    doc = KeyComponentsDocument.model_validate_json('{"key_dependencies": {}}')
    print("Success:", doc)
except pydantic.ValidationError as e:
    for err in e.errors():
        print(f"Error at {err['loc']}: {err['msg']}")

try:
    doc = KeyDependencies.model_validate_json('{}')
    print("Success KeyDependencies:", doc)
except pydantic.ValidationError as e:
    print("KeyDependencies Error:", e)

