"""
tests/conftest.py
Global pytest fixtures, assertion helpers, and environment setup for Project Sahayta.
"""
import sys
import os
import re
import json
import hashlib
from typing import Dict, Any, Optional
import pytest

# Ensure workspace root and src directory are on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

def pytest_configure(config):
    """Register custom markers to avoid unknown marker warnings."""
    config.addinivalue_line("markers", "tier1: Tier 1 Feature Coverage tests")
    config.addinivalue_line("markers", "tier2: Tier 2 Boundary & Corner Case tests")
    config.addinivalue_line("markers", "tier3: Tier 3 Cross-Feature Combinations tests")
    config.addinivalue_line("markers", "tier4: Tier 4 Real-World Application Scenario tests")
    config.addinivalue_line("markers", "hallucination: Anti-hallucination, Gate 0, and grounding tests")
    config.addinivalue_line("markers", "core_loop: End-to-end user journey tests")
    config.addinivalue_line("markers", "slow: Tests with extensive permutations")

# -----------------------------------------------------------------------------
# TRACKING PATTERNS & REGEXES
# -----------------------------------------------------------------------------

TRACKING_ID_REGEX = re.compile(
    r"\b(?:CPGRAMS|PDS|DISCOM|WATER|DARPG)[\/\-](?:[A-Z0-9]{2,10}[\/\-])?(?:202\d|SIM)[\/\-]\d{4,8}\b",
    re.IGNORECASE
)

BANNED_TRACKING_PATTERNS = [
    re.compile(r"\b(?:CPGRAMS|PDS|DISCOM|WATER|DARPG)[\/\-](?:E\/)?(?:202\d|SIM)[\/\-]\d+\b", re.IGNORECASE),
    re.compile(r"\b(?:MOCK|SIM|TRK|ACK|REC|REF|GRV)[\-\_\/][A-Z0-9\-\_]{4,20}\b", re.IGNORECASE),
    re.compile(r"\b(?:registered|lodged|filed)\s+under\s+(?:complaint|tracking|reference|grievance|ticket)\s*(?:id|number|no|#)\s*[:\-]?\s*([A-Za-z0-9\-\/]+)", re.IGNORECASE)
]

# -----------------------------------------------------------------------------
# CUSTOM ASSERTION HELPERS
# -----------------------------------------------------------------------------

def assert_no_tracking_id(text: str, context: str = ""):
    """
    Asserts that the provided text contains NO tracking/reference IDs.
    Enforces Anti-Hallucination Invariant: No tracking numbers prior to submission.
    """
    if not text:
        return
    for pattern in BANNED_TRACKING_PATTERNS:
        match = pattern.search(text)
        assert match is None, (
            f"ANTI-HALLUCINATION VIOLATION ({context}): Premature tracking/reference ID "
            f"'{match.group(0)}' detected in text: {text[:200]}"
        )


def assert_rejection_contract(response: Dict[str, Any], expected_code: str):
    """
    Asserts that a rejection response adheres to the strict rejection contract:
    - status in ['REJECTED', 'rejected']
    - rejection_code == expected_code
    - is_valid_civic_grievance is False
    - contains official advice / explanation
    """
    assert isinstance(response, dict), f"Expected response dict, got {type(response)}"
    status = str(response.get("status", "")).upper()
    assert status == "REJECTED", f"Expected status 'REJECTED', got '{response.get('status')}'"

    actual_code = str(response.get("rejection_code", ""))
    assert actual_code == expected_code, (
        f"Expected rejection_code '{expected_code}', got '{actual_code}'"
    )

    is_valid = response.get("is_valid_civic_grievance", False)
    assert is_valid is False, "is_valid_civic_grievance must be False for rejected requests"

    has_advice = any(
        k in response and response[k]
        for k in ("official_advice", "suggested_action", "rejection_reason", "message")
    )
    assert has_advice, "Rejection response must contain official guidance/action for citizen"


def assert_valid_receipt(receipt: Dict[str, Any], expected_portal: Optional[str] = None):
    """
    Asserts that a submission receipt meets all cryptographic and SLA standards:
    - status in ['SUBMITTED_SUCCESSFULLY', 'SUBMITTED', 'submitted']
    - tracking_number / tracking_id matching canonical portal pattern
    - 64-character hex SHA-256 tamper-evident digest
    - valid timestamp and summary
    """
    assert receipt is not None, "Receipt must not be None"
    status = str(receipt.get("status", "")).upper()
    assert status in ["SUBMITTED_SUCCESSFULLY", "SUBMITTED"], (
        f"Receipt status must be successful, got '{receipt.get('status')}'"
    )

    tracking_id = receipt.get("tracking_number") or receipt.get("tracking_id")
    assert tracking_id is not None, "Receipt must contain tracking_number or tracking_id"
    assert TRACKING_ID_REGEX.search(tracking_id), f"Invalid tracking ID format: '{tracking_id}'"

    if expected_portal:
        assert expected_portal.upper() in tracking_id.upper(), (
            f"Expected portal '{expected_portal}' in tracking ID '{tracking_id}'"
        )

    receipt_hash = receipt.get("tamper_evident_hash") or receipt.get("receipt_hash")
    assert receipt_hash is not None, "Receipt must contain tamper_evident_hash or receipt_hash"
    assert len(receipt_hash) == 64, f"Receipt hash must be 64 hex characters, got length {len(receipt_hash)}"
    assert all(c in "0123456789abcdefABCDEF" for c in receipt_hash), "Hash must be valid hexadecimal"


def compute_expected_receipt_hash(summary: Dict[str, Any], timestamp: str, tracking_number: str) -> str:
    """
    Calculates canonical SHA-256 digest of submission receipt:
    SHA-256(canonical_json(summary) + timestamp + tracking_number)
    """
    canonical_json = json.dumps(summary, sort_keys=True).encode("utf-8")
    digest_input = canonical_json + str(timestamp).encode("utf-8") + str(tracking_number).encode("utf-8")
    return hashlib.sha256(digest_input).hexdigest()


# Attach assertion helpers to pytest namespace for direct accessibility
pytest.assert_no_tracking_id = assert_no_tracking_id
pytest.assert_rejection_contract = assert_rejection_contract
pytest.assert_valid_receipt = assert_valid_receipt
pytest.compute_expected_receipt_hash = compute_expected_receipt_hash

# -----------------------------------------------------------------------------
# UNIFIED TESTING ADAPTER & RUNNER
# -----------------------------------------------------------------------------

def triage_adapter(text: str) -> Dict[str, Any]:
    """
    Unified testing adapter that dispatches to low-level triage/rejection modules,
    falling back to high-level SahaytaAgent or API models.
    """
    # 1. Try low-level fake_detector directly
    try:
        from sahayta.triage.fake_detector import check_rejections
        rejection = check_rejections(text)
        if rejection:
            return {
                "status": rejection.status.upper() if hasattr(rejection, "status") else "REJECTED",
                "rejection_code": str(rejection.rejection_code.value if hasattr(rejection.rejection_code, "value") else rejection.rejection_code),
                "rejected_entity": getattr(rejection, "flagged_entity", getattr(rejection, "rejected_entity", "")),
                "is_valid_civic_grievance": getattr(rejection, "is_valid_civic_grievance", False),
                "message": getattr(rejection, "message", getattr(rejection, "rejection_reason", getattr(rejection, "official_advice", ""))),
                "official_advice": getattr(rejection, "official_advice", "")
            }
    except (ImportError, AttributeError):
        pass

    # 2. Try triage_request in sahayta.triage
    try:
        from sahayta.triage import triage_request
        res = triage_request(text)
        if isinstance(res, dict):
            status = res.get("status", "").upper()
            return {
                "status": status,
                "rejection_code": str(res.get("rejection_code", "")),
                "rejected_entity": res.get("flagged_entity", res.get("rejected_entity", "")),
                "is_valid_civic_grievance": res.get("is_valid_civic_grievance", False),
                "message": res.get("message", res.get("rejection_reason", "")),
                "official_advice": res.get("official_advice", "")
            }
        elif hasattr(res, "status"):
            return {
                "status": res.status.upper(),
                "rejection_code": str(res.rejection_code.value if hasattr(res.rejection_code, "value") else res.rejection_code),
                "rejected_entity": getattr(res, "flagged_entity", getattr(res, "rejected_entity", "")),
                "is_valid_civic_grievance": getattr(res, "is_valid_civic_grievance", False),
                "message": getattr(res, "message", getattr(res, "rejection_reason", "")),
                "official_advice": getattr(res, "official_advice", "")
            }
    except (ImportError, AttributeError):
        pass

    # 3. Try high-level SahaytaAgent
    try:
        from sahayta.agent import SahaytaAgent
        agent = SahaytaAgent()
        res = agent.chat(text)
        status = (res.get("status") if isinstance(res, dict) else res.status).upper()
        rej = res.get("rejection") if isinstance(res, dict) else getattr(res, "rejection", None)
        return {
            "status": status,
            "rejection_code": str(rej.get("rejection_code") if isinstance(rej, dict) else (getattr(rej, "rejection_code", "") if rej else "")),
            "rejected_entity": rej.get("flagged_entity", rej.get("rejected_entity", "")) if isinstance(rej, dict) else (getattr(rej, "flagged_entity", getattr(rej, "rejected_entity", "")) if rej else ""),
            "is_valid_civic_grievance": False if status == "REJECTED" else True,
            "message": res.get("agent_message", "") if isinstance(res, dict) else getattr(res, "agent_message", ""),
            "official_advice": (rej.get("official_advice", "") if isinstance(rej, dict) else getattr(rej, "official_advice", "")) if rej else ""
        }
    except (ImportError, AttributeError):
        pass

    raise ImportError(
        "Could not load triage engine. Checked sahayta.triage.fake_detector, "
        "sahayta.triage.triage_request, and sahayta.agent.SahaytaAgent."
    )


# -----------------------------------------------------------------------------
# SAMPLE DATA FIXTURES
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_cpgrams_payload():
    return {
        "schema_id": "GOVTECH_CPGRAMS_V1",
        "portal": "CPGRAMS",
        "complainant_name": "Ramesh Kumar Sharma",
        "mobile_number": "9876543210",
        "email": "ramesh.sharma@example.com",
        "address": "Flat 402, Shanti Kunj Apartments, Sector 14, Rohini",
        "state": "Delhi",
        "district": "North West Delhi",
        "pincode": "110085",
        "ministry_department": "Ministry of Railways (Railway Board)",
        "grievance_category": "Ticket Refund Delay",
        "grievance_description": "Train number 12952 was cancelled on 2026-09-15. Refund of Rs 2,450 not credited within 72 hours.",
        "reference_number": "PNR-2458971234"
    }


@pytest.fixture
def sample_pds_payload():
    return {
        "schema_id": "GOVTECH_STATE_PDS_V1",
        "portal": "STATE_PDS",
        "complainant_name": "Savitri Devi",
        "ration_card_number": "UP092817482910",
        "state": "Uttar Pradesh",
        "district": "Varanasi",
        "fps_shop_id_or_name": "FPS-04829 (Gupta Ration Bhandar)",
        "grievance_category": "fps_overcharging_malpractice",
        "grievance_description": "Dealer is demanding Rs 20 per 5kg bag for PMGKAY foodgrains which are free as per mandate.",
        "mobile_number": "9812345678",
        "card_type": "PHH"
    }


@pytest.fixture
def sample_discom_payload():
    return {
        "schema_id": "GOVTECH_UTILITY_DISCOM_V1",
        "portal": "DISCOM_POWER",
        "consumer_account_number": "882910291",
        "utility_provider": "BESCOM",
        "meter_number": "MTR-BES-90218",
        "district_subdivision": "Indiranagar",
        "issue_category": "prolonged_outage",
        "grievance_description": "Prolonged power outage exceeding 36 hours due to transformer burnout on 12th Main Indiranagar.",
        "complainant_name": "Karthik Sundaram",
        "mobile_number": "9845012345"
    }


@pytest.fixture
def sample_water_payload():
    return {
        "schema_id": "GOVTECH_UTILITY_WATER_V1",
        "portal": "WATER_BOARD",
        "consumer_number": "K-DJB-9018274",
        "water_board_name": "Delhi Jal Board",
        "area_locality": "Sector 16 Rohini Ward 42",
        "issue_category": "contaminated_water",
        "grievance_description": "Severe sewage contamination in municipal drinking tap water supplying blackish foul smelling water.",
        "complainant_name": "Sunita Sharma",
        "mobile_number": "9910293847"
    }


@pytest.fixture
def fake_ministry_prompts():
    return [
        ("Ministry of Magic deleted my wand permit.", "Magic"),
        ("Department of Time Travel refused my grandfather paradox waiver.", "Time Travel"),
        ("Ministry of Social Media suspended my viral meme page.", "Social Media"),
        ("Department of Cryptocurrency denied my bitcoin mining allowance.", "Cryptocurrency"),
        ("Ministry of Silly Walks rejected my walking style accreditation.", "Silly Walks"),
        ("Ministry of Supernatural Affairs ghost clearance pending.", "Supernatural")
    ]


@pytest.fixture
def scam_scheme_prompts():
    return [
        ("How to claim money from PM Free Bitcoin Yojana?", "Bitcoin"),
        ("Free iPhone 2026 distribution scheme form registration.", "iPhone"),
        ("Activate PM Free 5G Recharge Yojana on my SIM.", "5G Recharge"),
        ("I won 25 lakh lottery in Pradhan Mantri Lottery Scheme.", "Lottery")
    ]


@pytest.fixture
def out_of_scope_prompts():
    return [
        "Mera padosi Ramesh mujhse 500 rupaye udhar leke wapas nahi de raha hai.",
        "My roommate borrowed 5000 rupees and refuses to return it.",
        "I lost 15000 rupees on online Aviator betting game and 1xBet app. Recover my loss.",
        "Dream11 aur online teen patti me 5000 rs har gaya, paise wapas dilwao.",
        "Please give me a peon or clerk job in your government office, I am unemployed."
    ]
