# DriftGuard: Comprehensive Project Digest 🛡️

## 1. Executive Summary
**DriftGuard** is an autonomous **Platform Engineering Governance Suite** designed to prevent "Broken Factory" syndrome in modern DevOps environments. It acts as a "Governance-as-Code" layer that sits within the CI/CD pipeline, automatically enforcing policies related to **Documentation**, **Cost Management (FinOps)**, and **Integration Stability**. 

**Security Note:** DriftGuard employs **OIDC (OpenID Connect)** "Zero Trust" authentication for Cloud Providers, eliminating the need for long-lived access keys.

By treating governance as a config-driven state machine, DriftGuard eliminates manual toil, ensures compliance without friction, and maintains a clean, cost-efficient cloud footprint across **AWS, Azure, and Google Cloud Platform (GCP)**.

---

## 2. Core Architecture: "The UniFlow" 🧠
The system functions as a modular State Machine orchestrated by GitHub Actions and driven by a central python engine.

### The Brain: `src/engine.py`
*   **Role:** The central orchestrator.
*   **Function:** It parses the `policy.yaml` configuration file at runtime to determine which logic "Guards" need to be executed for the current PR event.
*   **Design Pattern:** State Machine. It moves the PR through defined stages (e.g., `ai_doc_check` -> `infrastructure_preview` -> `cross_repo_safety`).

### The Configuration: `policy.yaml`
*   **Role:** The Single Source of Truth.
*   **Function:** Defines rules in simple usage:
    *   Which guards are enabled?
    *   What is the enforcement level (`BLOCK` vs `WARNING`)?
    *   What are the operational parameters (e.g., `ttl_hours: 24`, `target: [aws, azure]`)?

---

## 3. The Three Guardians (Modules) 👮‍♂️

### 🟢 Module 1: The Synchronizer (AI Documentation Guard)
*   **Goal:** Solve "Documentation Drift" where code evolves but docs stagnate.
*   **Tech:** Python, Google Gemini 1.5 Pro/Flash, PyGithub.
*   **Workflow:**
    1.  Inspects the Pull Request Diff.
    2.  Reads the current `README.md`.
    3.  **AI Analysis:** Uses an LLM to semantically compare the code changes against the documentation.
    4.  **Resiliency Fallback:** If the AI is down, a **Regex Guard** kicks in to scan for undocumented environment variables (`os.getenv`, `os.environ`) to ensure 100% safety integration.
    5.  **Action:** If drift is detected (e.g., new undocumented Env Var), it **BLOCKS** the PR and comments with a specific suggested fix.

### 🟡 Module 2: The Janitor (FinOps Cost Guard)
*   **Goal:** Eliminate "Zombie Infrastructure" and reduce cloud waste.
*   **Tech:** Boto3 (AWS), Azure SDK, Google Cloud Storage SDK.
*   **Multi-Cloud Support:** Fully functional across **AWS, Azure, and GCP**.
*   **Workflow:**
    1.  Scans cloud resources (S3 Buckets, Azure Resource Groups, GCP Buckets).
    2.  Checks for specific tags (e.g., `driftguard:expiry`).
    3.  **Logic:** If `Current Time > Expiry Tag`, the resource is deemed "Expired".
    4.  **Action:** Automatically **DESTROYS** the resource (handles dependency cleanup like emptying buckets first) to stop billing.

### 🔴 Module 3: The Sentry (Cross-Repo Integration Guard)
*   **Goal:** Prevent changes in the Platform Core from breaking downstream Consumer Apps.
*   **Tech:** GitHub API (`repository_dispatch` event).
*   **Workflow:**
    1.  Listens for valid changes in the core repository.
    2.  Identifies "Consumer" repositories defined in `policy.yaml`.
    3.  **Action:** Triggers a remote `repository_dispatch` event in those consumer repos, forcing them to run their own integration tests against the new core version.
    4.  **Security:** Uses a dedicated `DRIFTGUARD_PAT` (Personal Access Token) to authenticate across repository/organization boundaries securely.

---

## 4. Technology Stack 🛠️

| Category | Technology | Usage |
| :--- | :--- | :--- |
| **Language** | **Python 3.10+** | Core logic for all guards and the engine. |
| **Orchestration** | **GitHub Actions** | CI/CD runner, workflow automation (`workflow_call`). |
| **AI / ML** | **Google Gemini** | Semantic code analysis (via `google-genai` SDK). |
| **Cloud (AWS)** | **Boto3** | Resource scanning and deletion for AWS S3. |
| **Cloud (Azure)** | **Azure SDK** | Resource Group management and cleanup. |
| **Cloud (GCP)** | **Google Cloud SDK** | Storage Bucket lifecycle management. |
| **IaC** | **Terraform** | Provisioning test infrastructure. Configured with **S3 Backend** for State Locking. |
| **Formatting** | **YAML** | Policy definition and configuration. |
| **Frontend** | **HTML5/Tailwind** | Project Landing Page. |

---

## 5. Security & Production Hardening 🔐
*   **Credential Management:**
    *   Uses **GitHub Secrets** for all sensitive keys (`AWS_ACCESS_KEY`, `GEMINI_API_KEY`, etc.).
    *   **PAT Implementation:** Explicitly prioritizes `DRIFTGUARD_PAT` over `GITHUB_TOKEN` to ensure granular permissions for cross-repo operations.
*   **Fail-Safe Mechanisms:**
    *   **AI Fallback:** The system does not fail open. If the AI provider errors out, a deterministic **Regex Scanner** ensures critical checks (like Env Vars) still pass.
*   **Sanitized Inputs:**
    *   Inputs from PRs are treated as data; the engine parses text diffs rather than executing arbitrary code.

---

## 6. Project Structure 📂
```bash
DriftGuard/
├── .github/workflows/
│   ├── driftguard-main.yml    # Main Orchestrator (Reusable Workflow)
│   ├── janitor-cron.yml       # Scheduled FinOps Cleanup Job
│   └── consumer-simulation.yml # Test workflow for Cross-Repo logic
├── src/
│   ├── engine.py              # The Logic Brain / State Machine
│   ├── guards/
│   │   ├── ai_sync.py         # AI Documentation Logic
│   │   ├── janitor.py         # Multi-Cloud Cleanup Logic
│   │   └── cross_repo.py      # Downstream Dispatch Logic
├── terraform/                 # Infrastructure Code (for demos)
├── policy.yaml                # Governance Configuration
├── requirements.txt           # Python Dependencies
├── README.md                  # User Documentation
├── DEMO.md                    # Step-by-Step Demo Script
└── index.html                 # Marketing Landing Page
```

## 7. Operational Best Practices & Limitations ⚠️

### A. Cloud IAM Requirements (The Janitor)
For the Janitor to function, the provided credentials must have specific permissions. It is recommended to use "Least Privilege" access targeting only resources with `driftguard` tags, but here are the baseline permissions:
*   **AWS:** `s3:ListAllMyBuckets`, `s3:GetBucketTagging`, `s3:DeleteBucket`, `s3:DeleteObject` (Recursive).
*   **Azure:** `Contributor` role on the specific Subscription or Resource Groups (to allow `resources.begin_delete`).
*   **GCP:** `Storage Admin` (to allow `buckets.delete` and `objects.delete`).

### B. The "Nuke" Strategy vs Terraform State
The Janitor uses a **Direct API Destruction** strategy ("Nooking"). It searches for expired tags and deletes resources immediately via the Cloud SDKs.
*   **Benefit:** It works even if the Terraform State file is lost, corrupted, or locked. It is the ultimate cleanup for "Orphaned" resources.
*   **Trade-off:** It does not update the Terraform State file. If you run `terraform plan` afterwards, Terraform might be confused that resources are missing.
*   **Best Use Case:** Use this for **Ephemeral Sandbox Environments** (e.g., `dev-pr-123`) where the state file itself is also ephemeral or irrelevant after the PR closes.

### C. Handling AI False Positives
LLMs can occasionally "hallucinate" or flag a false positive (claiming drift where there is none).
*   **Mitigation:** If this becomes a blocker for your team, edit `policy.yaml` and change the severity of `ai_doc_check` from `block` to `warning`.
    ```yaml
    - name: ai_doc_check
      severity: warning # Log it, but don't stop the merge
    ```
*   **Manual Override:** Developers can simply type `/driftguard override` in the PR body or comments to bypass the AI check for that specific PR.

---

## 8. Conclusion
DriftGuard successfully bridges the gap between **velocity** and **control**. By automating the "boring" parts of governance (docs, cleanup, testing), it allows Platform Engineers to ship faster while ensuring the platform remains documented, cost-efficient, and stable. It is a production-ready template for modern IDP (Internal Developer Platform) governance.
