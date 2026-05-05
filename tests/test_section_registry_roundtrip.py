"""Round-trip tests for all registered sections in the SectionRegistry."""

import json
from indexing import section_registry
from indexing import schema
from indexing import rendering

def _generate_mock_section_data(spec: section_registry.SectionSpec) -> dict:
    """Generates valid mock data for a section based on its spec."""
    data = {}
    if spec.content_field:
        data[spec.content_field] = f"Mock content for {spec.section_id}"
    elif spec.list_field:
        # Generate a generic item based on the section id
        if spec.section_id == "key_individual_components":
            data[spec.list_field] = [{"name": "mock.py", "description": "Mock component"}]
        elif spec.section_id == "key_interfaces":
            data[spec.list_field] = [{"name": "MockInterface", "description": "Mock interface"}]
        elif spec.section_id == "key_dependencies":
            data[spec.list_field] = [{"name": "mock-dep", "description": "Mock dependency"}]
        elif spec.section_id == "configurations":
            data[spec.list_field] = [{"name": "MOCK_CONFIG", "description": "Mock config", "definition_link": "link"}]
        elif spec.section_id == "blueprint":
            data[spec.list_field] = [{"name": "MockSymbol", "signature": "def mock()", "description": "Mock symbol", "summary": "mock summary"}]
        elif spec.section_id == "implementation_invariants":
            data[spec.list_field] = [{"name": "MockInvariant", "description": "Mock invariant", "primitive": "mock_primitive", "intent": "mock intent", "usage_context": "mock context"}]
        elif spec.section_id == "workflow_patterns":
            data[spec.list_field] = [{"name": "MockItem", "description": "Mock item", "framework": "mock framework"}]
        elif spec.section_id == "tech_debt":
            data[spec.list_field] = [{"name": "MockDebt", "description": "Mock debt", "category": "MOCK", "impact": "High"}]
    else:
        # Shouldn't happen unless we have a section without content_field or list_field
        pass
    return data

def test_all_registered_sections_roundtrip():
    """Ensure every registered section can be serialized, deserialized, and rendered."""
    
    # 1. Producer output (dict)
    raw_dict = {}
    for spec in section_registry.SECTION_SPECS:
        raw_dict[spec.section_id] = _generate_mock_section_data(spec)
        
    # Add mandatory metadata
    raw_dict["generation_metadata"] = {
        "model_name": "test-model",
        "epoch": 1,
        "generated_at": "2026-01-01T00:00:00Z"
    }
    raw_dict["verification_state"] = {
        "verified": True,
        "verification_model": "test-model",
        "verified_at": "2026-01-01T00:00:00Z",
        "confidence": 1.0,
        "issues": []
    }

    # 2. Serialization/Deserialization
    json_str = json.dumps(raw_dict)
    try:
        doc = schema.IndexDocument.model_validate_json(json_str)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise AssertionError(f"Failed to validate JSON: {e}")

    # 3. Readback (check properties)
    for spec in section_registry.SECTION_SPECS:
        section_instance = getattr(doc, spec.section_id, None)
        assert section_instance is not None, f"Section {spec.section_id} is missing from document."
        
        # Verify it has content
        is_empty = section_registry.is_section_empty(spec.section_id, section_instance)
        assert not is_empty, f"Section {spec.section_id} was evaluated as empty after deserialization."

    # 4. Markdown Rendering
    md = rendering.to_markdown(doc)
    assert md is not None and len(md) > 0
    
    # Simple check: verify every section's title or mock data appears in the markdown
    for spec in section_registry.SECTION_SPECS:
        if spec.content_field:
            assert f"Mock content for {spec.section_id}" in md, f"Mock content not found for {spec.section_id}."
        elif spec.list_field:
            assert "Mock" in md, f"Mock data for {spec.section_id} not rendered."
