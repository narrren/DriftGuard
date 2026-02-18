# DriftGuard Project Digest 🛡️

**Date:** 2026-02-18
**Status:** 🟢 Active | Ready for Deployment
**Version:** 1.0.0

---

## 1. Executive Summary
DriftGuard is an autonomous "Governance-as-Code" platform designed to solve the "Broken Factory" syndrome in modern Platform Engineering. It replaces manual governance reviews with an automated policy engine that enforces:

1.  **Documentation Consistency**: Ensuring code changes (like new Env Vars) are reflected in documentation (README).
2.  **Cost Optimization (FinOps)**: Automatically detecting and cleaning up expired cloud resources across AWS, Azure, and GCP.
3.  **Integration Safety**: Triggering downstream integration tests to prevent breaking changes in consumer applications.

The project includes a **Feature-Rich Web Dashboard** for visualization and management.

---

## 2. System Architecture

The core of DriftGuard is a **State Machine** engine that parses a central `policy.yaml` configuration file and executes specific "Guard" modules based on the context (e.g., Pull Request, Cron Job, API Call).

```mermaid
graph TD
    User[User / CI System] -->|Interacts| API[FastAPI Backend]
    User -->|Views| Dashboard[Web Dashboard]
    API -->|Triggers| Engine[Policy Engine (src/engine.py)]
    Engine -->|Reads| Policy[policy.yaml]
    
    subgraph "The Guards (Modules)"
        Engine -->|Executes| AISync[AI Documentation Guard]
        Engine -->|Executes| Janitor[Cloud Janitor (FinOps)]
        Engine -->|Executes| CrossRepo[Cross-Repo Safety]
    end
    
    AISync -->|Gemini 1.5 Pro| GenAI[Google GenAI]
    Janitor -->|SDKs| Cloud[AWS / Azure / GCP]
    CrossRepo -->|Dispatch| GitHub[GitHub API]
```

---

## 3. Core Modules

### 🧠 Module 1: AI Documentation Guard (`src/guards/ai_sync.py`)
*   **Function**: Analyzes code diffs in Pull Requests. Use Google Gemini 1.5 to semantically understand if meaningful changes (features, env vars) require documentation updates.
*   **Logic**:
    *   Fetches PR Diffs and current README.
    *   Prompts Gemini to identify "Drift" (undocumented changes).
    *   **Fallback Mechanism**: Uses Regex to deterministically catch `os.getenv` calls if AI fails.
    *   **Action**: Blocks PR merge if drift is detected.

### 🧹 Module 2: automated Janitor (`src/guards/janitor.py`)
*   **Function**: Scans cloud environments for "expired" resources based on tags (e.g., `driftguard:expiry`).
*   **Supported Clouds**:
    *   **AWS**: S3 Buckets, EC2.
    *   **Azure**: Resource Groups.
    *   **GCP**: Storage Buckets.
*   **Integration**:
    *   Runs on a schedule or via API trigger.
    *   Supports `dry_run` mode for safety.
    *   Fully integrated into the FinOps Dashboard for visualization.

### 🛡️ Module 3: Cross-Repo Guard (`src/guards/cross_repo.py`)
*   **Function**: Prevents upstream platform changes from breaking downstream consumer apps.
*   **Logic**:
    *   Triggers `repository_dispatch` events to consumer repositories.
    *   Can wait for downstream CI status before allowing platform merge.

---

## 4. Web Dashboard & API

The project includes a modern, responsive web interface built with **FastAPI**, **Jinja2**, and **TailwindCSS**.

### 🌐 API Endpoints (`api/index.py`)
*   `GET /`: Landing Page.
*   `GET /login`: User Authentication.
*   `GET /dashboard`: Main Analytics Dashboard.
*   `GET /ai-guard`: **AI Documentation Guard**.
    *   Features: Diff Analysis, Drift Detection, AI Override.
*   `GET /finops`: **Cost Optimization Center**.
    *   Features: Cost Forecast Graph (Budget vs Actual), Savings Recommendations.
*   `GET /janitor`: **Multi-Cloud Cleanup Engine**.
    *   Features: Resource Scanning, Expiry Tag Management, Cleanup Actions.
*   `GET /sentry`: **Integration Safety Guard**.
    *   Features: Cross-Repo Dependency Graph, CI Status, Dispatch Triggers.
*   `GET /policy`: Policy Configuration Editor.
*   `GET /logs`: System Logs Console.
*   `GET /settings`: Platform Connectivity Settings.

### 🎨 Visualizations (`api/templates/finops.html`)
*   **Cost Forecast Chart**: CSS-based bar chart visualizing monthly spend vs budget.
*   **Recommendation Engine**: Cards showing potential savings (e.g., "Right-size EC2").

---

## 5. Deployment & Configuration

### 📄 Configuration (`policy.yaml`)
The central brain of the application.
```yaml
stages:
  - name: ai_doc_check
    enabled: true
    config:
      llm_provider: gemini
  - name: infrastructure_preview
    config:
      target: ["aws", "azure", "gcp"]
      ttl_hours: 24
```

### 📦 Dependencies (`requirements.txt`)
*   **Core**: `fastapi`, `uvicorn`, `pyyaml`, `requests`
*   **Cloud SDKs**: `boto3`, `azure-identity`, `azure-mgmt-resource`, `azure-storage-blob`, `google-cloud-storage`
*   **AI**: `google-genai`
*   **Utils**: `python-dateutil`, `PyGithub`

### 🚀 Setup Instructions
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Environment Variables**:
    *   `GEMINI_API_KEY`: Required for AI Guard.
    *   `GITHUB_TOKEN`: Required for PR interactions.
    *   `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`: For AWS Janitor.
    *   `AZURE_SUBSCRIPTION_ID`: For Azure Janitor.
    *   `GOOGLE_APPLICATION_CREDENTIALS`: For GCP Janitor.
3.  **Run Locally**:
    ```bash
    uvicorn api.index:app --reload
    ```

---

## 6. Directory Structure
```text
DriftGuard/
├── .github/                   # GitHub Actions Workflows
├── api/                       # Web Application
│   ├── templates/             # HTML/Jinja2 Templates (UI)
│   ├── static/                # Static Assets
│   └── index.py               # FastAPI Entrypoint
├── src/                       # Core Logic
│   ├── engine.py              # Policy Orchestrator
│   └── guards/                # Guard Modules
│       ├── ai_sync.py         # AI Logic
│       ├── janitor.py         # Cloud Logic
│       └── cross_repo.py      # Integration Logic
├── terraform/                 # IaC Templates
├── policy.yaml                # Configuration
├── requirements.txt           # Python Dependencies
├── vercel.json                # Deployment Config
├── PROJECT_DIGEST.md          # This File
└── README.md                  # General Documentation
```
