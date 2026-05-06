import typing
from typing import List
from pydantic import BaseModel

class MyModel(BaseModel):
    queries: List[str]

def _strip_annotation(ann):
    origin = typing.get_origin(ann)
    args = typing.get_args(ann)
    print(f"DEBUG: ann={ann}, origin={origin}, args={args}")
    
    if origin is typing.Union:
        new_args = tuple(_strip_annotation(a) for a in args)
        return typing.Union[new_args]
    elif origin is list or origin is getattr(typing, 'list', None) or origin is List:
        if args:
            new_args = tuple(_strip_annotation(a) for a in args)
            print(f"DEBUG LIST: returning List[{new_args[0]}]")
            return List[new_args[0]]
        return List
    elif isinstance(ann, type):
        return ann
    return ann

print("Original:", MyModel.model_fields["queries"].annotation)
print("Stripped:", _strip_annotation(MyModel.model_fields["queries"].annotation))
