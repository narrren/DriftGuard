# DriftGuard 🛡️

### **Autonomous Platform Engineering Suite for Config-Driven Governance**

**Status:** 🟢 Active | **Version:** 2.0.0

DriftGuard acts as a "Governance-as-Code" layer, automating the critical checks that prevent "Broken Factory" syndrome in Platform Engineering. It combines a powerful backend policy engine with a **modern web dashboard** to enforce Documentation, Cost, and Integration safety.

---

## ⚡ Key Features

| Module | Name | Function | Tech Stack |
| :--- | :--- | :--- | :--- |
| **Dashboard** | **The Console** | **Unified Web Interface**. A responsive, dark-mode UI to visualize drift, manage policies, view logs, and track cloud costs. | FastAPI, Jinja2, Tailwind CSS |
| **Module 1** | **The Synchronizer** | **AI Documentation Guard**. Uses Google Gemini 1.5 to semantic-check Pull Requests. If code changes (e.g., new Env Vars) aren't reflected in the README, it blocks the PR. | Python, Google GenAI SDK |
| **Module 2** | **The Janitor** | **FinOps Cost Guard**. Automatically detects and deletes "expired" cloud resources (Buckets, RGs) based on Tags to prevent cloud waste. Supports **AWS, Azure, and GCP**. | Python, Boto3, Azure SDK, Google Cloud SDK |
| **Module 3** | **The Guard** | **Cross-Repo Safety**. Automatically triggers integration tests in downstream consumer repositories whenever a core platform change is detected. | Github API (Repository Dispatch) |

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
*   Python 3.9+
*   **Google Gemini API Key**: For AI Analysis.
*   **Cloud Credentials**: AWS, Azure, or GCP credentials for Janitor features.

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-username/driftguard.git
cd driftguard

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Locally
Start the FastAPI server with hot-reload:
```bash
uvicorn api.index:app --reload
```
Acccess the dashboard at **http://localhost:8000/dashboard**.

---

## 🌐 Web Dashboard

The new UI provides a comprehensive view of your infrastructure governance:

*   **Landing Page**: `http://localhost:8000/`
*   **Dashboard**: `http://localhost:8000/dashboard`
*   **AI Guard**: `http://localhost:8000/ai-guard` - Visualize code drift.
*   **Janitor**: `http://localhost:8000/janitor` - Manage cloud resource cleanup.
*   **FinOps**: `http://localhost:8000/finops` - Cost forecasting and savings.
*   **Policy Editor**: `http://localhost:8000/policy` - Edit `policy.yaml`.
*   **Sentry**: `http://localhost:8000/sentry` - Cross-repo integration status.
*   **Logs**: `http://localhost:8000/logs` - Real-time system logs.

---

## 📦 Deployment

### Vercel
DriftGuard is configured for deployment on Vercel.

1.  Push your code to a GitHub repository.
2.  Import the project into Vercel.
3.  Vercel will automatically detect `api/index.py` based on `vercel.json`.
4.  Add your Environment Variables in the Vercel Dashboard.

---

## 📂 Project Structure

```bash
driftguard/
├── .github/                   # GitHub Actions Workflows
├── api/                       # Web Application
│   ├── templates/             # HTML/Jinja2 Templates (UI)
│   ├── static/                # Static Assets
│   └── index.py               # FastAPI Entrypoint
├── src/                       # Core Logic
│   ├── engine.py              # Policy Orchestrator
│   └── guards/                # Guard Modules
├── policy.yaml                # Governance Configuration
└── requirements.txt           # Python Dependencies
```
