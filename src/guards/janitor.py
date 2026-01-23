import boto3
import datetime
from dateutil import parser
import sys

def scan_and_clean_s3():
    s3 = boto3.client('s3')
    
    print("Janitor: Scanning S3 buckets...")
    
    try:
        response = s3.list_buckets()
    except Exception as e:
        print(f"Error listing buckets: {e}")
        return

    for bucket in response['Buckets']:
        bucket_name = bucket['Name']
        try:
            tags_response = s3.get_bucket_tagging(Bucket=bucket_name)
            tags = {t['Key']: t['Value'] for t in tags_response['TagSet']}
            
            if 'driftguard_ttl_expiry' in tags:
                expiry_str = tags['driftguard_ttl_expiry']
                try:
                    expiry_time = parser.parse(expiry_str)
                    # Make expiry_time offset-aware if it isn't, using UTC
                    if expiry_time.tzinfo is None:
                        expiry_time = expiry_time.replace(tzinfo=datetime.timezone.utc)
                        
                    now = datetime.datetime.now(datetime.timezone.utc)
                    
                    if now > expiry_time:
                        print(f"EXPIRED: {bucket_name} (Expired at {expiry_str}) - DESTROYING...")
                        reap_bucket(s3, bucket_name)
                    else:
                        print(f"ACTIVE: {bucket_name} (Expires at {expiry_str})")
                except Exception as e:
                    print(f"Error parsing date for {bucket_name}: {e}")
                    
        except boto3.exceptions.ClientError as e:
            # No tags or access denied
            if "NoSuchTagSet" not in str(e):
                 print(f"Skipping {bucket_name}: {e}")

def reap_bucket(s3_client, bucket_name):
    # Determine if we should also empty the bucket first (S3 requirement)
    # Using boto3 resource for easier object deletion
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket(bucket_name)
    
    try:
        bucket.objects.all().delete()
        bucket.delete()
        print(f"✔ REAPED: {bucket_name}")
    except Exception as e:
        print(f"❌ FAILED to reap {bucket_name}: {e}")

if __name__ == "__main__":
    scan_and_clean_s3()
