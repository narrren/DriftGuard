import os
import json
from github import Github

def analyze_diff_impact(diff_text, readme_content):
    """
    This function sends the diff and readme to the AI Model.
    For this boilerplate, we'll simulate the AI response or prepare the prompt.
    """
    
    prompt = f"""
    You are a Senior Technical Writer. Analyze this code diff.
    Does it change function signatures, API endpoints, or environment variables?
    If yes, check if the attached README reflects these changes.
    
    Diff:
    {diff_text[:1000]} # Truncated for token limits in this demo
    
    README:
    {readme_content[:1000]}
    
    Return a JSON: {{ 'status': 'PASS/FAIL', 'reason': '...', 'suggested_doc_edit': '...' }}
    """
    
    print("DEBUG: Sending prompt to AI...")
    # Real implementation would call OpenAI or Gemini here.
    # returning a mock response for now to ensure flow works without keys.
    
    # Simulating a check - if "BREAK_ME" is in diff and not "FIXED_DOC" in readme -> FAIL
    if "BREAK_ME" in diff_text and "FIXED_DOC" not in readme_content:
         return {
            'status': 'FAIL',
            'reason': 'Detected breaking change in function signatures without README update.',
            'suggested_doc_edit': 'Update README to include new parameter for XYZ.'
        }
    
    return {'status': 'PASS', 'reason': 'No documented changes needed.', 'suggested_doc_edit': ''}

def run_ai_guard(pr_number, github_token, repo_name):
    print(f"Running AI Doc-Guard on PR #{pr_number} in {repo_name}")
    
    g = Github(github_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    # 1. Fetch Diff
    # requests.get(pr.diff_url) or pr.get_files()
    # collecting all patch data
    diff_text = ""
    for file in pr.get_files():
        if file.patch:
            diff_text += f"\nFile: {file.filename}\n{file.patch}"
            
    # 2. Fetch README
    try:
        readme = repo.get_contents("README.md", ref=pr.head.ref)
        readme_content = readme.decoded_content.decode("utf-8")
    except Exception as e:
        print(f"Warning: README.md not found. {e}")
        readme_content = ""

    # 3. AI Analysis
    result = analyze_diff_impact(diff_text, readme_content)
    
    print(f"AI Result: {result}")
    
    if result['status'] == 'FAIL':
        # Action: Post comment
        comment_body = f"## 🤖 DriftGuard AI Report\n\n**Status:** ❌ FAIL\n\n**Reason:** {result['reason']}\n\n**Suggested Edit:**\n```markdown\n{result['suggested_doc_edit']}\n```"
        pr.create_issue_comment(comment_body)
        print("Blocked PR with comment.")
        sys.exit(1) # Block the build
    else:
        print("DriftGuard AI Check Passed.")

import sys
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ai_sync.py <pr_number> <repo_name>")
        sys.exit(1)
        
    pr_num = int(sys.argv[1])
    repo = sys.argv[2]
    token = os.environ.get("GITHUB_TOKEN")
    
    if not token:
        print("Error: GITHUB_TOKEN not set.")
        sys.exit(1)
        
    run_ai_guard(pr_num, token, repo)
