
import json
import logging
from typing import Any, List, Optional
import pydantic

# Mock the schema from schema.py
class _BaseModel(pydantic.BaseModel):
    pass

class Overview(_BaseModel):
    content: str

class OverviewDocument(_BaseModel):
    overview: Overview

# Mock the coercion logic from sequential_llm_prompter.py
class MockPrompter:
    @staticmethod
    def _coerce_for_schema(data: Any, output_schema: type[Any]) -> Any:
        # Determine which fields are required
        required_fields = set()
        if hasattr(output_schema, "model_fields"):  # Pydantic v2
            from pydantic_core import PydanticUndefined
            for name, field in output_schema.model_fields.items():
                if field.default is PydanticUndefined and field.default_factory is None:
                    required_fields.add(name)
        
        # Original logic for root wrapping
        # (Simplified for this test)
        
        # --- NEW PROPOSED LOGIC ---
        # --- Phase 0.7: Coerce string-valued sections to dicts ---
        # Handle cases where "overview": "string" instead of "overview": {"content": "string"}
        for section_key in ["overview", "deep_dive"]:
            if section_key in data and isinstance(data[section_key], str):
                print(f"[Coercion] Coerced string value for '{section_key}' to dict with 'content' key.")
                data[section_key] = {"content": data[section_key]}
        # --------------------------
        
        return data

def test_validation():
    # This is what the LLM returned according to the log
    parsed_output = {
        "overview": "The src/components directory hous...ic into reusable units."
    }
    
    print(f"Input data: {parsed_output}")
    
    # Apply coercion
    coerced_data = MockPrompter._coerce_for_schema(parsed_output, OverviewDocument)
    print(f"Coerced data: {coerced_data}")
    
    # Validate
    try:
        doc = OverviewDocument.model_validate(coerced_data)
        print("Validation PASSED")
        print(f"Result: {doc}")
    except pydantic.ValidationError as e:
        print("Validation FAILED")
        print(e)

if __name__ == "__main__":
    test_validation()
