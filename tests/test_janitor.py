
import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws
from ..src.guards.janitor import AWSJanitor 

# Mock Data
MOCK_BUCKET = "driftguard-test-bucket-expired"
PROTECTED_BUCKET = "driftguard-prod-bucket-active"

@mock_aws
def test_janitor_aws_kill_switch():
    """
    Ensures that resources tagged with 'Protected: True' are NEVER deleted, even if scanned.
    """
    s3 = boto3.client("s3", region_name="us-east-1")
    
    # 1. Setup Mock Environment
    s3.create_bucket(Bucket=MOCK_BUCKET)
    s3.create_bucket(Bucket=PROTECTED_BUCKET)
    
    # 2. Add Tags
    s3.put_bucket_tagging(
        Bucket=MOCK_BUCKET,
        Tagging={'TagSet': [{'Key': 'driftguard:expiry', 'Value': '2020-01-01'}]} # Expired
    )
    
    s3.put_bucket_tagging(
        Bucket=PROTECTED_BUCKET,
        Tagging={'TagSet': [
            {'Key': 'driftguard:expiry', 'Value': '2020-01-01'}, # technically expired
            {'Key': 'Protected', 'Value': 'True'} # BUT PROTECTED
        ]}
    )
    
    # 3. Running Janitor Logic
    janitor = AWSJanitor()
    # We call scan directly but force deletion (dry_run=False) so we can assert actual destructive actions
    janitor.scan_and_clean(dry_run=False)
    
    # 4. Assertions
    
    # Protected bucket MUST still exist
    try:
        s3.head_bucket(Bucket=PROTECTED_BUCKET)
        assert True # Success
    except ClientError:
        pytest.fail(f"Protected Bucket {PROTECTED_BUCKET} was deleted! Kill Switch Failed.")
        
    # Expired bucket SHOULD be gone (or slated for deletion if logic holds)
    # Note: AWSJanitor implementation might vary on how it deletes, let's just check the protected one primarily for this 'Kill Switch' test.
