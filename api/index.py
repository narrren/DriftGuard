from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
import os
import sys

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add src to path for engine/guards
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = FastAPI(title="DriftGuard", description="Autonomous Platform Governance")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "driftguard-super-secret-2026")
)

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)

# ─── OAuth Setup ──────────────────────────────────────────────────────────────
oauth = OAuth()

if os.getenv("GOOGLE_CLIENT_ID"):
    oauth.register(
        name='google',
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile https://www.googleapis.com/auth/cloud-platform'}
    )

if os.getenv("AZURE_CLIENT_ID"):
    oauth.register(
        name='azure',
        client_id=os.getenv("AZURE_CLIENT_ID"),
        client_secret=os.getenv("AZURE_CLIENT_SECRET"),
        api_base_url='https://graph.microsoft.com/v1.0/',
        access_token_url=f'https://login.microsoftonline.com/{os.getenv("AZURE_TENANT_ID","common")}/oauth2/v2.0/token',
        authorize_url=f'https://login.microsoftonline.com/{os.getenv("AZURE_TENANT_ID","common")}/oauth2/v2.0/authorize',
        client_kwargs={'scope': 'User.Read'}
    )

if os.getenv("AWS_CLIENT_ID") and os.getenv("AWS_COGNITO_POOL_ID"):
    oauth.register(
        name='aws',
        client_id=os.getenv("AWS_CLIENT_ID"),
        client_secret=os.getenv("AWS_CLIENT_SECRET"),
        server_metadata_url=f'https://cognito-idp.{os.getenv("AWS_REGION","us-east-1")}.amazonaws.com/{os.getenv("AWS_COGNITO_POOL_ID")}/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email'}
    )

# ─── Page Routes ──────────────────────────────────────────────────────────────
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
            return JSONResponse(
                {"error": f"Provider '{client_name}' not configured. Add credentials in Vercel Environment Variables."},
                status_code=400
            )
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
        return HTMLResponse(
            f"<script>window.opener.postMessage({{type:'OAUTH_SUCCESS',provider:'{provider}'}},'*');window.close();</script>"
        )
    except Exception as e:
        return HTMLResponse(
            f"<h2 style='font-family:monospace;color:#f87171;padding:2rem'>Auth Failed: {str(e)}</h2>"
            f"<p style='font-family:monospace;padding:0 2rem'>Ensure CLIENT_ID and SECRET are set in Vercel Environment Variables.</p>",
            status_code=403
        )

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
        "pipeline": {
            "policy": "ready",
            "ai_sync": "ready" if os.getenv("GEMINI_API_KEY") else "needs key",
            "sentry": "ready" if os.getenv("DRIFTGUARD_PAT") else "needs key",
            "janitor": "ready"
        },
        "stats": {
            "savings": 0.0,
            "drift_score": 100,
            "system_state": f"Live — {len(connected)} cloud(s) connected" if connected else "Live — No clouds connected"
        },
        "logs": [
            f"DriftGuard Engine online",
            f"Connected clouds: {', '.join(connected) if connected else 'none'}",
            f"Gemini AI: {'configured' if os.getenv('GEMINI_API_KEY') else 'not configured'}",
            f"GitHub PAT: {'configured' if os.getenv('DRIFTGUARD_PAT') else 'not configured'}",
        ]
    }

@app.post("/api/run_pipeline")
async def run_pipeline(request: Request):
    tokens = request.session.get('user_tokens', {})
    if not tokens and not os.getenv("GEMINI_API_KEY"):
        return {"status": "No credentials configured. Add environment variables in Vercel.", "results": {}}
    try:
        from src.engine import execute_stage, load_policy
        policy_path = os.path.join(os.path.dirname(__file__), '..', 'policy.yaml')
        policy = load_policy(policy_path)
        context = {
            "pr_number": "101",
            "repo_name": "narrren/DriftGuard",
            "token": os.getenv("DRIFTGUARD_PAT", ""),
            "gemini_key": os.getenv("GEMINI_API_KEY", ""),
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
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return {
            "drift_detected": False,
            "suggestion": "GEMINI_API_KEY not set. Add it in Vercel → Settings → Environment Variables.",
            "confidence": 0.0
        }
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = """You are a code review AI. A developer added these lines to their code:
+ SECRET_KEY = os.getenv('NEW_SECRET_KEY')
+ STRIPE_WEBHOOK = os.getenv('STRIPE_WEBHOOK_SECRET')

The README does not mention NEW_SECRET_KEY or STRIPE_WEBHOOK_SECRET.
Respond in 1-2 sentences: is there documentation drift? What should be documented?"""
        response = model.generate_content(prompt)
        return {
            "drift_detected": True,
            "suggestion": response.text,
            "confidence": 0.95
        }
    except Exception as e:
        return {"drift_detected": False, "error": str(e), "confidence": 0.0}

@app.post("/api/scan_resources")
async def scan_resources(request: Request):
    tokens = request.session.get('user_tokens', {})
    results = []

    # AWS
    if os.getenv("AWS_ACCESS_KEY_ID") or 'aws' in tokens:
        try:
            import boto3
            session_kwargs = {}
            if 'aws' in tokens:
                creds = tokens['aws']
                session_kwargs = {
                    'aws_access_key_id': creds.get('access_key'),
                    'aws_secret_access_key': creds.get('secret_key'),
                    'aws_session_token': creds.get('session_token')
                }
            s3 = boto3.client('s3', **session_kwargs)
            buckets = s3.list_buckets().get('Buckets', [])
            results.append({"id": "aws-s3", "type": "AWS", "status": f"Found {len(buckets)} S3 bucket(s)"})
        except ImportError:
            results.append({"id": "aws-sdk", "type": "AWS", "status": "boto3 not installed in this environment"})
        except Exception as e:
            results.append({"id": "aws-error", "type": "AWS", "status": f"Error: {str(e)}"})

    # Azure
    if os.getenv("AZURE_SUBSCRIPTION_ID") or 'azure' in tokens:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.resource import ResourceManagementClient
            cred = DefaultAzureCredential()
            client = ResourceManagementClient(cred, os.getenv("AZURE_SUBSCRIPTION_ID", ""))
            groups = list(client.resource_groups.list())
            results.append({"id": "azure-rg", "type": "Azure", "status": f"Found {len(groups)} resource group(s)"})
        except ImportError:
            results.append({"id": "azure-sdk", "type": "Azure", "status": "azure-mgmt-resource not installed in this environment"})
        except Exception as e:
            results.append({"id": "azure-error", "type": "Azure", "status": f"Error: {str(e)}"})

    # GCP
    if os.getenv("GCP_CREDENTIALS_JSON") or 'gcp' in tokens:
        try:
            from google.cloud import storage
            client = storage.Client()
            buckets = list(client.list_buckets())
            results.append({"id": "gcp-storage", "type": "GCP", "status": f"Found {len(buckets)} GCS bucket(s)"})
        except ImportError:
            results.append({"id": "gcp-sdk", "type": "GCP", "status": "google-cloud-storage not installed in this environment"})
        except Exception as e:
            results.append({"id": "gcp-error", "type": "GCP", "status": f"Error: {str(e)}"})

    if not results:
        return {"resources": [{"id": "no-creds", "type": "Info", "status": "No cloud credentials found. Connect a cloud provider or add environment variables."}]}
    return {"resources": results}

@app.delete("/api/reap_resource/{resource_id}")
async def reap_resource(resource_id: str):
    return {"status": "Safety Lock Active — deletion requires direct CLI access", "id": resource_id}

@app.post("/api/trigger_sentry")
async def trigger_sentry():
    pat = os.getenv("DRIFTGUARD_PAT")
    if not pat:
        return {"status": "Failed: DRIFTGUARD_PAT not set. Add it in Vercel → Settings → Environment Variables."}
    try:
        from github import Github
        g = Github(pat)
        repo = g.get_repo("narrren/DriftGuard")
        repo.create_repository_dispatch(event_type="driftguard_signal", client_payload={"source": "dashboard"})
        return {"status": f"✅ Signal dispatched to narrren/DriftGuard"}
    except Exception as e:
        return {"status": f"Error: {str(e)}"}

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
        alert_data = {
            "title": "🚨 COST SPIKE DETECTED",
            "msg": "3 GPU instances identified as Zombies. Estimated waste: $4.50/hr.",
            "level": "critical"
        }
    return {
        "credits": {
            "used": round(sum(base_spend), 2),
            "limit": 1000.0,
            "remaining": round(1000.0 - sum(base_spend), 2)
        },
        "forecast_dates": dates,
        "actual_spend": base_spend,
        "predicted_without_janitor": pred_spend,
        "zombies_reaped": reaped,
        "spend_distribution": [65.0, 25.0, 10.0],
        "alert": alert_data
    }
