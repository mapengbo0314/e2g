import typing
from typing import List, Dict, Union
from pydantic import BaseModel

class TestModel(BaseModel):
    queries: List[str]
    name: str

def _strip_annotation(ann):
    origin = typing.get_origin(ann)
    args = typing.get_args(ann)
    
    if origin is Union:
        new_args = tuple(_strip_annotation(a) for a in args)
        return Union[new_args]
    elif origin in (list, getattr(typing, 'List', None), List) and origin is not None:
        if args:
            new_args = tuple(_strip_annotation(a) for a in args)
            return List[new_args[0]]
        return List
    elif origin in (dict, getattr(typing, 'Dict', None), Dict) and origin is not None:
        if args:
            new_args = tuple(_strip_annotation(a) for a in args)
            return Dict[new_args[0], new_args[1]]
        return Dict
    elif isinstance(ann, type):
        return ann
    return ann

print("List[str] ->", _strip_annotation(TestModel.model_fields["queries"].annotation))
print("str ->", _strip_annotation(TestModel.model_fields["name"].annotation))
