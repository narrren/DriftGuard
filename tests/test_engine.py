import sys
import os
import yaml
import pytest
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.engine import load_policy, execute_stage, PolicyModel

# 1. Test Schema Validation (Pydantic)
def test_valid_policy_loading(tmp_path):
    policy_content = {
        "version": "1.0",
        "description": "Test Policy",
        "stages": [
            {
                "name": "ai_doc_check",
                "type": "documentation",
                "enabled": True,
                "severity": "block",
                "trigger_on": ["opened"],
                "config": {"llm_provider": "gemini"}
            }
        ]
    }
    
    p = tmp_path / "policy.yaml"
    p.write_text(yaml.dump(policy_content))
    
    loaded = load_policy(str(p))
    assert loaded['stages'][0]['name'] == 'ai_doc_check'

def test_invalid_policy_schema(tmp_path):
    # Missing 'trigger_on' field which is required
    policy_content = {
        "stages": [
            {
                "name": "broken_stage",
                "type": "test",
                "enabled": True
            }
        ]
    }
    
    p = tmp_path / "bad_policy.yaml"
    p.write_text(yaml.dump(policy_content))
    
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        load_policy(str(p))
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

# 2. Test Idempotency & Error Handling
def test_janitor_safe_scan():
    import src.guards.janitor
    
    with patch.object(src.guards.janitor, 'scan_resources', side_effect=Exception("API Throttling")):
        # Ideally should not crash the engine
        from src.engine import execute_stage
        stage = {
            "name": "janitor_cleanup",
            "type": "cleanup",
            "trigger_on": ["closed"],
            "enabled": True,
            "config": {}
        }
        
        # Execute
        # We expect it to catch the exception and log error, returning False (status)
        # Since severity defaults to 'warning', it should continue (or print warning).
        # We patch print/logging to verify but simplistically:
        execute_stage(stage, {}, "closed")
        # If it didn't raise SystemExit(1), it passed the resiliency check.

