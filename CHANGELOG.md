# 📋 DriftGuard Project Tracker




---

## 📅 Changelog (Chronological)

### **2026-01-28 (Production Hardening Sprint)**
*   **[Observability]** Implemented Structured JSON Logging (`python-json-logger`) in `engine.py` and `janitor.py`.
*   **[Resiliency]** Added `tenacity` library for Exponential Backoff/Retries on AI and Cloud API calls.
*   **[Safety]** Implemented Global **Dry Run Mode** in `policy.yaml` (default: `true`).
*   **[Safety]** Added **Protected Tag Logic** ("Hard Block") in Janitor to prevent deletion of `Production` or `Protected` resources.
*   **[Reliability]** Added **Pydantic** Schema Validation for `policy.yaml`.
*   **[Security]** Migrated AWS Authentication to **OIDC (Zero Trust)**, removing long-lived usage of Access Keys in Github Actions.
*   **[Docs]** Updated `README.md`, `PROJECT_DIGEST.md`, and `DEMO.md` with new features.
*   **[Testing]** Initialized `tests/` directory and added `pytest` unit tests for the Engine.
*   **[Resiliency]** Fixed **Janitor Idempotency** by handling `NoSuchBucket` (404) errors in `_nuke_bucket`.
*   **[Safety]** Added **CLI Dry Run** (`--dry-run`) to `engine.py` to force global simulation mode.

### **2026-01-27 (Feature Enhancement)**
*   **[Janitor]** Added specific **Safety Checks** (log verification) before deletion logic in `janitor.py`.
*   **[IaC]** Configured Terraform **State Locking** (S3 Backend) in `main.tf`.
*   **[AI Guard]** Implemented **Manual Override** commmand (`/driftguard override`) to bypass AI checks.
*   **[Fix]** Fixed Azure Janitor expiry date parsing logic.
*   **[Docs]** Created `DEMO.md` script.

### **2026-01-26 (Project Initialization & Core Logic)**
*   **[Core]** Created `DriftGuard` repository and directory structure.
*   **[Module 1]** Implemented **AI Synchronizer** (`ai_sync.py`) using Google Gemini 1.5.
*   **[Module 2]** Implemented **Janitor** (`janitor.py`) for Multi-Cloud (AWS, Azure, GCP).
*   **[Module 3]** Implemented **Cross-Repo Guard** (`cross_repo.py`) using Repository Dispatch.
*   **[Engine]** Built the Policy Engine (`engine.py`) and `policy.yaml` configuration.
*   **[CI/CD]** Created GitHub Actions workflows (`driftguard-main.yml`, `janitor-cron.yml`).

---

## 🚧 Roadmap / To-Do

### Immediate Priorities
- [x] **Idempotency Fix**: Ensure Janitor `_nuke_bucket` handles `404 Not Found` errors gracefully.
- [ ] **Test Stability**: Enhance `tests/test_engine.py` to be environment-agnostic.

### Future Enhancements
- [ ] **Dashboard**: Build a Next.js UI for log visualization.
- [ ] **ChatOps**: Complete Slack/Teams integration for alert notifications.
- [ ] **Full OIDC**: Extend OIDC to Azure and GCP.
