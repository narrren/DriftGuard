import os
import sys
from google import genai
from github import Github

def run(context, config):
    print("🧠 Starting AI Doc-Guard (Powered by google-genai SDK)...")
    
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

    # 3b. Check for Override Command
    context_override = False
    
    # Check PR body (safely handle None)
    if pr.body and "/driftguard override" in pr.body:
        context_override = True
    
    # Check comments (simplified - usually we'd page through them)
    if not context_override:
        for comment in pr.get_issue_comments():
            if comment.body and "/driftguard override" in comment.body:
                context_override = True
                break
    
    if context_override:
        print("🛡️  Override detected via '/driftguard override'. Skipping AI Policy.")
        return

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

    # 5. Call Gemini (New SDK V1) with Resiliency Fallback
    print("✨ Using AI Model: gemini-1.5-flash")
    client = genai.Client(api_key=gemini_key)
    
    from tenacity import retry, stop_after_attempt, wait_exponential

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def call_ai_with_retry():
        return client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )

    result = None
    
    try:
        response = call_ai_with_retry()
        # Cleanup response string to ensure JSON parsing
        text = response.text.replace('```json', '').replace('```', '').strip()
        import json
        result = json.loads(text)
        print("✅ AI Analysis Complete.")

    except Exception as e:
        print(f"⚠️  AI Provider Error ({e}). Switching to Resiliency Fallback Mode.")
        # FALLBACK: Deterministic Check
        # This ensures the pipeline verifies the critical change even if AI is down.
        # FALLBACK: Regex Pattern Matching for Env Vars
        # This ensures the pipeline verifies the critical change even if AI is down.
        import re
        
        # Regex to find: os.getenv('VAR'), os.environ.get('VAR'), os.environ['VAR']
        # Captures the VAR name in group 2 or 3 depending on quote style
        env_var_pattern = r"(os\.getenv|os\.environ\.get|os\.environ)\[?\(?['\"]([A-Z_0-9]+)['\"]"
        
        matches = re.findall(env_var_pattern, diff_text)
        found_vars = set([m[1] for m in matches])
        
        missing_vars = []
        for var in found_vars:
            if var not in readme_content:
                missing_vars.append(var)
        
        if missing_vars:
             result = {
                "status": "FAIL",
                "reason": f"[Fallback Guard] Detected new environment variables {missing_vars} in code but not in README.",
                "suggested_doc_edit": f"Please add {', '.join(missing_vars)} to the README environment configuration section."
            }
        else:
             result = {
                "status": "PASS",
                "reason": "[Fallback Guard] No undocumented environment variables found via regex scan.",
                "suggested_doc_edit": ""
            }

    print(f"Verdict: {result['status']}")

    # 6. Act on Result
    if result['status'] == 'FAIL':
        body = f"## 🤖 DriftGuard Report\n\n**Status:** ❌ Documentation Drift Detected\n\n**Reason:** {result['reason']}\n\n**Suggested Fix:**\n```markdown\n{result['suggested_doc_edit']}\n```"
        
        try:
           pr.create_issue_comment(body)
        except Exception as e:
           print(f"Could not post comment: {e}")
           
        raise Exception("DriftGuard blocked this PR: Documentation is out of sync.")
    else:
        print("✅ Documentation is in sync.")

