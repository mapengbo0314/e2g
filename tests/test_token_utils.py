import pytest
from harness.token_utils import count_tokens

def test_count_tokens_real_string():
    # This requires a GEMINI_API_KEY to be present in the environment for real counting
    # or we can mock the client. For this utility, we'll assume a real key is available.
    text = "Hello world"
    # Typical tokenizers might count this as 2 tokens
    count = count_tokens(text)
    assert isinstance(count, int)
    assert count > 0
