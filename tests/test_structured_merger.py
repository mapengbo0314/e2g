"""Tests for programmatic structured merging."""

import unittest
from typing import Any
from indexing import summary_merger
from indexing import schema
from indexing import section_registry

class FakeLlmPrompter:
    def prompt_for_merging(
        self,
        directory_path: str,
        system_prompt: str,
        initial_user_prompt: str,
        error_prompt_generator_instance: Any,
        directory_files: list[str] | None = None,
    ) -> schema.IndexDocument:
        # Simulate LLM returning a merged doc. 
        # It might have its own ideas about sections, but our patch should overwrite.
        return schema.IndexDocument(
            overview=schema.Overview(content="LLM Merged Overview"),
            blueprint=schema.Blueprint(symbols=[
                schema.ExportedSymbol(name="llm_symbol", signature="def llm()", summary="llm", file_path="llm.py", line_number=1, end_line_number=1)
            ])
        )

class FakeIndexState:
    def get_subdirectory_indexes(self, *args, **kwargs):
        return {}

class StructuredMergerTest(unittest.TestCase):
    def test_deterministic_merge_fidelity(self):
        prompter = FakeLlmPrompter()
        state = FakeIndexState()
        merger = summary_merger.SummaryMerger(prompter, state, None)
        
        # Two partial docs with different symbols
        doc1 = schema.IndexDocument(
            overview=schema.Overview(content="Overview 1"),
            blueprint=schema.Blueprint(symbols=[
                schema.ExportedSymbol(name="func1", signature="def func1()", summary="s1", file_path="f1.py", line_number=1, end_line_number=1)
            ])
        )
        doc2 = schema.IndexDocument(
            overview=schema.Overview(content="Overview 2"),
            blueprint=schema.Blueprint(symbols=[
                schema.ExportedSymbol(name="func2", signature="def func2()", summary="s2", file_path="f2.py", line_number=1, end_line_number=1)
            ])
        )
        
        merged = merger.merge([doc1, doc2], "/src")
        
        # Verify deterministic fields are unioned
        self.assertEqual(len(merged.blueprint.symbols), 2)
        sym_names = [s.name for s in merged.blueprint.symbols]
        self.assertIn("func1", sym_names)
        self.assertIn("func2", sym_names)
        
        # Verify LLM-synthesized fields are preserved
        self.assertEqual(merged.overview.content, "LLM Merged Overview")

    def test_accumulate_merge_tech_debt(self):
        prompter = FakeLlmPrompter()
        state = FakeIndexState()
        merger = summary_merger.SummaryMerger(prompter, state, None)
        
        doc1 = schema.IndexDocument(
            overview=schema.Overview(content="o1"),
            tech_debt=schema.TechDebt(notes=[
                schema.TechDebtNote(category="c1", description="d1", impact="i1")
            ])
        )
        doc2 = schema.IndexDocument(
            overview=schema.Overview(content="o2"),
            tech_debt=schema.TechDebt(notes=[
                schema.TechDebtNote(category="c2", description="d2", impact="i2")
            ])
        )
        
        merged = merger.merge([doc1, doc2], "/src")
        
        self.assertEqual(len(merged.tech_debt.notes), 2)
        categories = [n.category for n in merged.tech_debt.notes]
        self.assertIn("c1", categories)
        self.assertIn("c2", categories)

if __name__ == '__main__':
    unittest.main()
