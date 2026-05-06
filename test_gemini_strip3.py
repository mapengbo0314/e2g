import typing
from typing import List, Dict, Optional, Union, Any, Literal
from pydantic import BaseModel

class MyModel(BaseModel):
    queries: List[str]

def _strip_annotation(ann):
    origin = typing.get_origin(ann)
    args = typing.get_args(ann)
    
    if origin is Union:
        new_args = tuple(_strip_annotation(a) for a in args)
        return Union[new_args]
    elif origin is list or origin is getattr(typing, 'list', None) or origin is List:
        if args:
            new_args = tuple(_strip_annotation(a) for a in args)
            return List[new_args[0]]
        return List
    elif origin is dict or origin is getattr(typing, 'dict', None) or origin is Dict:
        if args:
            new_args = tuple(_strip_annotation(a) for a in args)
            return Dict[new_args[0], new_args[1]]
        return Dict
    elif isinstance(ann, type):
        return ann
    return ann

print("Original:", MyModel.model_fields["queries"].annotation)
print("Stripped:", _strip_annotation(MyModel.model_fields["queries"].annotation))
