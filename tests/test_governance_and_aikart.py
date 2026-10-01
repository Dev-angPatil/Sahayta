"""
tests/test_governance_and_aikart.py
Validates the Dynamic Hierarchical Governance Router and official aiKart Sandbox Runner.
"""

import os
import json
import pytest
from pathlib import Path

from sahayta.agent import SahaytaAgent
from sahayta.triage.governance_router import resolve_governance_authority, SovereignTier
from sahayta.aikart_runner import run as run_aikart


def test_governance_router_union_tier():
    """Validates that Central subjects (Railways, Banking) map to SovereignTier.UNION."""
    auth, reasoning = resolve_governance_authority("Train 12952 ticket refund delayed under PNR 2490182910.")
    assert auth.tier == SovereignTier.UNION
    assert "Railways" in auth.ministry_or_department
    assert auth.standard_sla_days == 30
    assert any("Union" in r for r in reasoning)


def test_governance_router_state_tier():
    """Validates that State subjects (PDS, DISCOM) map to SovereignTier.STATE."""
    auth_pds, _ = resolve_governance_authority("Ration dealer FPS1042 not distributing foodgrains.")
    assert auth_pds.tier == SovereignTier.STATE
    assert "Food" in auth_pds.ministry_or_department
    assert auth_pds.standard_sla_days == 7

    auth_discom, _ = resolve_governance_authority("BESCOM power outage in Indiranagar transformer burnt.")
    assert auth_discom.tier == SovereignTier.STATE
    assert auth_discom.standard_sla_days == 2


def test_governance_router_local_tier():
    """Validates that Municipal subjects (Water, Sewer) map to SovereignTier.LOCAL."""
    auth, _ = resolve_governance_authority("Delhi Jal Board water supply contaminated and pipe burst.")
    assert auth.tier == SovereignTier.LOCAL
    assert auth.standard_sla_days == 1


def test_agent_chat_returns_agentic_primitives():
    """Validates that SahaytaAgent returns tools_executed, grounded_data, and action."""
    agent = SahaytaAgent()
    res = agent.chat("Train 12952 refund delayed. PNR 2490182910.")
    
    assert "tools_executed" in res
    assert len(res["tools_executed"]) > 0
    assert "Tool: GateZeroSecurityAudit" in res["tools_executed"]
    assert "Tool: HierarchicalGovernanceRouter" in res["tools_executed"]
    assert "grounded_data" in res
    assert "sovereign_tier" in res["grounded_data"]
    assert "action" in res


def test_aikart_runner_execution_and_output(tmp_path, monkeypatch):
    """Validates that aikart_runner executes and produces valid JSON output with markdown."""
    test_input = {
        "complaint": "IRCTC refund delayed. PNR 2490182910. Complainant Ramesh Sharma, mobile 9876543210, email ramesh@gmail.com, living at Sector 14 Rohini Delhi 110085.",
        "language": "English"
    }
    monkeypatch.setenv("AIKART_INPUT", json.dumps(test_input))
    
    exit_code = run_aikart()
    assert exit_code == 0
    
    # Check output
    output_file = Path("/tmp/aikart_output.json")
    if not output_file.exists():
        output_file = Path("aikart_output.json")
        
    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["format"] == "markdown"
    assert "Sahayta — Autonomous GovTech Civic Action Agent" in data["response"]
    assert "Formal Administrative Petition" in data["response"]
    assert "Official Verifiable Filing Docket" in data["response"]
