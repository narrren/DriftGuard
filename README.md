# DriftGuard 🛡️

### **Autonomous Platform Engineering Suite for Config-Driven Governance**

**Status:** 🟢 Active | **Version:** 1.0.0

DriftGuard acts as a "Governance-as-Code" layer, automating the critical checks that prevent "Broken Factory" syndrome in Platform Engineering. Instead of manual reviews, it uses a central policy engine to enforce Documentation, Cost, and Integration safety.

---

## ⚡ Key Features (The 3 Pillars)

| Module | Name | Function | Tech Stack |
| :--- | :--- | :--- | :--- |
| **Module 1** | **The Synchronizer** | **AI Documentation Guard**. Uses Google Gemini 1.5 to semantic-check Pull Requests. If code changes (e.g., new Env Vars) aren't reflected in the README, it blocks the PR. Includes **Manual Override** via comments. | Python, Google GenAI SDK, Github Actions |
| **Module 2** | **The Janitor** | **FinOps Cost Guard**. Automatically detects and deletes "expired" cloud resources (Buckets, RGs) based on Tags. includes **Safe-Check** (verifies tag presence) and supports **AWS, Azure, GCP**. | Python, Boto3, Azure SDK, Google Cloud SDK |
| **Module 3** | **The Guard** | **Cross-Repo Safety**. Automatically triggers integration tests in downstream consumer repositories whenever a core platform change is detected. | Github API (Repository Dispatch), YAML |

---

## 🏗️ Architecture

DriftGuard uses a **State Machine** strategy. A central `policy.yaml` dictates which guards are active for every Pull Request.

```mermaid
graph LR
    A[Pull Request] --> B[GitHub Actions]
    B --> C{DriftGuard Engine}
    C -->|Read Policy| D[policy.yaml]
    D --> E[AI Guard]
    D --> F[FinOps Janitor]
    D --> G[Cross-Repo Dispatch]
    E -->|Fail?| H[Block Merge]
    E -->|Pass?| I[Allow Merge]
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
*   **GitHub Repository**: Hosted on GitHub.
*   **AWS Account**: For FinOps demonstrations.
*   **Google Gemini API Key**: For AI Analysis (Free tier works).

### 2. Configure Secrets
Navigate to **Settings > Secrets and variables > Actions** and add:
*   `GEMINI_API_KEY`: Your Google Gemini API Key.
*   `AWS_ROLE_ARN`: **Attributes of OIDC Role**. The ARN of the IAM Role you created for GitHub Actions OIDC (Trust Relationship).
*   *(Deleted)* `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`: No longer required (Zero Trust).
*   `AZURE_SUBSCRIPTION_ID`: (Optional) For Azure Resources.
*   `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`: Azure Service Principal credentials.
*   `GCP_CREDENTIALS_JSON`: (Optional) Google Cloud Service Account Key (JSON).
*   `DRIFTGUARD_PAT`: (Recommended) A Personal Access Token with `repo` scope for Cross-Repo dispatching.
*   `DATABASE_URL`: (Optional) Example variable for testing the AI Guard.

### 3. Usage
The platform runs automatically on every Pull Request.

**Configuration:**
Edit `policy.yaml` to enable/disable specific guards:
```yaml
stages:
  - name: ai_doc_check
    enabled: true
    severity: block
```

---

## 🎥 How to Demonstrate (The Demo Script)

See [DEMO.md](DEMO.md) for a step-by-step presentation script.

### 1. Trip the AI Guard 🧠
1.  Add a new environment variable requirement in `src/engine.py`.
2.  Open a PR **without** updating the README.
3.  **Result:** PR assumes "Drift" and blocks the merge.

### 2. Run the Janitor 🧹
1.  Go to **Actions > FinOps Janitor Live Drill**.
2.  Run the workflow.
3.  **Result:** It provisions a live S3 bucket, detects it as "Expired", and reaps it immediately.

### 3. Verify Cross-Repo Safety 🛡️
1.  Open any PR in the core repo.
2.  Check the **Actions** tab.
3.  **Result:** A "Consumer App Integration Test" workflow is automatically triggered to verify downstream compatibility.

---

## 📂 Project Structure

```bash
driftguard/
├── .github/workflows/
│   ├── driftguard-main.yml    # (The Orchestrator) Running on every PR
│   ├── janitor-cron.yml       # (The Scheduler) Running hourly cleanup
│   └── finops-drill.yml       # (The Demo) Manual verification tool
├── src/
│   ├── engine.py              # (The Brain) Parses policy and executes modules
│   ├── guards/
│   │   ├── ai_sync.py         # Module 1: AI Logic
│   │   ├── janitor.py         # Module 2: FinOps Logic
│   │   └── cross_repo.py      # Module 3: Dispatch Logic
├── terraform/                 # Infrastructure Templates for AWS
├── policy.yaml                # The Source of Truth for Governance
└── requirements.txt           # Python Dependencies
```

## ⚙️ Environment Variables Reference
| Variable | Description |
| :--- | :--- |
| `DRIFTGUARD_PAT` | **Recommended**. Personal Access Token for triggering workflows in external repositories (Cross-Repo Guard). |
| `ANY_ENV_VAR` | The AI Guard now scans for *any* `os.getenv` or `os.environ` usage in your code. Check the README! |


