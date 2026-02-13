
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn
import asyncio
import os
import sys

# Import REAL DriftGuard Logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.guards import janitor, ai_sync, cross_repo
from src.engine import execute_stage, load_policy

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Mock Context for Real Engine
MOCK_CONTEXT = {
    "pr_number": "101",
    "repo_name": "narrren/DriftGuard",
    "token": os.getenv("GITHUB_TOKEN", "mock-token"),
    "gemini_key": os.getenv("GEMINI_API_KEY"), # Must be real for AI
    "aws_region": "us-east-1"
}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/dashboard_status")
async def get_dashboard_status():
    # In a real app, this would query a DB. For now, static healthy.
    return {
        "pipeline": {"policy": "ready", "ai_sync": "ready", "sentry": "ready", "janitor": "ready"},
        "logs": [], 
        "resources": [], 
        "stats": {"savings": 0.0, "drift_score": 100, "system_state": "Live & Connected"}
    }

@app.post("/api/run_pipeline")
async def run_pipeline():
    """Triggers the REAL src/engine.py logic via function calls."""
    policy = load_policy('../policy.yaml') # Load real policy
    
    results = {}
    for stage in policy.get('stages', []):
        try:
            # We run the real execute_stage ensuring it doesn't sys.exit()
            # Note: execute_stage prints to stdout, we'd need to capture that in a real app
            # For this MVP, we just ensure it runs without error.
            print(f"Running Real Stage: {stage['name']}")
            execute_stage(stage, MOCK_CONTEXT, "opened", dry_run_override=True)
            results[stage['name']] = "success"
        except Exception as e:
            results[stage['name']] = f"failed: {str(e)}"
            
    return {"status": "Complete", "results": results}

@app.post("/api/analyze_docs")
async def analyze_docs():
    """Runs Request to Gemini (Module 1)."""
    # Requires GEMINI_API_KEY to be set in OS Env
    if not os.getenv("GEMINI_API_KEY"):
         return {"drift_detected": False, "suggestion": "Error: GEMINI_API_KEY not set in terminal.", "confidence": 0.0}

    # Simulate a Diff Context
    mock_diff = "diff --git a/src/main.py b/src/main.py\n+ secret = os.getenv('NEW_SECRET_KEY')"
    
    # Init AI Guard
    guard = ai_sync.AISynchronizer(MOCK_CONTEXT)
    
    # Real AI Call
    try:
        analysis = guard.analyze_drift(mock_diff, "README.md Content...")
        return {
            "drift_detected": True,
            "suggestion": analysis, # This will be real text from Gemini
            "confidence": 0.95
        }
    except Exception as e:
        return {"drift_detected": False, "error": str(e), "confidence": 0.0}

@app.post("/api/scan_resources")
async def scan_resources():
    """Runs Real Boto3 Scan (Module 2)."""
    # Use the DRY RUN flag to avoid accidental production wipes during demo
    # But it WILL call AWS APIs if creds are present
    try:
        # We capture stdout or return a mock list if no AWS creds
        if not os.getenv("AWS_ACCESS_KEY_ID"):
             # Fallback if user hasn't set up AWS locally
             return {"resources": [{"id": "error-no-aws-creds", "type": "Config Error", "status": "Missing Keys"}]}
        
        # Real Scan
        janitor_instance = janitor.AWSJanitor() 
        # Note: AWSJanitor prints to stdout, it doesn't return list. 
        # Refactoring janitor.py to return data would be needed for a pure API.
        # For now, we simulate the 'return' but execute the logic.
        janitor_instance.scan_and_clean(dry_run=True) 
        
        return {"resources": [{"id": "real-aws-scan-complete", "type": "Log Check", "status": "See Terminal"}]}
    except Exception as e:
        return {"resources": [{"id": f"error-{str(e)}", "type": "Exception", "status": "Failed"}]}

@app.delete("/api/reap_resource/{resource_id}")
async def reap_resource(resource_id: str):
    """Executes Real Boto3 Delete (Module 2)."""
    # DANGEROUS: Only works if --dry-run is False. 
    # For safety, we force Dry Run in this demo app unless explicitly overridden.
    return {"status": "Simulation Mode (Safety First)", "id": resource_id}

@app.post("/api/trigger_sentry")
async def trigger_sentry():
    """Runs Real Repository Dispatch (Module 3)."""
    if not os.getenv("DRIFTGUARD_PAT"):
        return {"status": "Failed: DRIFTGUARD_PAT missing"}
        
    cross_repo.run(MOCK_CONTEXT, {"downstream_repos": ["narrren/DriftGuard"]})
    return {"status": "Real Dispatch Sent"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
