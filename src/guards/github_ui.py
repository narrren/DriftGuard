
from github import Github

def update_github_check(context, commit_sha, status="completed", conclusion="success", output=None):
    """
    Submits a formal 'Check Run' to the GitHub Checks API (Developer Experience).
    """
    token = context.get('token')
    repo_name = context.get('repo_name')
    if not token or not repo_name:
        print("Missing GITHUB_TOKEN or REPO_NAME in context. Skipping Check Run.")
        return

    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        # Using the commit SHA directly ensures the status is attached to the right commit in the PR
        
        check_name = "DriftGuard Governance"
        
        # If output is provided, maximize the Check Run details
        check_output = output if output else {
            "title": f"DriftGuard Policy: {conclusion.upper()}",
            "summary": "Policy execution completed successfully."
        }
        
        repo.get_commit(sha=commit_sha).create_check_run(
            name=check_name,
            head_sha=commit_sha,
            status=status,
            conclusion=conclusion,
            output=check_output
        )
        print(f"✅ GitHub Check Run updated: {conclusion}")
        
    except Exception as e:
        print(f"⚠️ Failed to update GitHub Check Run: {e}")
