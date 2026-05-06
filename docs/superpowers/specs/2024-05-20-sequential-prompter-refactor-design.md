# Sequential LLM Prompter Refactor Design

## 1. Naming: Universal Prompter identity
The class `UniversalLlmPrompter` is currently a misnomer, as it fully supports OpenAI, Anthropic, and local Ollama backends. 
**Recommendation:** Rename `UniversalLlmPrompter` to `MultiProviderLlmPrompter` (or simply `UniversalLlmPrompter`), and `UniversalLlmConfig` to `LlmPrompterConfig`. This accurately reflects its status as an abstraction layer over multiple LLM backends.

## 2. Dynamic Coercion: Eliminating Hardcoded Names
Currently, `_deep_replace_nulls` relies on a hardcoded set of `_STRING_KEYS` to convert `None` and `"N/A"` into empty strings (`""`). This is brittle and couples the prompter to specific schema fields.

**Design:** We will implement a dynamic schema traversal using Pydantic's metadata (`model_fields` in v2, or `__fields__` in v1) with a fallback to `__annotations__`. The function will walk the returned JSON dictionary and the schema type in tandem.

```python
import typing

def _unwrap_type(annotation: Any) -> Any:
    """Unwraps Optional[...] and Union[...] to find base types."""
    origin = typing.get_origin(annotation)
    if origin is typing.Union or getattr(origin, "__name__", "") == "UnionType":
        args = typing.get_args(annotation)
        # Filter out NoneType to get the real type
        non_none_args = [a for a in args if a is not type(None)]
        return non_none_args[0] if non_none_args else args[0]
    return annotation

def _coerce_nulls_dynamically(data: Any, schema_type: type[Any]) -> Any:
    if data is None or data == "N/A":
        # Only coerce strictly if the underlying type is str
        base_type = _unwrap_type(schema_type)
        if base_type is str:
            return ""
        return None

    if isinstance(data, list):
        # Extract the inner type of the List (e.g., List[Component] -> Component)
        origin = typing.get_origin(schema_type)
        if origin is list or origin is typing.List:
            args = typing.get_args(schema_type)
            item_type = args[0] if args else Any
            return [_coerce_nulls_dynamically(item, item_type) for item in data]
        return data

    if isinstance(data, dict):
        coerced_dict = {}
        # Get fields using Pydantic v2 model_fields, v1 __fields__, or standard annotations
        fields = getattr(schema_type, "model_fields", getattr(schema_type, "__fields__", {}))
        annotations = getattr(schema_type, "__annotations__", {})

        for key, value in data.items():
            field_type = Any
            if hasattr(schema_type, "model_fields") and key in fields:
                field_type = fields[key].annotation
            elif hasattr(schema_type, "__fields__") and key in fields:
                field_type = fields[key].outer_type_
            elif key in annotations:
                field_type = annotations[key]

            coerced_dict[key] = _coerce_nulls_dynamically(value, field_type)
        return coerced_dict

    return data
```
This dynamic approach ensures we only coerce fields explicitly annotated as `str` (or `Optional[str]`), decoupling the prompter from the domain schema entirely.

## 3. Tight Coupling Identification
A scan of `sequential_llm_prompter.py` reveals significant architectural bleeding. The prompter acts more like an `IndexingPipelineOrchestrator` than a generic LLM utility.

Coupling points discovered:
1. **`prompt_for_enrichment`**: Explicitly imports and operates on `schema.FileSkeleton` and `schema.FileEnrichment`. It contains hardcoded business logic for chunking symbols (e.g., `if len(skeleton.symbols) <= 40:`).
2. **`prompt_for_indexing`**: Contains the exact hardcoded multi-stage pipeline flow (`research`, `key_components`, `deep_dive`, `overview`, `custom`) and taint-analysis healing logic.
3. **`_coerce_for_schema`**: Contains phases (Phase 0.5 to Phase 2) that heavily rely on `section_registry._LIST_FIELD_MAP`, `_CONTENT_FIELD_MAP`, and `VerificationVerdict`. It wraps/unwraps specific payload structures.
4. **`_SimpleConversation._build_default_output`**: Contains hardcoded factory blocks for `schema.IndexDocument`, `schema.KeyComponentsDocument`, `schema.DeepDiveDocument`, etc.

**Recommended Architectural Boundary:** 
Extract the pure LLM abstractions (`MultiProviderLlmPrompter`, retry logic, rate limiting, and generic schema coercion) into a core utility module (e.g., `llm_core/multi_provider_prompter.py`). The domain-specific pipeline methods (`prompt_for_indexing`, `prompt_for_enrichment`, chunking logic) should be moved to a `PipelineOrchestrator` within the indexing domain.

## 4. Sphinch Mark Seeds (Readiness Assertions)
- `UniversalLlmPrompter` is renamed to `MultiProviderLlmPrompter` in both the class definition and its usages across the codebase.
- `_STRING_KEYS` is completely removed from `sequential_llm_prompter.py`.
- `_deep_replace_nulls` is replaced with a dynamic traversal method (e.g., `_coerce_nulls_dynamically`) that accepts both the data and the schema type.
- The new coercion method uses Pydantic's `model_fields` (or `__annotations__` fallback) and only coerces `None` to `""` if the underlying type is resolved to strictly `str`.
- `_SimpleConversation._build_default_output` handles mock generation generically without hardcoding specific schema classes like `schema.IndexDocument` or `schema.DeepDiveDocument`.
- Domain-specific orchestrations (`prompt_for_indexing`, `prompt_for_enrichment`) are identified as architectural debt slated for extraction in a future PR.
