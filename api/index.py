from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

# Locate templates directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def read_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/finops", response_class=HTMLResponse)
async def read_finops(request: Request):
    return templates.TemplateResponse("finops.html", {"request": request})

@app.get("/janitor", response_class=HTMLResponse)
async def read_janitor(request: Request):
    return templates.TemplateResponse("janitor.html", {"request": request})

@app.get("/sentry", response_class=HTMLResponse)
async def read_sentry(request: Request):
    return templates.TemplateResponse("sentry.html", {"request": request})

@app.get("/policy", response_class=HTMLResponse)
async def read_policy(request: Request):
    return templates.TemplateResponse("policy.html", {"request": request})

@app.get("/ai-guard", response_class=HTMLResponse)
async def read_ai_guard(request: Request):
    return templates.TemplateResponse("ai_guard.html", {"request": request})

# API Routes stub (for JS calls to not fail)
@app.get("/api/janitor/scan")
def janitor_scan():
    return {"orphaned_count": 15, "projected_savings": 520}

@app.get("/api/analyze_docs")
def analyze_docs():
    return {"verdict": "Safe to Merge", "confidence": 92}
