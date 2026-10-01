"""
src/sahayta/elicitation/guardrails.py
Operational Anti-Hallucination Guardrails:
- Invariant 2: Zero pre-submission tracking IDs
- Invariant 3: Strict Schema Whitelist (Zero arbitrary inquiries)
- Invariant 4: Authentic Portal URL Grounding
"""

from __future__ import annotations
import re
from typing import List, Set, Optional
from sahayta.elicitation.state_machine import SCHEMA_REQUIRED_FIELDS


AUTHENTIC_GOV_URLS: Set[str] = {
    "https://pgportal.gov.in",
    "https://nfsa.gov.in",
    "https://cybercrime.gov.in",
    "https://delhijalboard.delhi.gov.in",
    "https://bwssb.karnataka.gov.in",
    "https://bescom.karnataka.gov.in",
    "https://tatapower-ddl.com",
    "https://bsesdelhi.com",
    "https://upenergy.in",
    "https://mahadiscom.in",
    "https://cgrf.gov.in",
}

BANNED_TRACKING_REGEXES: List[str] = [
    r"\b(?:CPGRAMS|PDS|DISCOM|WATER|DARPG)[\/\-](?:E\/)?(?:202\d|SIM)[\/\-]\d+\b",
    r"\b(?:MOCK|SIM|TRK|ACK|REC|REF|GRV)[\-\_\/][A-Z0-9\-\_]{4,20}\b",
    r"\b(?:registered|lodged|filed)\s+under\s+(?:complaint|tracking|reference|grievance|ticket)\s*(?:id|number|no|#)\s*[:\-]?\s*([A-Za-z0-9\-\/]+)"
]

FORBIDDEN_ARBITRARY_PATTERNS: List[str] = [
    r"\baadhaar\s+(?:otp|pin|biometric)\b",
    r"\bbank\s+(?:pin|password|cvv|mpin)\b",
    r"\bcredit\s+card\s+cvv\b",
    r"\bnetbanking\s+password\b",
    r"\bcaste\b",
    r"\breligion\b",
    r"\bproperty\s+deed\b"
]


class GuardrailViolationError(Exception):
    """Raised when an anti-hallucination operational invariant is violated."""
    pass


def scan_for_premature_tracking_ids(text: str, current_state: str) -> None:
    """
    Invariant 2 Enforcer:
    Strictly forbids minting or uttering tracking identifiers while in
    TRIAGED, ELICITING, READY_FOR_DRAFT, READY_FOR_REVIEW, or DRAFT_GENERATED states.
    """
    pre_submission_states = {
        "UNINITIALIZED", "TRIAGED", "ELICITING", "READY_FOR_DRAFT",
        "READY_FOR_REVIEW", "DRAFT_GENERATED"
    }
    if current_state in pre_submission_states:
        for pattern in BANNED_TRACKING_REGEXES:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raise GuardrailViolationError(
                    f"Invariant 2 Violation: Premature tracking ID pattern '{match.group(0)}' "
                    f"detected in assistant output while in pre-submission state '{current_state}'."
                )


def validate_elicitation_target(field_name: str, schema_id: str) -> None:
    """
    Invariant 3 Enforcer:
    Verifies that the field being elicited exists in the active schema's required fields list.
    """
    required = SCHEMA_REQUIRED_FIELDS.get(schema_id, [])
    if field_name not in required:
        raise GuardrailViolationError(
            f"Invariant 3 Violation: Attempted to elicit off-schema field '{field_name}' "
            f"not defined in required schema '{schema_id}' (Allowed: {required})."
        )


def sanitize_outgoing_urls(text: str) -> str:
    """
    Invariant 4 Enforcer:
    Inspects all HTTP/HTTPS links in outbound dialogue. Replaces unverified
    or third-party domains with canonical portal URLs.
    """
    urls = re.findall(r"https?://[^\s\)\"'>]+", text)
    for url in urls:
        clean_url = url.rstrip("/")
        is_whitelisted = any(clean_url.startswith(auth.rstrip("/")) for auth in AUTHENTIC_GOV_URLS)
        if not is_whitelisted:
            text = text.replace(url, "https://pgportal.gov.in")
    return text


def verify_dialogue_guardrails(
    text: str,
    current_state: str,
    target_field: Optional[str] = None,
    schema_id: Optional[str] = None
) -> str:
    """
    Unified dialogue guardrail interceptor.
    """
    scan_for_premature_tracking_ids(text, current_state)

    if target_field and schema_id:
        validate_elicitation_target(target_field, schema_id)

    text_lower = text.lower()
    for bad_pat in FORBIDDEN_ARBITRARY_PATTERNS:
        if re.search(bad_pat, text_lower):
            raise GuardrailViolationError(
                f"Invariant 3 Violation: Prohibited intrusive inquiry pattern '{bad_pat}' detected in dialogue."
            )

    return sanitize_outgoing_urls(text)
