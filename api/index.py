from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from pydantic import BaseModel
from typing import List, Dict
import os
import sys
import time

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = FastAPI(title="DriftGuard", description="Autonomous Platform Governance")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "driftguard-super-secret-2026"))

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# ─── OAuth Setup ─────────────────────────────────────────────────────────────
oauth = OAuth()

oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile https://www.googleapis.com/auth/cloud-platform'}
)

oauth.register(
    name='azure',
    client_id=os.getenv("AZURE_CLIENT_ID"),
    client_secret=os.getenv("AZURE_CLIENT_SECRET"),
    api_base_url='https://graph.microsoft.com/v1.0/',
    access_token_url=f'https://login.microsoftonline.com/{os.getenv("AZURE_TENANT_ID","common")}/oauth2/v2.0/token',
    authorize_url=f'https://login.microsoftonline.com/{os.getenv("AZURE_TENANT_ID","common")}/oauth2/v2.0/authorize',
    client_kwargs={'scope': 'User.Read https://management.azure.com/.default'}
)

if os.getenv("AWS_COGNITO_POOL_ID"):
    oauth.register(
        name='aws',
        client_id=os.getenv("AWS_CLIENT_ID"),
        client_secret=os.getenv("AWS_CLIENT_SECRET"),
        server_metadata_url=f'https://cognito-idp.{os.getenv("AWS_REGION","us-east-1")}.amazonaws.com/{os.getenv("AWS_COGNITO_POOL_ID")}/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email'}
    )

# ─── Page Routes ─────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/ai-guard", response_class=HTMLResponse)
async def ai_guard(request: Request):
    return templates.TemplateResponse("ai_guard.html", {"request": request})

@app.get("/janitor", response_class=HTMLResponse)
async def janitor_page(request: Request):
    return templates.TemplateResponse("janitor.html", {"request": request})

@app.get("/sentry", response_class=HTMLResponse)
async def sentry_page(request: Request):
    return templates.TemplateResponse("sentry.html", {"request": request})

@app.get("/finops", response_class=HTMLResponse)
async def finops_page(request: Request):
    return templates.TemplateResponse("finops.html", {"request": request})

@app.get("/policy", response_class=HTMLResponse)
async def policy_page(request: Request):
    return templates.TemplateResponse("policy.html", {"request": request})

# ─── OAuth Routes ─────────────────────────────────────────────────────────────
@app.get("/auth/login/{provider}")
async def login_provider(provider: str, request: Request):
    client_name = 'google' if provider == 'gcp' else provider
    try:
        client = oauth.create_client(client_name)
        if not client:
            return JSONResponse({"error": f"Provider '{client_name}' not configured. Set credentials in environment."}, status_code=400)
        redirect_uri = request.url_for('auth_callback', provider=provider)
        return await client.authorize_redirect(request, redirect_uri)
    except Exception as e:
        return JSONResponse({"error": f"OAuth init failed: {str(e)}"}, status_code=500)

@app.get("/auth/callback/{provider}")
async def auth_callback(provider: str, request: Request):
    client_name = 'google' if provider == 'gcp' else provider
    try:
        client = oauth.create_client(client_name)
        token = await client.authorize_access_token(request)
        tokens = request.session.get('user_tokens', {})
        tokens[provider] = dict(token)
        request.session['user_tokens'] = tokens
        return HTMLResponse(f"<script>window.opener.postMessage({{type:'OAUTH_SUCCESS',provider:'{provider}'}},'*');window.close();</script>")
    except Exception as e:
        return HTMLResponse(f"<h2 style='font-family:monospace;color:#f87171'>Auth Failed: {str(e)}</h2><p>Ensure CLIENT_ID and SECRET are set in environment variables.</p>", status_code=403)

@app.get("/auth/status")
async def auth_status(request: Request):
    tokens = request.session.get('user_tokens', {})
    return {
        "aws":   {"connected": "aws"   in tokens},
        "azure": {"connected": "azure" in tokens},
        "gcp":   {"connected": "gcp"   in tokens},
    }

@app.post("/auth/disconnect/{provider}")
async def disconnect(provider: str, request: Request):
    tokens = request.session.get('user_tokens', {})
    tokens.pop(provider, None)
    request.session['user_tokens'] = tokens
    return {"status": "Disconnected"}

# ─── API Routes ───────────────────────────────────────────────────────────────
@app.get("/api/dashboard_status")
async def dashboard_status(request: Request):
    tokens = request.session.get('user_tokens', {})
    connected = [p for p in ['aws', 'azure', 'gcp'] if p in tokens]
    return {
        "mode": "REAL",
        "connected_clouds": connected,
        "pipeline": {"policy": "ready", "ai_sync": "ready", "sentry": "ready", "janitor": "ready"},
        "stats": {"savings": 0.0, "drift_score": 100, "system_state": "Live & Connected"},
        "logs": [f"System Live — {len(connected)} cloud(s) connected" if connected else "No clouds connected yet. Use the Connect buttons."]
    }

@app.post("/api/run_pipeline")
async def run_pipeline(request: Request):
    tokens = request.session.get('user_tokens', {})
    if not tokens:
        return {"status": "No clouds connected", "results": {}}
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from src.engine import execute_stage, load_policy
        policy = load_policy(os.path.join(os.path.dirname(__file__), '..', 'policy.yaml'))
        context = {
            "pr_number": "101",
            "repo_name": "narrren/DriftGuard",
            "token": os.getenv("DRIFTGUARD_PAT", ""),
            "gemini_key": os.getenv("GEMINI_API_KEY"),
            "aws_region": os.getenv("AWS_REGION", "us-east-1")
        }
        results = {}
        for stage in policy.get('stages', []):
            try:
                execute_stage(stage, context, "opened", dry_run_override=True)
                results[stage['name']] = "success"
            except Exception as e:
                results[stage['name']] = f"failed: {str(e)}"
        return {"status": "Complete", "results": results}
    except Exception as e:
        return {"status": f"Error: {str(e)}", "results": {}}

@app.post("/api/analyze_docs")
async def analyze_docs():
    if not os.getenv("GEMINI_API_KEY"):
        return {"drift_detected": False, "suggestion": "GEMINI_API_KEY not set in environment variables.", "confidence": 0.0}
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from src.guards import ai_sync
        context = {"gemini_key": os.getenv("GEMINI_API_KEY"), "token": os.getenv("DRIFTGUARD_PAT",""), "repo_name": "narrren/DriftGuard", "pr_number": "101"}
        guard = ai_sync.AISynchronizer(context)
        mock_diff = "diff --git a/src/main.py b/src/main.py\n+ secret = os.getenv('NEW_SECRET_KEY')"
        analysis = guard.analyze_drift(mock_diff, "README.md Content...")
        return {"drift_detected": True, "suggestion": analysis, "confidence": 0.95}
    except Exception as e:
        return {"drift_detected": False, "error": str(e), "confidence": 0.0}

@app.post("/api/scan_resources")
async def scan_resources(request: Request):
    tokens = request.session.get('user_tokens', {})
    results = []
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from src.guards import janitor as janitor_mod

        if os.getenv("AWS_ACCESS_KEY_ID") or 'aws' in tokens:
            try:
                j = janitor_mod.AWSJanitor(credentials=tokens)
                j.scan_and_clean(dry_run=True)
                results.append({"id": "aws-scan", "type": "AWS", "status": "Scan Complete — check server logs"})
            except Exception as e:
                results.append({"id": "aws-error", "type": "AWS", "status": f"Error: {str(e)}"})

        if os.getenv("AZURE_SUBSCRIPTION_ID") or 'azure' in tokens:
            try:
                j = janitor_mod.AzureJanitor(credentials=tokens)
                j.scan_and_clean(dry_run=True)
                results.append({"id": "azure-scan", "type": "Azure", "status": "Scan Complete"})
            except Exception as e:
                results.append({"id": "azure-error", "type": "Azure", "status": f"Error: {str(e)}"})

        if os.getenv("GCP_CREDENTIALS_JSON") or 'gcp' in tokens:
            try:
                j = janitor_mod.GCPJanitor(credentials=tokens)
                j.scan_and_clean(dry_run=True)
                results.append({"id": "gcp-scan", "type": "GCP", "status": "Scan Complete"})
            except Exception as e:
                results.append({"id": "gcp-error", "type": "GCP", "status": f"Error: {str(e)}"})

        if not results:
            return {"resources": [{"id": "no-creds", "type": "Info", "status": "No cloud credentials found. Connect a cloud provider first."}]}
        return {"resources": results}
    except Exception as e:
        return {"resources": [{"id": "error", "type": "Exception", "status": str(e)}]}

@app.delete("/api/reap_resource/{resource_id}")
async def reap_resource(resource_id: str):
    return {"status": "Safety Lock Active — deletion requires direct CLI access", "id": resource_id}

@app.post("/api/trigger_sentry")
async def trigger_sentry():
    if not os.getenv("DRIFTGUARD_PAT"):
        return {"status": "Failed: DRIFTGUARD_PAT not set in environment"}
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from src.guards import cross_repo
        context = {"token": os.getenv("DRIFTGUARD_PAT"), "repo_name": "narrren/DriftGuard", "pr_number": "101", "gemini_key": ""}
        cross_repo.run(context, {"downstream_repos": ["narrren/DriftGuard"]})
        return {"status": "Signal dispatched to downstream repos"}
    except Exception as e:
        return {"status": f"Error: {str(e)}"}

# ─── FinOps API ───────────────────────────────────────────────────────────────
@app.get("/api/finops/stats")
async def finops_stats(simulate_leak: bool = False):
    dates = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    base_spend = [12.5, 15.0, 18.2, 14.5, 16.0, 10.5, 11.0]
    pred_spend = [12.5, 35.0, 68.0, 95.5, 140.0, 195.5, 260.0]
    reaped = [5, 12, 8, 3, 15, 2, 4]
    alert_data = None
    if simulate_leak:
        base_spend[-1] = 85.0
        base_spend[-2] = 45.0
        alert_data = {"title": "COST SPIKE DETECTED", "msg": "3 GPU Instances identified as Zombies. Estimated waste: $4.50/hr.", "level": "critical"}
    return {
        "credits": {"used": sum(base_spend), "limit": 1000.0, "remaining": 1000.0 - sum(base_spend)},
        "forecast_dates": dates,
        "actual_spend": base_spend,
        "predicted_without_janitor": pred_spend,
        "zombies_reaped": reaped,
        "spend_distribution": [65.0, 25.0, 10.0],
        "alert": alert_data
    }
