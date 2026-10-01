"""
src/sahayta/elicitation/__init__.py
Dynamic Elicitation State Machine and Anti-Hallucination Guardrails.
"""

from sahayta.elicitation.state_machine import (
    ElicitationStateMachine,
    SCHEMA_REQUIRED_FIELDS,
    QUESTION_BANK,
)
from sahayta.elicitation.guardrails import (
    GuardrailViolationError,
    scan_for_premature_tracking_ids,
    validate_elicitation_target,
    sanitize_outgoing_urls,
    verify_dialogue_guardrails,
)

__all__ = [
    "ElicitationStateMachine",
    "SCHEMA_REQUIRED_FIELDS",
    "QUESTION_BANK",
    "GuardrailViolationError",
    "scan_for_premature_tracking_ids",
    "validate_elicitation_target",
    "sanitize_outgoing_urls",
    "verify_dialogue_guardrails",
]
