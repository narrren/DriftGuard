
import random
import time
import json
from datetime import datetime, timedelta

class DemoSimulator:
    def __init__(self):
        self.logs = []
        self.resources = self._generate_mock_resources()
        self.pipeline_status = {
            "policy": "pending",
            "ai_sync": "pending",
            "sentry": "pending",
            "janitor": "pending"
        }
        self.stats = {
            "savings": 0.0,
            "drift_score": 98,
            "system_state": "Healthy"
        }

    def _generate_mock_resources(self):
        """Generates initial fake cloud resources."""
        base_time = datetime.now()
        
        return [
            {
                "id": "dg-bucket-prod-01",
                "type": "S3 Bucket",
                "created_at": (base_time - timedelta(days=30)).strftime("%Y-%m-%d %H:%M"),
                "expiry": "N/A (Protected)",
                "status": "Protected",
                "tags": {"Environment": "Production"}
            },
            {
                "id": "dg-dev-env-pr-404",
                "type": "EC2 Instance",
                "created_at": (base_time - timedelta(hours=26)).strftime("%Y-%m-%d %H:%M"),
                "expiry": (base_time - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"), # Expired
                "status": "Expired",
                "tags": {"driftguard:expiry": "2024-03-10T10:00:00Z"}
            },
            {
                "id": "dg-test-db-shard-1",
                "type": "RDS Database",
                "created_at": (base_time - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
                "expiry": (base_time + timedelta(hours=19)).strftime("%Y-%m-%d %H:%M"),
                "status": "Active",
                "tags": {"driftguard:expiry": "Active"}
            },
            {
                "id": "dg-temp-storage-99",
                "type": "Azure Blob",
                "created_at": (base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
                "expiry": (base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), # Expired
                "status": "Expired",
                "tags": {"driftguard:expiry": "Expired"}
            },
             {
                "id": "dg-core-api-v2",
                "type": "GCP Function",
                "created_at": (base_time - timedelta(weeks=1)).strftime("%Y-%m-%d %H:%M"),
                "expiry": "N/A",
                "status": "Active",
                "tags": {"Owner": "PlatformTeam"}
            }
        ]

    def log_event(self, event_type, message, details=None):
        """Standardized JSON logging simulation."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "message": message,
            "details": details or {}
        }
        self.logs.append(log_entry)
        # Keep only last 50 logs
        if len(self.logs) > 50:
            self.logs.pop(0)
        return log_entry

    def run_pipeline_step(self, step_name):
        """Simulates latency and execution of a pipeline step."""
        self.log_event("pipeline_step_start", f"Starting {step_name}...")
        time.sleep(random.uniform(0.5, 1.5)) # Simulate work
        
        if step_name == "ai_sync":
            self.log_event("ai_analysis", "Scanning codebase for drift...", {"files_scanned": 12, "model": "Gemini 1.5 Pro"})
        elif step_name == "sentry":
            self.log_event("cross_repo_dispatch", "Triggering downstream consumers...", {"repos": ["consumer-app-a", "billing-service"], "status": "200 OK"})
        elif step_name == "janitor":
             self.log_event("cloud_scan", "Scanning for expired resources...", {"targets": ["aws", "azure", "gcp"]})

        self.pipeline_status[step_name] = "success"
        self.log_event("pipeline_step_complete", f"Completed {step_name} successfully.")
        return {"status": "success"}

    def delete_resource(self, resource_id):
        """Simulates resource deletion."""
        target = next((r for r in self.resources if r["id"] == resource_id), None)
        if target:
            if target["status"] == "Protected":
                 self.log_event("janitor_skip", f"Skipped protected resource: {resource_id}", {"reason": "Protected Tag Found"})
                 return False
            
            self.resources.remove(target)
            cost_saved = random.uniform(15.0, 120.0)
            self.stats["savings"] += cost_saved
            self.log_event("janitor_reap", f"Deleted resource: {resource_id}", {"cloud": "aws", "cost_saved": f"${cost_saved:.2f}", "strategy": "Hybrid Nuke"})
            return True
        return False

    def get_ai_analysis(self):
        """Mock AI Response."""
        return {
            "drift_detected": True,
            "suggestion": "You added `STRIPE_API_KEY` to `src/engine.py` but it is missing from `README.md`. \n\n**Suggested Fix:** Add `STRIPE_API_KEY` to the 'Environment Variables' table in README.",
            "confidence": 0.98
        }
