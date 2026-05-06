
import time
from typing import List, Optional
from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo
import json

class DeepNested(BaseModel):
    info: str = "default"

class Nested(BaseModel):
    deep: DeepNested = Field(default_factory=DeepNested)
    values: List[int] = Field(default_factory=list)

class ComplexModel(BaseModel):
    nested: Nested = Field(default_factory=Nested)
    optional_nested: Optional[Nested] = None
    flags: List[bool] = []
    
def _strip_defaults_from_model(model_cls):
    fields = {}
    for name, field in model_cls.model_fields.items():
        new_field_info = FieldInfo(
            annotation=field.annotation,
            description=field.description,
        )
        fields[name] = (field.annotation, new_field_info)
    return create_model(model_cls.__name__ + "Stripped", **fields, __base__=model_cls)


def profile():
    start = time.time()
    for i in range(1000):
        stripped = _strip_defaults_from_model(ComplexModel)
        schema = stripped.model_json_schema()
    end = time.time()
    print(f"1000 iterations took {end - start:.4f} seconds")

if __name__ == "__main__":
    profile()
