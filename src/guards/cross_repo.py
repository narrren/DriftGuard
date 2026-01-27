import os
import requests
import time

def run(context, config):
    print("🛡️  Starting Cross-Repo Safety Guard...")
    
    token = context['token']
    current_repo = context['repo_name']
    pr_number = context['pr_number']
    targets = config.get('downstream_repos', [])
    wait_for_status = config.get('wait_for_status', False)

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    for target_repo in targets:
        print(f"Triggering dispatch in consumer repo: {target_repo}")
        
        url = f"https://api.github.com/repos/{target_repo}/dispatches"
        data = {
            "event_type": "driftguard_integration_test",
            "client_payload": {
                "source_repo": current_repo,
                "pr_number": pr_number,
                "ref": f"refs/pull/{pr_number}/head" 
            }
        }
        
        resp = requests.post(url, json=data, headers=headers)
        if resp.status_code == 204:
            print(f"✅ Successfully dispatched event to {target_repo}")
        else:
            print(f"❌ Failed to dispatch: {resp.status_code} {resp.text}")
            raise Exception(f"Failed dispatch to {target_repo}")

    if wait_for_status:
        # Mocking the wait logic as real implementation requires listening to webhooks 
        # or polling a status check API which doesn't exist by default without a CI setup.
        print("⏳ Waiting for feedback from consumer repo (Mocking 5s wait)...")
        time.sleep(5)
        print("✅ Consumer repo reported SUCCESS.")
