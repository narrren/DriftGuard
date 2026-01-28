# 📋 DriftGuard Project Tracker

This document tracks the evolution of DriftGuard from MVP to a Production-Ready Platform Engineering Governance Suite.

---

## 🧠 Strategic Evolution (Architectural Decisions)

This breakdown tracks how the project shifted from a "simple automation script" to a "Production-Ready Platform Engineering Suite."

### 1. Architectural Shift: From Scripting to Engine-Based (UniFlow)
*   **Issue:** Hardcoding automation logic (e.g., `if pr_opened, do x`) makes the tool brittle and hard to maintain as the team grows.
*   **Fix:** Created the **"UniFlow"** architecture—a central `engine.py` that acts as a state machine, governed by a `policy.yaml` file.
*   **Result:** The system is now **Config-Driven**. A non-developer or a manager can change governance rules (like changing TTL from 24h to 12h) by editing a YAML file without touching the source code. It makes the tool modular and extensible.

### 2. Security Evolution: From Access Keys to OIDC
*   **Issue:** Storing AWS/Azure secret keys in GitHub Actions is a security risk; if the repo is compromised, the keys are leaked and can be used indefinitely.
*   **Fix:** Implemented **OIDC (OpenID Connect) "Zero Trust"** authentication.
*   **Result:** Long-lived keys are eliminated. DriftGuard now requests a temporary, short-lived token from the Cloud Provider for every run. It is compliant with modern enterprise security standards.

### 3. Resiliency Logic: The AI + Regex Fallback
*   **Issue:** Relying 100% on an AI (LLM) for documentation checks is risky. If the API is down or the model "hallucinates," the whole pipeline stops or allows bad code through.
*   **Fix:** Integrated a **Deterministic Regex Guard** as a fallback for the AI Synchronizer.
*   **Result:** If the AI fails, the system automatically falls back to a code-based scanner that looks for critical items (like new environment variables). This ensures 100% uptime for safety checks regardless of AI availability.

### 4. Reliability Logic: Pydantic Schema Validation
*   **Issue:** A simple typo in the `policy.yaml` configuration could cause the Python script to crash halfway through a cloud deployment, leaving resources in an undefined state.
*   **Fix:** Forced all configuration through **Pydantic Model Validation** at the startup of `engine.py`.
*   **Result:** The system "fails fast." If the configuration is wrong, the tool refuses to start and tells the user exactly which line in the YAML is incorrect. This prevents logic-based production outages.

### 5. FinOps Logic: The Hybrid "Safe Nuke" Strategy
*   **Issue:** Automated cleanups often fail if the Infrastructure-as-Code (Terraform) state file is locked, corrupted, or deleted. This leads to "Zombie" resources that continue to cost money.
*   **Fix:** Developed a **Two-Phase Destruction Strategy**. Phase 1 tries a clean Terraform destroy; Phase 2 uses a Direct Cloud API "Nuke" as a fallback.
*   **Result:** It guarantees 100% cost elimination. Even if the deployment tool breaks, the Janitor will find the resource via its tag and delete it directly, ensuring no accidental cloud bills.

### 6. Safety Logic: Blast Radius & Kill Switches
*   **Issue:** An automated "Janitor" script is dangerous; a bug could theoretically delete a production database or the entire company infrastructure.
*   **Fix:** Implemented **Namespace Filtering** (must start with `dg-`) and **Protected Tag** logic (ignores resources tagged `Environment: Production`).
*   **Result:** The Blast Radius is contained. The script is programmatically "blind" to any resource it doesn't own, making it safe to run in a production account.

### 7. Observability: JSON Structured Logging
*   **Issue:** Standard `print()` statements are hard to search and useless for automated monitoring tools like Datadog or Splunk.
*   **Fix:** Switched to **Structured JSON Logging** (`python-json-logger`) and automatic Build Artifact uploads.
*   **Result:** Every action taken by DriftGuard is searchable and auditable. If a resource is deleted, there is a clear JSON trace showing the "Why, When, and Who," making the tool enterprise-compliant for audits.

### 8. Reliability: Exponential Backoff (Tenacity)
*   **Issue:** Cloud APIs and AI APIs frequently experience "transient failures" (temporary network blips). Standard scripts crash on the first failure.
*   **Fix:** Wrapped all external API calls with **Tenacity** retries using exponential backoff.
*   **Result:** The system is Self-Healing. It will automatically wait and retry a failed call before giving up, reducing "Flaky" builds and developer frustration.

### 📈 Summary of Current Utility

| Feature | Current Usefulness |
| :--- | :--- |
| **DriftGuard** | Saves money by automatically killing test environments the moment they aren't needed. |
| **Synchronizer** | Keeps documentation 100% accurate without developers having to manually check it. |
| **The Guard** | Prevents "Microservice Chaos" by ensuring a change in one repo doesn't break another. |
| **Engine** | Allows the tool to scale from 1 repo to 100 repos just by changing a YAML file. |
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
