"""
src/sahayta/drafting/__init__.py
Formal Administrative Petition Drafting, Submission Automation, and Receipt Verification.
"""

from sahayta.drafting.letter_synthesizer import (
    GrievanceDraft,
    synthesize_grievance_draft,
    synthesize_administrative_letter,
    extract_and_validate_payload,
)
from sahayta.drafting.submission_engine import (
    HitlConfirmationRequiredError,
    SubmissionReceipt,
    submit_grievance,
    submit_grievance_payload,
    evaluate_hitl_confirmation,
    mint_tracking_number,
    generate_tamper_evident_hash,
    verify_receipt_authenticity,
)

__all__ = [
    "GrievanceDraft",
    "synthesize_grievance_draft",
    "synthesize_administrative_letter",
    "extract_and_validate_payload",
    "HitlConfirmationRequiredError",
    "SubmissionReceipt",
    "submit_grievance",
    "submit_grievance_payload",
    "evaluate_hitl_confirmation",
    "mint_tracking_number",
    "generate_tamper_evident_hash",
    "verify_receipt_authenticity",
]
