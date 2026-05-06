
import pydantic
from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo
from typing import List, Optional, Any
import gc

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
    # Using a unique name to ensure we see the leak if it exists
    # In the actual code it uses model_cls.__name__ + "Stripped" (constant)
    return create_model(model_cls.__name__ + "Stripped", **fields, __base__=model_cls)

def test_leak_constant_name():
    print(f"--- Constant Name Test ---")
    print(f"Initial subclasses: {len(IndexDocument.__subclasses__())}")
    for i in range(100):
        _strip_defaults_from_model(IndexDocument)
    print(f"Subclasses after 100 calls (same name): {len(IndexDocument.__subclasses__())}")
    gc.collect()
    print(f"Subclasses after GC: {len(IndexDocument.__subclasses__())}")

def test_leak_unique_name():
    print(f"\n--- Unique Name Test ---")
    class Base2(BaseModel): pass
    print(f"Initial subclasses: {len(Base2.__subclasses__())}")
    for i in range(100):
        fields = {"f": (int, FieldInfo())}
        create_model(f"Model{i}", **fields, __base__=Base2)
    print(f"Subclasses after 100 calls (unique names): {len(Base2.__subclasses__())}")

def test_nested_complex():
    print(f"\n--- Nested Complex Test ---")
    class Inner(BaseModel):
        val: str = "default"
    
    class Outer(BaseModel):
        inner: Optional[Inner] = None
        inners: List[Inner] = Field(default_factory=list)

    stripped = _strip_defaults_from_model(Outer)
    schema = stripped.model_json_schema()
    
    import json
    # Look for 'default' in the schema
    schema_str = json.dumps(schema)
    if '"default":' in schema_str:
        print("FAIL: 'default' found in schema!")
        # Print where it is
        for name, definition in schema.get("$defs", {}).items():
            if "default" in json.dumps(definition):
                print(f"  Found in $defs.{name}")
    else:
        print("SUCCESS: No 'default' found (unlikely)")

if __name__ == "__main__":
    test_leak_constant_name()
    test_leak_unique_name()
    test_nested_complex()
