import pytest
from unittest.mock import patch, MagicMock
from chat.fetchers.cloud_costs import fetch_aws_cost, fetch_gcp_cost

def test_fetch_aws_cost_success():
    with patch("chat.fetchers.cloud_costs.boto3.client") as mock_client:
        mock_ce = MagicMock()
        mock_client.return_value = mock_ce
        mock_ce.get_cost_and_usage.return_value = {
            "ResultsByTime": [
                {
                    "Total": {
                        "UnblendedCost": {
                            "Amount": "12.50"
                        }
                    }
                }
            ]
        }
        
        result = fetch_aws_cost("dummy_key", "dummy_secret")
        assert result["cost"] == 12.50
        assert result["status"] == "success"

def test_fetch_aws_cost_error():
    with patch("chat.fetchers.cloud_costs.boto3.client") as mock_client:
        mock_client.side_effect = Exception("AWS Error")
        
        result = fetch_aws_cost("dummy_key", "dummy_secret")
        assert result["cost"] == 0.0
        assert result["status"] == "error"
        assert result["error"] == "AWS Error"

def test_fetch_aws_cost_missing_creds():
    result = fetch_aws_cost(None, None)
    assert result["cost"] == 0.0
    assert result["status"] == "error"
    assert result["error"] == "Missing AWS credentials"

def test_fetch_gcp_cost_stub():
    result = fetch_gcp_cost("dummy_credentials_json")
    assert result["cost"] == 0.0
    assert result["status"] == "stubbed"

def test_fetch_gcp_cost_missing_creds():
    result = fetch_gcp_cost(None)
    assert result["cost"] == 0.0
    assert result["status"] == "error"
    assert result["error"] == "Missing GCP credentials"
