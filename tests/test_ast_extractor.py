import pytest
from indexing.ast_extractor import extract_skeleton

def test_extract_skeleton_generates_ids():
    code = "class Foo:\n    pass\n"
    skeleton = extract_skeleton("test.py", code)
    assert len(skeleton.symbols) == 1
    assert skeleton.symbols[0].id is not None
    assert len(skeleton.symbols[0].id) > 0
