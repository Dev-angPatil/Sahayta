"""
src/sahayta/agent.py
Project Sahayta GovTech AI Agent.
Coordinates Multilingual Triage, Dynamic Elicitation, Formal Administrative Drafting,
Human-in-the-Loop Confirmation, and Verifiable Form Submission.
"""

from __future__ import annotations
import uuid
from typing import Any, Dict, Optional

from sahayta.elicitation.state_machine import ElicitationStateMachine
from sahayta.elicitation.guardrails import verify_dialogue_guardrails
from sahayta.triage.fake_detector import check_gate_zero
from sahayta.drafting.letter_synthesizer import synthesize_administrative_letter
from sahayta.drafting.submission_engine import (
    submit_grievance_payload,
    evaluate_hitl_confirmation,
    HitlConfirmationRequiredError,
)


class SahaytaAgent:
    """
    Action-oriented GovTech AI Agent for Indian civic grievance redressal.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id: str = session_id or f"sess-{uuid.uuid4().hex[:8]}"
        self.state: ElicitationStateMachine = ElicitationStateMachine(session_id=self.session_id)

    def chat(self, message: str) -> Dict[str, Any]:
        """
        Processes an incoming citizen message and progresses the grievance workflow.
        """
        reasoning_trace: list = []

        # Step 1: If session not yet initialized, screen with Gate 0 and initialize
        if self.state.current_step == "UNINITIALIZED":
            reasoning_trace.append("🔍 Received new citizen complaint — initiating Gate 0 security screening")

            rejection = check_gate_zero(message)
            if rejection:
                self.state.current_step = "TERMINATED_REJECTED"
                reasoning_trace.append(f"🚫 Gate 0 REJECTED: Detected '{rejection.rejected_entity}' — {rejection.rejection_code.value}")
                rej_dict = rejection.to_dict()
                return {
                    "session_id": self.session_id,
                    "status": "REJECTED",
                    "rejection_code": rejection.rejection_code.value,
                    "is_valid_civic_grievance": False,
                    "rejected_entity": rejection.rejected_entity,
                    "flagged_entity": rejection.rejected_entity,
                    "agent_message": rejection.message,
                    "message": rejection.message,
                    "reason": rejection.reason,
                    "rejection_reason": rejection.reason,
                    "suggested_action": rejection.suggested_action,
                    "official_advice": rejection.suggested_action,
                    "rejection": rej_dict,
                    "reasoning_trace": reasoning_trace,
                }

            reasoning_trace.append("✅ Gate 0 PASSED — No fake entities or scam schemes detected")

            triage_res = self.state.initialize_session(message)
            if not triage_res.get("is_valid_civic_grievance", True):
                return triage_res

            reasoning_trace.append(f"🌐 Language Detected: {triage_res.get('detected_language', 'en')} ({triage_res.get('detected_script', 'latin')})")
            reasoning_trace.append(f"🏛️ Domain Classification: {self.state.portal} → Schema: {self.state.schema_id}")
            reasoning_trace.append(f"📋 Entities Extracted: {', '.join(self.state.collected_fields.keys()) or 'none'}")

            if self.state.missing_mandatory_fields:
                reasoning_trace.append(f"⚠️ Missing Fields ({len(self.state.missing_mandatory_fields)}): {', '.join(self.state.missing_mandatory_fields)}")
            else:
                reasoning_trace.append("✅ All mandatory fields present — transitioning to READY_FOR_DRAFT")

            # If all fields were provided in the initial message
            if self.state.current_step in ["READY_FOR_DRAFT", "READY_FOR_REVIEW"]:
                draft = synthesize_administrative_letter(
                    schema_id=self.state.schema_id,
                    fields=self.state.collected_fields,
                    lang=self.state.language,
                )
                self.state.draft = draft
                self.state.draft_letter = draft.full_letter_text
                reasoning_trace.append(f"📝 Formal administrative petition synthesized for {self.state.portal_name}")
                agent_msg = (
                    f"I have verified your grievance particulars for {self.state.portal_name}. "
                    f"A formal petition draft has been synthesized. Please review and reply 'confirm' to submit."
                )
                return {
                    "session_id": self.session_id,
                    "status": self.state.current_step,
                    "portal": self.state.portal,
                    "schema_id": self.state.schema_id,
                    "collected_fields": self.state.collected_fields,
                    "missing_fields": self.state.missing_mandatory_fields,
                    "agent_message": agent_msg,
                    "draft": draft,
                    "reasoning_trace": reasoning_trace,
                }

            # Otherwise, start elicitation
            reasoning_trace.append(f"💬 Eliciting next field: {self.state.last_elicited_field}")
            next_q = self.state.get_next_question()
            verify_dialogue_guardrails(
                next_q,
                self.state.current_step,
                target_field=self.state.last_elicited_field,
                schema_id=self.state.schema_id,
            )
            return {
                "session_id": self.session_id,
                "status": "ELICITING",
                "portal": self.state.portal,
                "schema_id": self.state.schema_id,
                "collected_fields": self.state.collected_fields,
                "missing_fields": self.state.missing_mandatory_fields,
                "agent_message": next_q,
                "reasoning_trace": reasoning_trace,
            }

        # Step 2: Handle ongoing conversation
        # Check if user is confirming submission while in ready state
        if self.state.current_step in ["READY_FOR_DRAFT", "READY_FOR_REVIEW", "DRAFT_GENERATED"]:
            if evaluate_hitl_confirmation(user_message=message):
                reasoning_trace.append("✅ HITL Confirmation received — executing submission")
                raw_payload = self.state.draft.raw_payload if self.state.draft else self.state.collected_fields
                receipt = submit_grievance_payload(
                    schema_id=self.state.schema_id,
                    payload=raw_payload,
                    citizen_confirmation=True,
                )
                self.state.current_step = "SUBMITTED"
                self.state.receipt = receipt
                reasoning_trace.append(f"📨 Grievance SUBMITTED → Tracking: {receipt['tracking_number']}")
                reasoning_trace.append(f"🔐 SHA-256 integrity hash generated: {receipt['tamper_evident_hash'][:16]}...")
                agent_msg = (
                    f"Your grievance has been successfully submitted to {self.state.portal_name}! "
                    f"Official Tracking Reference: {receipt['tracking_number']}. "
                    f"{receipt['advice_to_citizen']}"
                )
                return {
                    "session_id": self.session_id,
                    "status": "SUBMITTED",
                    "portal": self.state.portal,
                    "schema_id": self.state.schema_id,
                    "agent_message": agent_msg,
                    "receipt": receipt,
                    "reasoning_trace": reasoning_trace,
                }

        # Ingest the citizen turn
        reasoning_trace.append(f"📥 Ingesting citizen reply — extracting entities")
        self.state.ingest_turn(message)

        if self.state.current_step in ["READY_FOR_DRAFT", "READY_FOR_REVIEW"]:
            reasoning_trace.append(f"✅ All {len(self.state.collected_fields)} mandatory fields collected")
            draft = synthesize_administrative_letter(
                schema_id=self.state.schema_id,
                fields=self.state.collected_fields,
                lang=self.state.language,
            )
            self.state.draft = draft
            self.state.draft_letter = draft.full_letter_text
            reasoning_trace.append(f"📝 Administrative petition synthesized — awaiting HITL confirmation")
            agent_msg = (
                f"Thank you. All mandatory particulars have been verified. "
                f"Your formal petition draft is ready. Please review and reply 'confirm' to officially lodge this grievance."
            )
            return {
                "session_id": self.session_id,
                "status": self.state.current_step,
                "portal": self.state.portal,
                "schema_id": self.state.schema_id,
                "collected_fields": self.state.collected_fields,
                "missing_fields": self.state.missing_mandatory_fields,
                "agent_message": agent_msg,
                "draft": draft,
                "reasoning_trace": reasoning_trace,
            }

        reasoning_trace.append(f"⚠️ Still missing {len(self.state.missing_mandatory_fields)} field(s): {', '.join(self.state.missing_mandatory_fields)}")
        reasoning_trace.append(f"💬 Eliciting: {self.state.last_elicited_field}")
        next_q = self.state.get_next_question()
        verify_dialogue_guardrails(
            next_q,
            self.state.current_step,
            target_field=self.state.last_elicited_field,
            schema_id=self.state.schema_id,
        )
        return {
            "session_id": self.session_id,
            "status": "ELICITING",
            "portal": self.state.portal,
            "schema_id": self.state.schema_id,
            "collected_fields": self.state.collected_fields,
            "missing_fields": self.state.missing_mandatory_fields,
            "agent_message": next_q,
            "reasoning_trace": reasoning_trace,
        }

    def submit(self, citizen_confirmation: bool = True) -> Dict[str, Any]:
        """
        Direct submission invocation with explicit citizen confirmation.
        """
        if not citizen_confirmation:
            raise HitlConfirmationRequiredError("Explicit citizen confirmation is required for submission.")

        raw_payload = self.state.draft.raw_payload if self.state.draft else self.state.collected_fields
        receipt = submit_grievance_payload(
            schema_id=self.state.schema_id,
            payload=raw_payload,
            citizen_confirmation=True,
        )
        self.state.current_step = "SUBMITTED"
        self.state.receipt = receipt
        return receipt


def main():
    """CLI entrypoint."""
    print("Sahayta GovTech AI Agent initialized.")


if __name__ == "__main__":
    main()
