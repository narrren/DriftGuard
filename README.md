# DriftGuard 🛡️

**An Autonomous Platform Engineering Suite for Config-Driven Governance.**

DriftGuard acts as a "Governance-as-Code" layer between your Pull Request and the Cloud. It solves the "Broken Factory" problem by ensuring:
1.  **Documentation Integrity**: Code changes must match README updates (AI-Verified).
2.  **FinOps Control**: Ephemeral environments are automatically reaped after 24h or PR closure.
3.  **Cross-Repo Safety**: Changes in Core trigger integration tests in Consumers before merge.

---

## 🏗️ Architecture

DriftGuard uses a **State Machine** strategy. A central `policy.yaml` dictates which guards are active.

`PR Open` -> **Engine** -> `policy.yaml` -> [ **AI Guard** | **Janitor** | **Cross-Repo** ] -> `Merge Allow/Block`

---

## 🚀 Quickstart Guide

### 1. Fork & Clone
Fork this repository and clone it locally.
```bash
git clone https://github.com/YOUR_USERNAME/DriftGuard.git
cd DriftGuard
```

### 2. Configure Secrets
Go to **Settings > Secrets and variables > Actions** and add:
- `GEMINI_API_KEY`: Your Google Gemini API Key.
- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY`: AWS User with S3 full access.
- `GITHUB_TOKEN`: Automatically provided, but ensure permissions are enabled.

### 3. Update Policy
Edit `policy.yaml` to enable/disable specific guards.
```yaml
stages:
  - name: ai_doc_check
    enabled: true
    severity: block
```

### 4. Run Locally (Test Mode)
You can test the engine logic by mocking the environment check:
```bash
pip install -r requirements.txt
python src/engine.py --event pull_request --action opened
```

### 5. Deploy
Push a change!
1. Create a new branch.
2. Change a function signature in code (e.g., `src/engine.py`) but **DO NOT** update the README.
3. Open a PR.
4. Watch DriftGuard **Block** the merge with a suggested fix!

---

## 📂 Project Structure

- `driftguard-core/`
    - `.github/workflows/` (The Orchestrator)
    - `src/`
        - `engine.py` (The Brain)
        - `guards/` (The Modules: AI, Janitor, Guard)
    - `terraform/` (Infrastructure Templates)
    - `policy.yaml` (The Source of Truth)
