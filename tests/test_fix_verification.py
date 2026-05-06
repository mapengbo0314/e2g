
import unittest
from unittest.mock import MagicMock, patch
from indexing.sequential_llm_prompter import UniversalLlmPrompter, UniversalLlmConfig
from indexing import verification_types

class TestFixVerification(unittest.TestCase):
    def test_verify_artifact_keyword_args(self):
        # Create a prompter with a mock config
        config = UniversalLlmConfig(bundle_name="test")
        prompter = UniversalLlmPrompter(config=config, fs_manager=None)
        
        # Mock _execute_single_prompt
        prompter._execute_single_prompt = MagicMock()
        
        # Mock prompt_templates.create_verifier_prompt
        with patch('indexing.prompt_templates.create_verifier_prompt', return_value="user prompt"):
            with patch('indexing.prompt_templates.VERIFIER_SYSTEM_PROMPT', "system prompt"):
                # Call verify_artifact
                prompter.verify_artifact(artifact_json='{}', source_context='context')
        
        # Check that _execute_single_prompt was called with the correct arguments
        args, kwargs = prompter._execute_single_prompt.call_args
        self.assertIn('directory_path', kwargs)
        self.assertEqual(kwargs['directory_path'], 'verification_step')
        self.assertIn('initial_user_prompt', kwargs)
        self.assertIn('agent_name', kwargs)
        self.assertEqual(kwargs['agent_name'], 'verifier_agent')
        self.assertIn('error_prompt_generator_instance', kwargs)
        self.assertIn('conversation_factory', kwargs)
        self.assertIn('stringified_system_prompt', kwargs)
        self.assertIn('output_schema', kwargs)
        self.assertEqual(kwargs['output_schema'], verification_types.VerificationVerdict)
        
        # Ensure system_prompt and model_type are NOT in kwargs (which caused the error)
        self.assertNotIn('system_prompt', kwargs)
        self.assertNotIn('model_type', kwargs)

if __name__ == "__main__":
    unittest.main()
