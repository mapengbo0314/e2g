import unittest
from indexing.schema import FileEnrichment, SymbolEnrichment, InvariantEnrichment

class TestMergeStrategy(unittest.TestCase):
    def test_semantic_first_win(self):
        # Empty summary should be overwritten
        e1 = FileEnrichment(symbols={"sym1": SymbolEnrichment(summary="")})
        e2 = FileEnrichment(symbols={"sym1": SymbolEnrichment(summary="Real summary")})
        e1.merge(e2)
        self.assertEqual(e1.symbols["sym1"].summary, "Real summary")

        # Placeholder summary should be overwritten
        e3 = FileEnrichment(symbols={"sym2": SymbolEnrichment(summary="No summary provided")})
        e4 = FileEnrichment(symbols={"sym2": SymbolEnrichment(summary="Better summary")})
        e3.merge(e4)
        self.assertEqual(e3.symbols["sym2"].summary, "Better summary")

        # If both are populated, keep the first one
        e5 = FileEnrichment(symbols={"sym3": SymbolEnrichment(summary="First summary")})
        e6 = FileEnrichment(symbols={"sym3": SymbolEnrichment(summary="Verbose hallucination that is much longer")})
        e5.merge(e6)
        self.assertEqual(e5.symbols["sym3"].summary, "First summary")

        # Invariants: Empty intent/usage should be overwritten
        inv1 = FileEnrichment(invariants={"inv1": InvariantEnrichment(intent="[AST Discovered - LLM must enrich intent]", usage_context="")})
        inv2 = FileEnrichment(invariants={"inv1": InvariantEnrichment(intent="Real intent", usage_context="Real usage")})
        inv1.merge(inv2)
        self.assertEqual(inv1.invariants["inv1"].intent, "Real intent")

        # Invariants: If both are populated, keep the first one
        inv3 = FileEnrichment(invariants={"inv2": InvariantEnrichment(intent="First intent", usage_context="First usage")})
        inv4 = FileEnrichment(invariants={"inv2": InvariantEnrichment(intent="Second intent which is longer", usage_context="Second usage which is longer")})
        inv3.merge(inv4)
        self.assertEqual(inv3.invariants["inv2"].intent, "First intent")

if __name__ == "__main__":
    unittest.main()
