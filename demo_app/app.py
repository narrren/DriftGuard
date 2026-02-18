
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load Environment Variables from .env file
load_dotenv()

# Load Environment Variables from .env file
load_dotenv()

# Import REAL DriftGuard Logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.guards import janitor, ai_sync, cross_repo
from src.engine import execute_stage, load_policy
from demo_mode import DemoSimulator

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# State Management
USE_SIMULATION = True
sim = DemoSimulator()

# Mock Context for Real Engine
MOCK_CONTEXT = {
    "pr_number": "101",
    "repo_name": "narrren/DriftGuard",
    "token": os.getenv("GITHUB_TOKEN", "mock-token"),
    "gemini_key": os.getenv("GEMINI_API_KEY"), 
    "aws_region": os.getenv("AWS_REGION", "us-east-1")
}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "simulation_mode": USE_SIMULATION})

@app.post("/api/toggle_mode")
async def toggle_mode():
    global USE_SIMULATION
    USE_SIMULATION = not USE_SIMULATION
    mode = "SIMULATION" if USE_SIMULATION else "REAL_ENGINE"
    print(f"🔄 Switched to {mode} Mode")
    return {"mode": mode, "is_simulation": USE_SIMULATION}

@app.get("/api/dashboard_status")
async def get_dashboard_status():
    if USE_SIMULATION:
        return {
            "pipeline": sim.pipeline_status,
            "logs": sim.logs[-10:],
            "resources": sim.resources,
            "stats": sim.stats,
            "mode": "SIMULATION"
        }
    else:
        # Real Mode Status (Simplified)
        return {
            "pipeline": {"policy": "ready", "ai_sync": "ready", "sentry": "ready", "janitor": "ready"},
            "logs": [], 
            "resources": [], 
            "stats": {"savings": 0.0, "drift_score": 100, "system_state": "Live & Connected"},
            "mode": "REAL"
        }

@app.post("/api/run_pipeline")
async def run_pipeline():
    if USE_SIMULATION:
        stages = ["policy", "ai_sync", "sentry", "janitor"]
        sim.log_event("engine_start", "DriftGuard Engine Initializing (Simulation)...")
        for stage in stages:
            sim.pipeline_status[stage] = "running"
            await asyncio.sleep(1.0)
            sim.run_pipeline_step(stage)
            sim.pipeline_status[stage] = "completed"
        return {"status": "Complete"}
    
    # REAL MODE
    policy = load_policy('../policy.yaml')
    results = {}
    for stage in policy.get('stages', []):
        try:
            print(f"Running Real Stage: {stage['name']}")
            execute_stage(stage, MOCK_CONTEXT, "opened", dry_run_override=True)
            results[stage['name']] = "success"
        except Exception as e:
            results[stage['name']] = f"failed: {str(e)}"
    return {"status": "Complete", "results": results}

@app.post("/api/analyze_docs")
async def analyze_docs():
    if USE_SIMULATION:
        sim.log_event("ai_sync_start", "Reviewing PR #104 against README.md...")
        await asyncio.sleep(1.5)
        return sim.get_ai_analysis()

    # REAL MODE
    if not os.getenv("GEMINI_API_KEY"):
         return {"drift_detected": False, "suggestion": "Error: GEMINI_API_KEY not set.", "confidence": 0.0}
    
    mock_diff = "diff --git a/src/main.py b/src/main.py\n+ secret = os.getenv('NEW_SECRET_KEY')"
    guard = ai_sync.AISynchronizer(MOCK_CONTEXT)
    try:
        analysis = guard.analyze_drift(mock_diff, "README.md Content...")
        return {"drift_detected": True, "suggestion": analysis, "confidence": 0.95}
    except Exception as e:
        return {"drift_detected": False, "error": str(e), "confidence": 0.0}

@app.post("/api/scan_resources")
async def scan_resources():
    if USE_SIMULATION:
        sim.log_event("janitor_scan_start", "Scanning AWS/Azure/GCP for expired tags...")
        await asyncio.sleep(1.0)
        return {"resources": sim.resources}

    # REAL MODE
    try:
        if not os.getenv("AWS_ACCESS_KEY_ID"):
             return {"resources": [{"id": "error-no-aws-keys", "type": "Config Error", "status": "Missing Keys"}]}
        
        janitor_instance = janitor.AWSJanitor() 
        janitor_instance.scan_and_clean(dry_run=True) 
        return {"resources": [{"id": "real-aws-scan-complete", "type": "Log Check", "status": "See Terminal"}]}
    except Exception as e:
        return {"resources": [{"id": f"error-{str(e)}", "type": "Exception", "status": "Failed"}]}

@app.delete("/api/reap_resource/{resource_id}")
async def reap_resource(resource_id: str):
    if USE_SIMULATION:
        sim.log_event("janitor_nuke_start", f"Nuclear Launch Detected on {resource_id}...")
        await asyncio.sleep(2.0)
        success = sim.delete_resource(resource_id)
        return {"status": "Reaped", "id": resource_id} if success else JSONResponse(status_code=400, content={"message": "Blocked"})

    # REAL MODE
    return {"status": "Simulation Mode (Safety First)", "id": resource_id}

@app.post("/api/trigger_sentry")
async def trigger_sentry():
    if USE_SIMULATION:
        sim.log_event("sentry_dispatch", "Dispatching integration tests...")
        await asyncio.sleep(2.5)
        return {"status": "Passed"}

    # REAL MODE
    if not os.getenv("DRIFTGUARD_PAT"):
        return {"status": "Failed: DRIFTGUARD_PAT missing"}
    cross_repo.run(MOCK_CONTEXT, {"downstream_repos": ["narrren/DriftGuard"]})
    return {"status": "Real Dispatch Sent"}

# --- FINOPS DASHBOARD LOGIC (Pitch Mode) ---
from pydantic import BaseModel
from typing import List, Dict

class FinOpsStats(BaseModel):
    credits: Dict[str, float]
    forecast_dates: List[str]
    actual_spend: List[float]
    predicted_without_janitor: List[float]
    zombies_reaped: List[int]
    spend_distribution: List[float] # AWS, Azure, GCP
    alert: Dict[str, str] = None

@app.get("/api/finops/stats", response_model=FinOpsStats)
async def get_finops_stats(simulate_leak: bool = False):
    """
    Returns realistic mock data for the 'Cost of Inaction' pitch.
    If simulate_leak is True, we show a spike to demonstrate detection.
    """
    # 7-Day Window
    dates = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    # Baseline: Healthy DriftGuard Usage ($15-20/day)
    base_spend = [12.5, 15.0, 18.2, 14.5, 16.0, 10.5, 11.0]
    
    # Prediction: What happens if we turn off the Janitor? (Cumulative zombie cost)
    # Starts same, then diverges rapidly
    pred_spend = [12.5, 35.0, 68.0, 95.5, 140.0, 195.5, 260.0]
    
    reaped = [5, 12, 8, 3, 15, 2, 4]
    
    alert_data = None
    
    if simulate_leak:
        # PITCH SCENARIO: A developer left a massive GPU cluster running
        base_spend[-1] = 85.0 # Sudden spike
        base_spend[-2] = 45.0
        alert_data = {
            "title": "COST SPIKE DETECTED",
            "msg": "3 GPU Instances identified as Zombies. Estimated waste: $4.50/hr.",
            "level": "critical"
        }
        
    return FinOpsStats(
        credits={
            "used": sum(base_spend), 
            "limit": 1000.0, 
            "remaining": 1000.0 - sum(base_spend)
        },
        forecast_dates=dates,
        actual_spend=base_spend,
        predicted_without_janitor=pred_spend,
        zombies_reaped=reaped,
        spend_distribution=[65.0, 25.0, 10.0], # AWS vs Azure vs GCP
        alert=alert_data
    )

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
