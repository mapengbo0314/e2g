import pydantic
from typing import *
from indexing import schema
print("Original:", schema.ResearchPlan.model_json_schema())
stripped = schema.strip_defaults_for_gemini(schema.ResearchPlan)
print("Stripped:", stripped.model_json_schema())
print("Annotations:")
for name, field in stripped.model_fields.items():
    print(f"  {name}: {field.annotation}")
