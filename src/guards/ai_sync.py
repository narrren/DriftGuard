import os
import sys
import google.generativeai as genai
from github import Github

def run(context, config):
    print("🧠 Starting AI Doc-Guard...")
    
    token = context['token']
    repo_name = context['repo_name']
    pr_number = int(context['pr_number'])
    gemini_key = context['gemini_key']
    readme_path = config.get('readme_path', 'README.md')

    if not gemini_key:
        raise Exception("GEMINI_API_KEY not set in environment.")

    # 1. Connect to GitHub
    g = Github(token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # 2. Get Diff
    diff_text = ""
    print(f"Fetching diff for PR #{pr_number}...")
    files = pr.get_files()
    for file in files:
        if file.patch:
            diff_text += f"\nFile: {file.filename}\n{file.patch}\n"
    
    if not diff_text:
        print("No changes found in diff.")
        return

    # 3. Get README
    print(f"Fetching {readme_path}...")
    try:
        readme_file = repo.get_contents(readme_path, ref=pr.head.ref)
        readme_content = readme_file.decoded_content.decode("utf-8")
    except Exception as e:
        print(f"Warning: {readme_path} not found. ({e})")
        readme_content = "(No README file found)"

    # 4. Prepare Prompt for Gemini
    prompt = f"""
    You are a generic Senior Technical Writer and Code Reviewer.
    Your task is to analyze the following Code Diff and ensure that the Documentation (README) is up to date.
    
    Pass Criteria:
    - If the code changes are internal logic, bug fixes, or minor refactors that do NOT affect the API, usage, or environment variables, return PASS.
    - If the code changes introduce new features, change function signatures, adding/removing environment variables, or change API endpoints, checks if these are reflected in the README.
    
    Input Data:
    
    === CURRENT README ===
    {readme_content[:2000]} 
    
    === CODE DIFF ===
    {diff_text[:3000]}
    
    Instructions:
    Return your response in pure JSON format (no markdown formatting).
    JSON Structure:
    {{
      "status": "PASS" or "FAIL",
      "reason": "Short explanation of why.",
      "suggested_doc_edit": "Markdown text suggesting how to fix the documentation."
    }}
    """

    # 5. Call Gemini
    # 5. Call Gemini
    print("✨ Using AI Model: gemini-1.5-flash")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    
    try:
        # Cleanup response string to ensure JSON parsing
        text = response.text.replace('```json', '').replace('```', '').strip()
        import json
        result = json.loads(text)
    except Exception as e:
        print(f"Failed to parse AI response: {response.text}")
        raise e

    print(f"AI Verdict: {result['status']}")

    # 6. Act on Result
    if result['status'] == 'FAIL':
        body = f"## 🤖 DriftGuard AI Report\n\n**Status:** ❌ Documentation Drift Detected\n\n**Reason:** {result['reason']}\n\n**Suggested Fix:**\n```markdown\n{result['suggested_doc_edit']}\n```"
        
        # Check if we already commented to avoid spam (optional, skipping for MVP)
        pr.create_issue_comment(body)
        raise Exception("Documentation is out of sync with code changes.")
    else:
        print("✅ Documentation is in sync.")
