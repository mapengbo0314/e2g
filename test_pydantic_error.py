import json
from indexing import schema

data = {
    "overview": {"content": "test"},
    "key_dependencies": {}
}

try:
    schema.IndexDocument.model_validate(data)
    print("Success")
except Exception as e:
    import pydantic
    if isinstance(e, pydantic.ValidationError):
        for err in e.errors():
            loc = ".".join(str(l) for l in err["loc"])
            print(f"Schema error at '{loc}': {err['msg']}")
    else:
        print("Other error:", e)

