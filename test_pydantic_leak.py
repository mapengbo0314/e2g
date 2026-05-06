
import pydantic
from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo
from typing import List, Optional

class Overview(BaseModel):
    content: str = Field(default="default overview")

class IndexDocument(BaseModel):
    overview: Overview = Field(default_factory=Overview)
    names: List[str] = Field(default_factory=list)

def _strip_defaults_from_model(model_cls):
    fields = {}
    for name, field in model_cls.model_fields.items():
        new_field_info = FieldInfo(
            annotation=field.annotation,
            description=field.description,
        )
        fields[name] = (field.annotation, new_field_info)
    return create_model(model_cls.__name__ + "Stripped", **fields, __base__=model_cls)

def test_leak():
    print(f"Initial subclasses of IndexDocument: {len(IndexDocument.__subclasses__())}")
    for i in range(100):
        _strip_defaults_from_model(IndexDocument)
    print(f"Subclasses after 100 calls: {len(IndexDocument.__subclasses__())}")

def test_nested():
    stripped = _strip_defaults_from_model(IndexDocument)
    print("\nSchema for stripped model:")
    import json
    print(json.dumps(stripped.model_json_schema(), indent=2))
    
    # Check if 'overview' field in stripped model still points to 'Overview' which has a default
    overview_field = stripped.model_fields['overview']
    print(f"\nOverview field annotation: {overview_field.annotation}")
    print(f"Overview schema: {json.dumps(Overview.model_json_schema(), indent=2)}")

if __name__ == "__main__":
    test_leak()
    test_nested()
