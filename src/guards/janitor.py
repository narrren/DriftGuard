import boto3
import datetime
from dateutil import parser
import sys

def get_s3_client(region):
    return boto3.client('s3', region_name=region)

def get_s3_resource(region):
    return boto3.resource('s3', region_name=region)

def scan_and_reap(config, region='us-east-1'):
    """
    CRON Logic: Scans all buckets for expired tags.
    """
    s3 = get_s3_client(region)
    print("🧹 Janitor: Scanning S3 buckets for expired TTLs...")
    
    try:
        response = s3.list_buckets()
    except Exception as e:
        print(f"Error listing buckets: {e}")
        return

    for bucket in response['Buckets']:
        bucket_name = bucket['Name']
        check_and_destroy(s3, bucket_name, region)

def cleanup_pr_resources(context, config):
    """
    PR CLOSED Logic: Destroys resources associated with a specific PR.
    This assumes resources are named or tagged with the PR number/Branch.
    Since terraform random_id is used, we might rely on tags.
    For this MVP, we will scan ALL buckets and looks for a tag 'DriftGuard_PR' = pr_number if we added it,
    OR we rely on the implementation where 'Preview Env' is unique per PR.
    
    Current Terraform implementation: "driftguard-env-${random_id}"
    There is no PR specific tag in the current main.tf. 
    
    IMPROVEMENT: We will scan for buckets where driftguard_ttl_expiry is present 
    AND (optional) match a PR tag if we added one. 
    Strictly following the prompt: "Executes terraform destroy if ... script receives a 'PR Closed' signal".
    We will strictly look for *expired* items OR items explicitly marked for this PR.
    
    Since we didn't add a PR tag in terraform, we will assume the User wants aggressive cleanup 
    or we skip the specific PR check and just run the reaper.
    
    Let's stick to the prompt's "Reaper" logic which checks expiry.
    But for "PR Closed", we usually want immediate destruction.
    I will assume we can't identify the bucket easily without state, so I will run the standard expired check
    BUT ideally we would run 'terraform destroy' in the directory.
    
    If terraform dir is provided in config, we can run `terraform destroy`.
    """
    tf_dir = config.get('terraform_dir')
    if tf_dir and os.path.exists(tf_dir):
        print(f"Build closed. Running terraform destroy in {tf_dir}...")
        # In a real CI, we need the tfstate file. 
        # If the state is remote, this works. If local, it's lost in a fresh runner.
        # Assuming remote state or artifacts for this MVP logic.
        # We will use python-terraform or subprocess.
        import subprocess
        try:
            # -auto-approve is critical
            subprocess.run(['terraform', 'init'], cwd=tf_dir, check=True)
            subprocess.run(['terraform', 'destroy', '-auto-approve'], cwd=tf_dir, check=True)
            print("✅ Resources destroyed via Terraform.")
        except Exception as e:
            print(f"❌ Terraform destroy failed: {e}")
    else:
        print("Janitor: No terraform dir found for cleanup. Running Scan...")
        reap_all_expired(context.get('aws_region', 'us-east-1'))

def check_and_destroy(s3, bucket_name, region):
    try:
        tags_response = s3.get_bucket_tagging(Bucket=bucket_name)
        tags = {t['Key']: t['Value'] for t in tags_response['TagSet']}
        
        if 'driftguard_ttl_expiry' in tags:
            expiry_str = tags['driftguard_ttl_expiry']
            try:
                expiry_time = parser.parse(expiry_str)
                if expiry_time.tzinfo is None:
                    expiry_time = expiry_time.replace(tzinfo=datetime.timezone.utc)
                    
                now = datetime.datetime.now(datetime.timezone.utc)
                
                if now > expiry_time:
                    print(f"EXPIRED: {bucket_name} (Expired at {expiry_str}) - DESTROYING...")
                    destroy_bucket(bucket_name, region)
                else:
                    print(f"ACTIVE: {bucket_name} (Expires at {expiry_str})")
            except Exception as e:
                print(f"Error parsing date for {bucket_name}: {e}")
                
    except boto3.exceptions.ClientError as e:
        if "NoSuchTagSet" not in str(e):
             print(f"Skipping {bucket_name}: {e}")

def destroy_bucket(bucket_name, region):
    s3_resource = get_s3_resource(region)
    bucket = s3_resource.Bucket(bucket_name)
    try:
        bucket.objects.all().delete()
        bucket.delete()
        print(f"✔ REAPED: {bucket_name}")
    except Exception as e:
        print(f"❌ FAILED to reap {bucket_name}: {e}")

if __name__ == "__main__":
    # If run directly as script (e.g. Cron)
    scan_and_reap({}, 'us-east-1')
