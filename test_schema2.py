import json
from indexing.schema import IndexDocument, KeyComponentsDocument
import pydantic

class MyModel(pydantic.BaseModel):
    properties: KeyComponentsDocument

try:
    doc = MyModel.model_validate_json('{"properties": {"key_dependencies": {}}}')
    print("Success MyModel")
except pydantic.ValidationError as e:
    for err in e.errors():
        print(f"Error at {err['loc']}: {err['msg']}")

try:
    doc = IndexDocument.model_validate_json('{"properties": {"key_dependencies": {}}}')
    print("Success IndexDocument")
except pydantic.ValidationError as e:
    for err in e.errors():
        print(f"Error IndexDocument at {err['loc']}: {err['msg']}")

