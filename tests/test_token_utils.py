import pytest
from unittest.mock import patch, MagicMock
from harness.token_utils import count_tokens

def test_count_tokens_empty_string():
    """Verify that an empty string returns 0 tokens."""
    assert count_tokens("") == 0

def test_count_tokens_fallback_no_api_key():
    """Verify fallback logic when no API key is present."""
    with patch.dict("os.environ", {}, clear=True):
        # "a" is 1 char, 1 // 4 = 0, should be max(1, 0) = 1
        assert count_tokens("a") == 1
        # "abcd" is 4 chars, 4 // 4 = 1
        assert count_tokens("abcd") == 1
        # "abcde" is 5 chars, 5 // 4 = 1
        assert count_tokens("abcde") == 1
        # "abcdefgh" is 8 chars, 8 // 4 = 2
        assert count_tokens("abcdefgh") == 2

def test_count_tokens_fallback_on_api_error():
    """Verify fallback logic when API call fails."""
    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}):
        with patch("harness.token_utils.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.count_tokens.side_effect = Exception("API Error")
            mock_get_client.return_value = mock_client
            
            assert count_tokens("Hello world") == max(1, len("Hello world") // 4)

def test_count_tokens_with_mocked_api():
    """Verify that the API is called correctly and returns expected value."""
    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}):
        with patch("harness.token_utils.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.total_tokens = 5
            mock_client.models.count_tokens.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            count = count_tokens("Hello world")
            assert count == 5
            mock_client.models.count_tokens.assert_called_once_with(
                model="gemini-1.5-flash",
                contents="Hello world"
            )
