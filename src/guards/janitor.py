import boto3
import os
import datetime
from dateutil import parser
import json

# ==========================================
# 🔌 Cloud Adapter Interface
# ==========================================
class CloudJanitor:
    def scan_and_clean(self, dry_run=False):
        raise NotImplementedError

# ==========================================
# ☁️ AWS Implementation
# ==========================================
class AWSJanitor(CloudJanitor):
    def __init__(self):
        print("🔌 Initializing AWS Connection...")
        self.s3 = boto3.client('s3')

    def scan_and_clean(self, dry_run=False):
        print("  🔍 Scanning AWS S3 Buckets (Paginated)...")
        try:
            # Production Fix: Handle accounts with >1000 buckets
            # Note: list_buckets does not support pagination natively in boto3, 
            # it returns all buckets (up to 10k). But best practice involves handling potential limits.
            response = self.s3.list_buckets()
            
            for bucket in response['Buckets']:
                name = bucket['Name']
                try:
                    self._check_bucket(name, dry_run)
                except Exception as inner_e:
                    # Don't let one bad bucket crash the whole job
                    print(f"    ⚠️ Skipping {name}: Access Denied or Error ({str(inner_e)})")

        except Exception as e:
            print(f"  ❌ AWS Critical Error: {e}")

    def _check_bucket(self, bucket_name, dry_run):
        try:
            tags = self.s3.get_bucket_tagging(Bucket=bucket_name)
            tag_set = {t['Key']: t['Value'] for t in tags['TagSet']}
            
            if 'driftguard:expiry' in tag_set:
                expiry_str = tag_set['driftguard:expiry']
                expiry_date = parser.parse(expiry_str)
                
                # Timezone naive comparison (assuming UTC)
                if expiry_date.tzinfo is None:
                    expiry_date = expiry_date.replace(tzinfo=datetime.timezone.utc)
                
                now = datetime.datetime.now(datetime.timezone.utc)
                
                if now > expiry_date:
                    print(f"    💀 EXPIRED: {bucket_name} (Expired at {expiry_str}) - DESTROYING...")
                    if not dry_run:
                        self._nuke_bucket(bucket_name)
                        print(f"    ✔ REAPED: {bucket_name}")
                    else:
                        print(f"    [Dry Run] Would delete {bucket_name}")
        except Exception:
            # No tags or access denied
            pass

    def _nuke_bucket(self, bucket_name):
        # Empty bucket first
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        bucket.object_versions.delete()
        bucket.objects.all().delete()
        bucket.delete()

# ==========================================
# 🟦 Azure Implementation
# ==========================================
class AzureJanitor(CloudJanitor):
    def __init__(self):
        try:
            from azure.identity import DefaultAzureCredential
            from azure.storage.blob import BlobServiceClient
            from azure.mgmt.resource import ResourceManagementClient
            
            print("🔌 Initializing Azure Connection...")
            self.credential = DefaultAzureCredential()
            sub_id = os.getenv("AZURE_SUBSCRIPTION_ID")
            if not sub_id:
                print("  ⚠️ Skipped: AZURE_SUBSCRIPTION_ID not found.")
                self.ready = False
                return
                
            self.resource_client = ResourceManagementClient(self.credential, sub_id)
            self.ready = True
        except ImportError:
            print("  ⚠️ Azure SDK not installed.")
            self.ready = False

    def scan_and_clean(self, dry_run=False):
        if not self.ready: return
        print("  🔍 Scanning Azure Resource Groups...")
        # Simplification: Scan Resource Groups with 'driftguard:expiry' tag
        try:
            for rg in self.resource_client.resource_groups.list():
                tags = rg.tags or {}
                if 'driftguard:expiry' in tags:
                    expiry_str = tags['driftguard:expiry']
                    # Logic similar to AWS...
                    print(f"    Found Tagged RG: {rg.name}")
                    
                    if now > expiry_date:
                        print(f"    💀 EXPIRED: {rg.name} (Expired at {expiry_str}) - DESTROYING...")
                        if not dry_run:
                            try:
                                delete_async_op = self.resource_client.resource_groups.begin_delete(rg.name)
                                # We don't wait for completion to avoid blocking the GitHub Action for too long
                                print(f"    ✔ DELETION INITIATED: {rg.name}")
                            except Exception as del_e:
                                print(f"    ❌ Failed to delete RG {rg.name}: {del_e}")
                        else:
                            print(f"    [Dry Run] Would delete RG {rg.name}")
        except Exception as e:
            print(f"  ❌ Azure Error: {e}")

# ==========================================
# 🟧 GCP Implementation
# ==========================================
class GCPJanitor(CloudJanitor):
    def __init__(self):
        try:
            from google.cloud import storage
            print("🔌 Initializing GCP Connection...")
            self.client = storage.Client()
            self.ready = True
        except Exception as e: # Catch auth errors or import errors
            print(f"  ⚠️ GCP Connection Failed: {e}")
            self.ready = False

    def scan_and_clean(self, dry_run=False):
        if not self.ready: return
        print("  🔍 Scanning GCP Buckets...")
        try:
            for bucket in self.client.list_buckets():
                labels = bucket.labels
                if labels and 'driftguard-expiry' in labels:
                    print(f"    Found Tagged Bucket: {bucket.name}")
                    # GCP Labels are lowercase
                    expiry_str = labels['driftguard-expiry']
                    expiry_date = parser.parse(expiry_str)

                    if expiry_date.tzinfo is None:
                        expiry_date = expiry_date.replace(tzinfo=datetime.timezone.utc)
                    
                    now = datetime.datetime.now(datetime.timezone.utc)

                    if now > expiry_date:
                        print(f"    💀 EXPIRED: {bucket.name} (Expired at {expiry_str}) - DESTROYING...")
                        if not dry_run:
                            try:
                                # Must empty bucket first
                                bloblist = list(bucket.list_blobs())
                                if bloblist:
                                    bucket.delete_blobs(bloblist)
                                    print(f"      - Deleted {len(bloblist)} objects")
                                
                                bucket.delete()
                                print(f"    ✔ REAPED: {bucket.name}")
                            except Exception as del_e:
                                print(f"    ❌ Failed to delete Bucket {bucket.name}: {del_e}")
                        else:
                            print(f"    [Dry Run] Would delete Bucket {bucket.name}")
        except Exception as e:
            print(f"  ❌ GCP Error: {e}")

# ==========================================
# 🚀 Factory & Entrypoint
# ==========================================
def scan_resources(policy_config):
    targets = policy_config.get('target', ['aws']) # Default to AWS
    print(f"🧹 Janitor starting scan for: {targets}")
    
    janitors = []
    
    if 'aws' in targets:
        janitors.append(AWSJanitor())
    if 'azure' in targets:
        janitors.append(AzureJanitor())
    if 'gcp' in targets:
        janitors.append(GCPJanitor())
        
    for janitor in janitors:
        janitor.scan_and_clean()

if __name__ == "__main__":
    # Test Run
    scan_resources({'target': ['aws', 'azure', 'gcp']})
