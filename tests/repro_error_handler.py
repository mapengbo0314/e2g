import unittest
from indexing.sequential_llm_prompter import UniversalLlmPrompter, UniversalLlmConfig

class TestErrorHandler(unittest.TestCase):
    def test_model_not_found_error(self):
        prompter = UniversalLlmPrompter(UniversalLlmConfig(bundle_name="test", research_gemini_model="my-model"), None)
        
        # Simulate a "model not found" error
        class MockError(Exception):
            pass
            
        try:
            prompter._handle_llm_prompt_error(MockError("model not_found"), "dir", None, None, attempt=1)
            self.fail("Should have raised an exception")
        except Exception as e:
            from indexing.sequential_llm_prompter import UnrecoverableLlmError
            self.assertIsInstance(e, UnrecoverableLlmError)
            self.assertIn("my-model", str(e))

if __name__ == "__main__":
    unittest.main()
