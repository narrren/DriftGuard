# 🎥 DriftGuard Demo Script

This guide provides a step-by-step script to demonstrate the capabilities of the **DriftGuard** platform.

---

## 🟢 Module 1: The AI Synchronizer (Documentation Guard)
**Scenario:** A developer adds a new environment variable requirement but forgets to document it.

1.  **Create a Branch:**
    ```bash
    git checkout -b demo/bad-pr-test
    ```
2.  **Make a Change:**
    Add this line to `src/engine.py`:
    ```python
    # New dependency
    stripe_key = os.environ.get("STRIPE_API_KEY") 
    ```
3.  **Push & Open PR:**
    Push the branch and open a Pull Request on GitHub.
4.  **Observe:**
    - Wait ~30 seconds.
    - The `DriftGuard Engine` check will **FAIL**.
    - A bot comment will appear: *"❌ Documentation Drift Detected. You added `STRIPE_API_KEY` but did not document it."*
    - **(Optional) Bypass:** Reply with `/driftguard override`. The check will re-run and **PASS**, demonstrating the manual intervention capability.

---

## 🟡 Module 2: The Janitor (FinOps Guard)
**Scenario:** An ephemeral environment was created for testing but "forgotten" (tagged with an old expiry date).

1.  Go to the **Actions** tab in GitHub.
2.  Select **FinOps Janitor Live Drill** from the left sidebar.
3.  Click **Run workflow** (Leave "Simulate EXPIRED" as `true`).
4.  **Observe:**
    - Click into the run details.
    - See Terraform **Provision** a real S3 Bucket.
    - See the Python Janitor script **Scan** the cloud.
    - Logs will show: `EXPIRED: driftguard-env-xxxx ... DESTROYING... ✔ REAPED`.

---

## 🔴 Module 3: The Guard (Cross-Repo Safety)
**Scenario:** A change in the Core Platform triggers automatic regression testing in downstream consumer apps.

1.  **Observe Recent Actions:**
    - Go to the **Actions** tab.
    - Look for **"Consumer App Integration Test"**.
    - Note that valid Pull Requests automatically trigger this workflow via `repository_dispatch`.
    - *(Note: Ensure `DRIFTGUARD_PAT` is set in Secrets if dispatching to a different organization or private repo).*
    - This proves DriftGuard is communicating across the repository boundary to enforce safety.

---

## 🔵 Module 4: Production Safety & Observability (The "Hardening" Layer)
**Scenario:** Prove to the professor that this isn't just a toy script, but enterprise-ready software.

1.  **Safety CLI (Dry Run):**
    *   Open your terminal (VS Code).
    *   Run the engine in "Simulation Mode":
        ```bash
        python src/engine.py --event pull_request --action opened --dry-run
        ```
    *   **Observe:** The logs will distinctly say `🔧 Dry Run Override Enabled via CLI` and `[Dry Run] Would delete...`. Explain that this "Safety Switch" prevents accidental data loss during maintenance.

2.  **Observability (Audit Trails):**
    *   Go to any completed GitHub Action run.
    *   Scroll down to the **Artifacts** section.
    *   Download `driftguard-engine-logs` or `driftguard-janitor-logs`.
    *   Open the JSON file to show the structured data (Events, Timestamps, Resource IDs).
    *   **Pitch:** "Professor, we don't just print text. We emit structured telemetry that can be piped into Splunk or Datadog for enterprise monitoring."

---
**Summary for Interviewers:**
> "DriftGuard is a config-driven Internal Developer Platform (IDP) that enforces governance (Docs, Cost, Integration) seamlessly in the CI/CD pipeline using Python, Terraform, and AI."
