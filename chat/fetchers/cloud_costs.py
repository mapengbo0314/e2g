import boto3
import logging
from datetime import datetime, timedelta
from typing import Optional

def fetch_aws_cost(aws_access_key_id: Optional[str], aws_secret_access_key: Optional[str]) -> dict:
    if not aws_access_key_id or not aws_secret_access_key:
        return {
            "cost": 0.0,
            "status": "error",
            "error": "Missing AWS credentials"
        }
    
    try:
        client = boto3.client(
            'ce',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name='us-east-1'
        )
        
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        
        cost = 0.0
        for result in response.get('ResultsByTime', []):
            cost_str = result['Total']['UnblendedCost']['Amount']
            cost += float(cost_str)
        
        return {
            "cost": cost,
            "status": "success"
        }
    except Exception as e:
        logging.error(f"AWS cost fetch failed: {e}")
        return {
            "cost": 0.0,
            "status": "error",
            "error": str(e)
        }

def fetch_gcp_cost(credentials_json: Optional[str]) -> dict:
    if not credentials_json:
        return {
            "cost": 0.0,
            "status": "error",
            "error": "Missing GCP credentials"
        }
    
    return {
        "cost": 0.0,
        "status": "stubbed"
    }
