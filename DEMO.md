# � Professor Presentation: DriftGuard Demo Master Script

**Goal:** Demonstrate DriftGuard as a "Production-Ready Internal Developer Platform" to your professor.
**Time Estimate:** 10 Minutes.

---

## 🏁 Phase 0: Pre-Demo Setup (Do this 5 mins before)
1.  **Open VS Code** to the `DriftGuard` folder.
2.  **Open the Browser** to your GitHub Repository > "Actions" tab.
3.  **Open 3 Key Files** in VS Code tabs (Command+P):
    *   `policy.yaml` (The config)
    *   `src/engine.py` (The state machine)
    *   `PROJECT_DIGEST.md` (Arch diagrams)
4.  **Open Terminal** in VS Code (`Ctrl + ~`).

---

## �️ Phase 1: The Pitch (1 Minute)
**Action:** Open `PROJECT_DIGEST.md` (preview mode) or just look at the professor.

**Script:**
> "Professor, in modern Cloud Engineering, there's a huge problem called 'Drift'.
> Teams create cloud resources and forget them (wasting money), or they write code and forget to document it (creating technical debt).
>
> I built **DriftGuard**. It's an automated governance engine that runs inside the CI/CD pipeline. It stops bad code from merging and cleans up cloud waste automatically. It uses a State Machine architecture I call 'UniFlow' and is designed with Zero-Trust security."

---

## 🟢 Phase 2: The AI Documentation Guard (3 Minutes)
**Goal:** Show that the system understands code semantics using AI.

**Step 1: Create a "Bad" Branch**
Type this in your terminal:
```bash
git checkout -b demo/professor-test
```

**Step 2: Inject "Undocumented" Code**
Open `src/engine.py`.
Scroll to the bottom (inside `main()`) and add this line:
```python
# Hiding a secret dependency here...
stripe_key = os.environ.get("STRIPE_SECRET_KEY")
```
*Save the file (Ctrl+S).*

**Step 3: Push the "Bad" Code**
```bash
git add src/engine.py
git commit -m "feat: add stripe payments"
git push origin demo/professor-test
```
*(GitHub will give you a link in the terminal to create a PR. Control+Click it to open browser).*

**Step 4: Create the PR**
*   Click **"Create Pull Request"**.
*   **Say:** "I just added a hard dependency on an Environment Variable (`STRIPE_SECRET_KEY`), but I didn't document it in the README or validation config. Normally, this breaks production."

**Step 5: The Block**
*   Wait ~30 seconds for the Action to run.
*   Show the **Red X** (Failure) on the PR page.
*   Show the **Bot Comment**: "❌ Documentation Drift Detected. You added `STRIPE_SECRET_KEY` but did not document it."
*   **Say:** "My AI agent scanned the git diff, realized I added a requirement, checked the docs, saw it was missing, and blocked the merge automatically."

---

## 🟡 Phase 3: The Janitor (The "FinOps" Drill) (2 Minutes)
**Goal:** Show infrastructure automation and "Self-Healing".

**Step 1: Navigate**
Go to GitHub Actions Tab.
Click **"FinOps Janitor Live Drill"** on the left sidebar.

**Step 2: Trigger**
Click the **"Run workflow"** button.
Leave inputs as default. Click green **Run workflow**.

**Step 3: Watch & Explain**
*   Click into the running job.
*   **Say:** "This represents a developer creating a temporary test environment. Terraform is provisioning a real S3 bucket right now."
*   Wait for the **"Run Janitor"** step to start.
*   **Point to Logs:** Look for the line `[Janitor] Found Tag... driftguard:expiry`.
*   **Say:** "The Janitor sees the tag is expired. It doesn't ask permission. It executes a 'Safe Nuke' strategy to kill the cost immediately. It handled the cleanup without human intervention."

---

## 🔵 Phase 4: Production Hardening (The "A" Grade Component) (3 Minutes)
**Goal:** Prove this is engineered, not just hacked together.

**Step 1: Safety CLI (Dry Run)**
*   Go back to VS Code Terminal.
*   **Say:** "You might ask: Is this safe? Could a bug delete our database?"
*   Run this command:
    ```bash
    python src/engine.py --event pull_request --action opened --dry-run
    ```
*   **Point to Output:** Show the `[Dry Run] Would delete...` logs.
*   **Say:** "I implemented a global CLI override. We can simulate the entire governance policy locally without touching a single real API. It's safe by default."

**Step 2: Observability (Audit)**
*   Go back to the GitHub Action run you just finished.
*   Scroll to the bottom **"Artifacts"** section.
*   Download `driftguard-janitor-logs`.
*   Open the JSON file.
*   **Say:** "We don't just print text. We emit structured JSON telemetry (`timestamp`, `resource_id`, `action`). This connects to tools like Splunk for enterprise compliance auditing."

---

## 🏁 Phase 5: Conclusion
**Say:**
> "DriftGuard isn't just a script. It's a Zero-Trust, Idempotent, Config-Driven Platform. It allows engineering teams to move fast because the 'Guardrails' are automated."
