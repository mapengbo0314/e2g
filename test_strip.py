from typing import Optional, List, Union, Dict
from pydantic import BaseModel, Field
import functools
from pydantic import create_model
from pydantic.fields import FieldInfo
import typing

@functools.lru_cache(maxsize=None)
def strip_defaults_for_gemini(model_cls: type[BaseModel]) -> type[BaseModel]:
    fields = {}
    for name, field in model_cls.model_fields.items():
        annotation = field.annotation
        
        def _strip_annotation(ann):
            origin = typing.get_origin(ann)
            args = typing.get_args(ann)
            
            if origin is Union:
                new_args = tuple(_strip_annotation(a) for a in args)
                return Union[new_args]
            elif origin is list or origin is List:
                if args:
                    new_args = tuple(_strip_annotation(a) for a in args)
                    return List[new_args[0]]
                return List
            elif origin is dict or origin is Dict:
                if args:
                    new_args = tuple(_strip_annotation(a) for a in args)
                    return Dict[new_args[0], new_args[1]]
                return Dict
            elif isinstance(ann, type) and issubclass(ann, BaseModel):
                return strip_defaults_for_gemini(ann)
            return ann

        new_annotation = _strip_annotation(annotation)

        new_field_info = FieldInfo(
            annotation=new_annotation,
            description=field.description,
        )
        fields[name] = (new_annotation, new_field_info)
        
    return create_model(model_cls.__name__ + "Stripped", **fields, __base__=model_cls)

class ConfigurationItem(BaseModel):
    comments: str = Field(default="")

class Configurations(BaseModel):
    configurations: Optional[List[ConfigurationItem]] = Field(default_factory=list)

Stripped = strip_defaults_for_gemini(Configurations)
import json
print(json.dumps(Stripped.model_json_schema(), indent=2))
print("Contains default?", "default" in json.dumps(Stripped.model_json_schema()))
