import importlib
import sys
from typing import List, Optional
import pytest

# We need to test the fallback _BaseModel that is used when pydantic is not present.
def test_schema_fallback_recursive_instantiation():
    # Save the original pydantic module
    orig_pydantic = sys.modules.get("pydantic")
    
    # Hide pydantic
    sys.modules["pydantic"] = None
    
    # Import or reload indexing.schema
    import indexing.schema
    importlib.reload(indexing.schema)
    
    try:
        from indexing.schema import _BaseModel, _field
        
        class Child(_BaseModel):
            name: str = _field()

        class Parent(_BaseModel):
            # Complex annotation to trigger the bug
            children: Optional[List[Child]] = _field(default_factory=list)

        data = {
            "children": [{"name": "child1"}, {"name": "child2"}]
        }
        
        # This will fail with the old re.search logic if 'Optional' or 'List' is found first.
        # But wait, globals().get("Child") in schema.py would return None because Child is in this test's module.
        # We need to inject Child into schema.py's globals for the test to work, because the fallback _BaseModel
        # relies on globals() of the module where the class is defined... wait, it uses globals() of schema.py!
        # Let's check schema.py: `target_cls = globals().get(cls_name)`
        # This means `target_cls` MUST be defined in `indexing.schema`!
        # So instead of a custom Child, we use an existing model like ExportedSymbol and FileSkeleton.
        
        from indexing.schema import FileSkeleton, SkeletonSymbol
        
        data2 = {
            "symbols": [{"id": "hash1", "name": "foo", "is_private": False, "signature": "def foo(): pass", "line_number": 1}],
            "invariants": []
        }
        
        # FileSkeleton has: symbols: List[SkeletonSymbol]
        # Wait, if we use typing.Optional[typing.List[SkeletonSymbol]], let's make a mock class inside schema.py dynamically
        indexing.schema.Child = type('Child', (_BaseModel,), {'__annotations__': {'name': 'str'}})
        setattr(indexing.schema.Child, 'name', _field())
        
        indexing.schema.Parent = type('Parent', (_BaseModel,), {'__annotations__': {'children': 'typing.Optional[typing.List[Child]]'}})
        setattr(indexing.schema.Parent, 'children', _field(default_factory=list))
        
        parent = indexing.schema.Parent(**{"children": [{"name": "child1"}]})
        
        # Verify it was instantiated properly
        assert type(parent.children[0]) == indexing.schema.Child
        
    finally:
        # Restore original pydantic
        if orig_pydantic is not None:
            sys.modules["pydantic"] = orig_pydantic
        else:
            del sys.modules["pydantic"]
        importlib.reload(indexing.schema)
