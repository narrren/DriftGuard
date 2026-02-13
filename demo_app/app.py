
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from demo_mode import DemoSimulator
import asyncio

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize Simulator
sim = DemoSimulator()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/dashboard_status")
async def get_dashboard_status():
    return {
        "pipeline": sim.pipeline_status,
        "logs": sim.logs[-10:], # Last 10
        "resources": sim.resources,
        "stats": sim.stats
    }

@app.post("/api/run_pipeline")
async def run_pipeline():
    """Simulate the full UniFlow."""
    stages = ["policy", "ai_sync", "sentry", "janitor"]
    sim.log_event("engine_start", "DriftGuard Engine Initializing...")
    
    for stage in stages:
        sim.pipeline_status[stage] = "running"
        await asyncio.sleep(1.2) # Visual Delay
        sim.run_pipeline_step(stage)
        sim.pipeline_status[stage] = "completed"
        
    sim.log_event("engine_complete", "Pipeline finished successfully.")
    return {"status": "Complete"}

@app.post("/api/analyze_docs")
async def analyze_docs():
    """Module 1: AI Sync."""
    sim.log_event("ai_sync_start", "Reviewing PR #104 against README.md...")
    await asyncio.sleep(1.5)
    result = sim.get_ai_analysis()
    sim.log_event("ai_drift_detected", "Found undocumented secret: STRIPE_API_KEY")
    return result

@app.post("/api/scan_resources")
async def scan_resources():
    """Module 2: Janitor Scan."""
    sim.log_event("janitor_scan_start", "Scanning AWS/Azure/GCP for expired tags...")
    await asyncio.sleep(1.0)
    found = [r for r in sim.resources if r['status'] == 'Expired']
    sim.log_event("janitor_findings", f"Found {len(found)} expired resources.", {"ids": [x['id'] for x in found]})
    return {"resources": sim.resources}

@app.delete("/api/reap_resource/{resource_id}")
async def reap_resource(resource_id: str):
    """Module 2: Janitor Reap."""
    sim.log_event("janitor_nuke_start", f"Nuclear Launch Detected on {resource_id}...")
    await asyncio.sleep(2.0) # Dramatic Pause for "Deleting..."
    success = sim.delete_resource(resource_id)
    if success:
        return {"status": "Reaped", "id": resource_id}
    return JSONResponse(status_code=400, content={"message": "Cannot delete protected resource"})

@app.post("/api/trigger_sentry")
async def trigger_sentry():
    """Module 3: Sentry Integration."""
    sim.log_event("sentry_dispatch", "Dispatching integration tests to 'consumer-app-frontend'...")
    await asyncio.sleep(2.5)
    sim.log_event("sentry_result", "Integration Tests Passed ✅", {"repo": "consumer-app-frontend", "duration": "2.4s"})
    return {"status": "Passed"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
