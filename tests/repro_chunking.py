import unittest
from indexing.schema import FileSkeleton, SkeletonSymbol, SkeletonInvariant
from indexing.sequential_llm_prompter import UniversalLlmPrompter, UniversalLlmConfig

class TestChunking(unittest.TestCase):
    def test_invariant_chunking(self):
        prompter = UniversalLlmPrompter(UniversalLlmConfig(bundle_name="test"), None)
        
        # We need to mock _execute_enrichment_chunk to see what it receives
        received_chunks = []
        def mock_execute(file_path, chunk_skeleton, source_code):
            received_chunks.append(chunk_skeleton)
            from indexing.schema import FileEnrichment
            return FileEnrichment()
        
        prompter._execute_enrichment_chunk = mock_execute
        
        # Create a skeleton with 100 symbols and 10 invariants
        symbols = [SkeletonSymbol(id=f"s{i}", name=f"sym{i}", signature=f"def sym{i}()", line_number=i) for i in range(100)]
        invariants = [SkeletonInvariant(id=f"i{i}", primitive=f"Lock{i}", line_number=i) for i in range(10)]
        skeleton = FileSkeleton(symbols=symbols, invariants=invariants)
        
        prompter.prompt_for_enrichment("test.py", skeleton, "code")
        
        self.assertEqual(len(received_chunks), 3) # 100 symbols / 40 = 3 chunks
        
        # Check invariants in each chunk
        inv_counts = [len(chunk.invariants) for chunk in received_chunks]
        self.assertEqual(sum(inv_counts), 10)
        
        # Ensure not all invariants are in the first chunk
        self.assertNotEqual(inv_counts[0], 10)

if __name__ == "__main__":
    unittest.main()
