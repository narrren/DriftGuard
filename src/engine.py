import os
import sys
import yaml
import importlib

# Add src to path so we can import guards
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def load_policy(policy_path='policy.yaml'):
    if not os.path.exists(policy_path):
        # try relative to root
        policy_path = os.path.join(os.getcwd(), policy_path)
    
    if not os.path.exists(policy_path):
        print(f"Policy file {policy_path} not found.")
        return None
        
    with open(policy_path, 'r') as f:
        return yaml.safe_load(f)

def run_stage(stage, context):
    name = stage['name']
    enabled = stage.get('enabled', False)
    
    if not enabled:
        print(f"Skipping stage {name} (Disabled)")
        return
        
    print(f"Executing stage: {name}...")
    
    if name == 'ai_doc_check':
        from src.guards import ai_sync
        try:
            ai_sync.run_ai_guard(context['pr_number'], context['token'], context['repo_name'])
        except Exception as e:
            print(f"Error in ai_doc_check: {e}")
            if stage.get('severity') == 'block':
                sys.exit(1)
                
    elif name == 'janitor':
        # Placeholder for Phase 3
        print("Janitor stage logic not yet integrated in engine.")
        
    elif name == 'cross_repo_safety':
         # Placeholder for Phase 4
        print("Cross-repo safety logic not yet integrated in engine.")

def main():
    print("DriftGuard Engine Starting...")
    
    # Context from Environment Variables (set by GitHub Action)
    pr_number = os.environ.get('PR_NUMBER')
    repo_name = os.environ.get('GITHUB_REPOSITORY')
    token = os.environ.get('GITHUB_TOKEN')
    
    if not pr_number or not repo_name:
        print("Not running in a PR context or missing env vars. Exiting.")
        # We might be running in a cron job or issue comment, handle accordingly
        return

    context = {
        'pr_number': int(pr_number),
        'repo_name': repo_name,
        'token': token
    }

    policy = load_policy()
    if policy:
        print(f"Policy Version: {policy.get('version')}")
        for stage in policy.get('stages', []):
            run_stage(stage, context)
            
    else:
        print("No policy loaded.")
        sys.exit(1)

if __name__ == "__main__":
    main()
