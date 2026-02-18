
import requests
import os

def send_alert(message, severity="error"):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("[Notification] SLACK_WEBHOOK_URL not set. Skipping alert.")
        return

    color = "#FF0000" if severity == "error" else "#FFFF00"
    payload = {
        "attachments": [{
            "color": color,
            "title": f"DriftGuard Alert: {severity.upper()}",
            "text": message
        }]
    }
    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        response.raise_for_status()
        print(f"[Notification] Alert sent to Slack: {severity}")
    except Exception as e:
        print(f"[Notification] Failed to send alert: {e}")
