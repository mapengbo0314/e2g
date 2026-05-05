import pytest
from indexing.schema import FileSkeleton, FileEnrichment, SkeletonSymbol, SymbolEnrichment
from indexing.ast_merger import ASTMerger, MissingEnrichmentError

def test_ast_merger_success():
    skeleton = FileSkeleton(symbols=[SkeletonSymbol(id="h1", name="Foo", signature="class Foo", line_number=1)])
    enrichment = FileEnrichment(symbols={"h1": SymbolEnrichment(summary="A class")})
    symbols, _ = ASTMerger.merge("test.py", skeleton, enrichment)
    assert symbols[0].summary == "A class"
    assert symbols[0].source_kind == "merged"

def test_ast_merger_missing_id():
    skeleton = FileSkeleton(symbols=[SkeletonSymbol(id="h1", name="Foo", signature="class Foo", line_number=1)])
    enrichment = FileEnrichment(symbols={})
    with pytest.raises(MissingEnrichmentError) as exc:
        ASTMerger.merge("test.py", skeleton, enrichment)
    assert "h1" in str(exc.value)
