"""Comprehensive E2E integration test for the indexing pipeline.

This test runs the full indexing orchestration (Chunking -> Indexing -> Merging -> Verification)
using a MockPrompter that can be configured to simulate real-world failure modes
like gRPC errors, Pydantic validation errors, and double-wrapped JSON.
"""

import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest
from indexing import generate_bundles
from indexing import schema
from indexing import shared_flags
from indexing import sequential_llm_prompter
from indexing import verification_types

class MockPrompter(sequential_llm_prompter.LlmPrompter):
    """A prompter that returns pre-defined or programmatic responses."""

    def __init__(self):
        self.responses = {} # (agent_name, directory_path) -> response_obj
        self.call_counts = {}
        self.side_effects = [] # List of callables to run on each prompt

    def prompt_for_indexing(self, directory_path, system_prompt, initial_user_prompt, error_prompt_generator_instance, verifier=None, directory_files=None, previous_artifact=None, previous_verdict=None):
        return self._execute_mock("indexing_agent", directory_path, schema.IndexDocument)

    def prompt_for_merging(self, directory_path, system_prompt, initial_user_prompt, error_prompt_generator_instance):
        return self._execute_mock("merging_agent", directory_path, schema.IndexDocument)

    def prompt_for_root_map_summary(self, root_map_content):
        return "Mock Root Map Summary"

    def verify_artifact(self, artifact_json, source_context, directory_files=None, is_merger_mode=False):
        return self._execute_mock("verifier_agent", "verification_step", verification_types.VerificationVerdict)

    def _execute_mock(self, agent_name, path, output_schema):
        key = (agent_name, path)
        self.call_counts[key] = self.call_counts.get(key, 0) + 1
        
        # Check for side effects (like raising exceptions)
        for effect in self.side_effects:
            effect(agent_name, path, self.call_counts[key])

        # Return predefined response if any
        if key in self.responses:
            return self.responses[key]
        
        # Default successful response
        if output_schema == schema.IndexDocument:
            # Match AST grounding expectations
            symbol_name = "run" if "src1" in str(path) else "util"
            file_name = "app.py" if "src1" in str(path) else "util.py"
            signature = f"def {symbol_name}()" # Match AST extractor normalization
            
            return schema.IndexDocument(
                overview=schema.Overview(content=f"Mock for {path}"),
                key_interfaces=schema.KeyInterfaces(interfaces=[
                    schema.Interface(name=symbol_name, signature=signature, description="Main entry")
                ]),
                blueprint=schema.Blueprint(symbols=[
                    schema.ExportedSymbol(
                        name=symbol_name, 
                        signature=signature, 
                        summary="Intent summary", 
                        file_path=file_name
                    )
                ]),
                key_individual_components=schema.KeyIndividualComponents(components=[])
            )
        if output_schema == verification_types.VerificationVerdict:
            return verification_types.VerificationVerdict(passed=True, confidence=1.0)
        
        return output_schema()

@pytest.fixture
def workspace():
    """Sets up a minimal codebase for indexing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        # Create TWO directories to ensure Map-Reduce summary is triggered
        src1 = root / "src1"
        src1.mkdir()
        (src1 / "app.py").write_text("def run(): pass")
        
        src2 = root / "src2"
        src2.mkdir()
        (src2 / "util.py").write_text("def util(): pass")
        
        out = root / "index_out"
        out.mkdir()
        
        yield [str(src1), str(src2)], out

def test_e2e_pipeline_with_mock_prompter(workspace):
    """Verifies the pipeline completes with a completely mock prompter."""
    input_dirs, out_dir = workspace
    
    # Configure flags
    shared_flags.config.pipeline.num_epochs = 1
    shared_flags.config.trust.enabled = True
    
    mock_prompter = MockPrompter()
    
    # Pre-populate mock root map summary
    mock_prompter.responses[("root_map_summary", "")] = "Mock Root Map Summary"
    
    bundle = generate_bundles.BundleConfig(
        bundle_name="e2e_test",
        input_dirs=input_dirs,
        output_dir=str(out_dir),
    )
    
    # Run the pipeline with our mock prompter
    generate_bundles.execute_indexing(bundle, llm_prompter=mock_prompter)
    
    # Verify outputs
    root_map = out_dir / "root_map_v0.md"
    assert root_map.exists()
    content = root_map.read_text()
    
    # RootMap uses _recursive_summarize. If len(items) > 1, it calls prompt_for_root_map_summary.
    # Our MockPrompter.prompt_for_root_map_summary returns "Mock Root Map Summary".
    assert "Mock Root Map Summary" in content
    assert "🟢" in content # High confidence


def test_e2e_recovery_from_transient_error(workspace):
    """Verifies the pipeline retries and recovers from transient errors (like gRPC issues)."""
    input_dirs, out_dir = workspace
    
    # Configure global flags to allow mock fallback
    shared_flags.config.llm.allow_mock_fallback = True
    shared_flags.config.pipeline.num_epochs = 1
    
    bundle = generate_bundles.BundleConfig(
        bundle_name="retry_test",
        input_dirs=input_dirs,
        output_dir=str(out_dir),
    )
    
    # Monkeypatch _SimpleConversation to simulate failures
    original_prompt = sequential_llm_prompter._SimpleConversation.prompt
    
    call_count = 0
    def mock_prompt_with_failure(self, user_prompt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            logging.info("Simulating transient gRPC failure (Stream removed)")
            raise Exception("Stream removed")
        return original_prompt(self, user_prompt)
        
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(sequential_llm_prompter._SimpleConversation, "prompt", mock_prompt_with_failure)
        
        generate_bundles.execute_indexing(bundle)
    
    # The pipeline should have retried and eventually succeeded
    assert call_count >= 2 # At least one retry happened
    assert (out_dir / "root_map_v0.md").exists()

def test_e2e_coercion_double_wrapping(workspace):
    """Verifies that double-wrapped JSON from LLM is correctly coerced and doesn't fail validation."""
    input_dirs, out_dir = workspace
    bundle = generate_bundles.BundleConfig(
        bundle_name="coercion_test",
        input_dirs=input_dirs,
        output_dir=str(out_dir),
    )
    
    # Simulate double-wrapped response in _SimpleConversation
    original_prompt = sequential_llm_prompter._SimpleConversation.prompt
    def mock_prompt_double_wrapped(self, user_prompt):
        if self.output_schema_type == schema.IndexDocument:
            # Create a double-wrapped structure
            data = {
                "overview": {
                    "content": {
                        "content": "Double wrapped overview content"
                    }
                },
                "key_individual_components": {"components": []},
                "key_interfaces": {"interfaces": [
                    {"name": "run", "signature": "def run()", "description": "desc"}
                ]},
                "blueprint": {"symbols": [
                    {"name": "run", "signature": "def run()", "summary": "test summary", "file_path": "app.py"}
                ]}
            }
            return sequential_llm_prompter.PromptResult(
                text=json.dumps(data),
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            )
        return original_prompt(self, user_prompt)

    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(sequential_llm_prompter._SimpleConversation, "prompt", mock_prompt_double_wrapped)
        # We also need to make sure get_state returns the dict so it goes through coercion
        def mock_get_state(self, agent_name):
            try:
                return json.loads(self.prompt("").text)
            except:
                return None
        mp.setattr(sequential_llm_prompter._SimpleConversation, "get_state", mock_get_state)
        
        # Ensure trust is enabled to exercise the verifier if needed
        shared_flags.config.trust.enabled = True
        
        generate_bundles.execute_indexing(bundle)

    # If it reached here without raising ValidationError, coercion worked!
    assert (out_dir / "root_map_v0.md").exists()

if __name__ == "__main__":
    pytest.main([__file__])
