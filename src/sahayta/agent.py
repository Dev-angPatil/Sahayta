"""
src/sahayta/agent.py
Project Sahayta GovTech AI Agent.
Coordinates Multilingual Triage, Dynamic Elicitation, Gemini 2.5 Flash LLM Reasoning,
Formal Administrative Drafting (Article 350), Human-in-the-Loop Confirmation,
and Verifiable Form Submission.
"""

from __future__ import annotations
import uuid
import re
from typing import Any, Dict, Optional, List

from sahayta.elicitation.state_machine import ElicitationStateMachine
from sahayta.elicitation.guardrails import verify_dialogue_guardrails
from sahayta.triage.fake_detector import check_gate_zero
from sahayta.triage.governance_router import resolve_governance_authority, GovernanceAuthority, SovereignTier
from sahayta.triage.classifier import classify_domain, extract_entities
from sahayta.triage.language import detect_script_and_lang
from sahayta.drafting.letter_synthesizer import synthesize_administrative_letter
from sahayta.drafting.submission_engine import (
    submit_grievance_payload,
    evaluate_hitl_confirmation,
    HitlConfirmationRequiredError,
)
from sahayta.llm.gemini_client import get_gemini_client, GeminiClient


class SahaytaAgent:
    """
    Action-oriented GovTech AI Agent for Indian civic grievance redressal.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id: str = session_id or f"sess-{uuid.uuid4().hex[:8]}"
        self.state: ElicitationStateMachine = ElicitationStateMachine(session_id=self.session_id)
        self.governance_authority: Optional[GovernanceAuthority] = None
        self.gemini: GeminiClient = get_gemini_client()
        self.has_active_grievance: bool = False

    def get_grounded_data_summary(self) -> Dict[str, Any]:
        """Returns structured governance and evidentiary metadata."""
        if not self.governance_authority:
            portal_name = self.state.portal_name or "CPGRAMS Central Grievance Registry"
            tier = "Union Government (Central)"
            if self.state.portal == "STATE_PDS":
                tier = "State Government"
            elif self.state.portal in ["DISCOM_POWER", "WATER_BOARD"]:
                tier = "Local Body (Municipal / Utility)"

            return {
                "sovereign_tier": tier,
                "ministry_or_department": portal_name,
                "nodal_entity": "Department of Administrative Reforms and Public Grievances (DARPG)",
                "statutory_act": "Constitution of India Article 350 & Citizen's Charter",
                "standard_sla_days": 30,
                "escalation_avenue": "Appellate Authority, DARPG, Government of India",
                "schema_id": self.state.schema_id or "GOVTECH_CPGRAMS_V1",
            }
        return {
            "sovereign_tier": self.governance_authority.tier.value,
            "ministry_or_department": self.governance_authority.ministry_or_department,
            "nodal_entity": self.governance_authority.nodal_entity,
            "statutory_act": self.governance_authority.statutory_act,
            "standard_sla_days": self.governance_authority.standard_sla_days,
            "escalation_avenue": self.governance_authority.escalation_avenue,
            "schema_id": self.governance_authority.schema_id,
        }

    def chat(self, message: str) -> Dict[str, Any]:
        """
        Processes an incoming citizen message and progresses the grievance workflow.
        Integrates Gemini 2.5 Flash for natural conversations, explanations, and extraction.
        """
        reasoning_trace: List[str] = []
        tools_executed: List[str] = []
        cleaned_msg = message.strip()

        # Step 1: Gate 0 Security & Anti-Hallucination screening
        reasoning_trace.append("🔍 Initiating Gate 0 security & anti-hallucination screening")
        tools_executed.append("Tool: GateZeroSecurityAudit")

        rejection = check_gate_zero(cleaned_msg)
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
                "tools_executed": tools_executed,
                "grounded_data": {},
                "action": "TERMINATE_REJECTED",
            }

        reasoning_trace.append("✅ Gate 0 PASSED — Verified legitimate civic domain")

        # Step 2: Handle HITL Confirmation if draft is ready
        if self.state.current_step in ["READY_FOR_DRAFT", "READY_FOR_REVIEW", "DRAFT_GENERATED"]:
            if evaluate_hitl_confirmation(user_message=cleaned_msg):
                tools_executed.append("Tool: HumanInTheLoopGate")
                tools_executed.append("Tool: CryptographicNotary")
                tools_executed.append("Tool: StatutorySLAWatchdog")
                reasoning_trace.append("✅ Explicit citizen confirmation received — executing official submission")
                raw_payload = self.state.draft.raw_payload if self.state.draft else self.state.collected_fields
                receipt = submit_grievance_payload(
                    schema_id=self.state.schema_id,
                    payload=raw_payload,
                    citizen_confirmation=True,
                )
                self.state.current_step = "SUBMITTED"
                self.state.receipt = receipt
                reasoning_trace.append(f"📨 Grievance SUBMITTED → Official Tracking ID: {receipt['tracking_number']}")
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
                    "message": agent_msg,
                    "receipt": receipt,
                    "reasoning_trace": reasoning_trace,
                    "tools_executed": tools_executed,
                    "grounded_data": self.get_grounded_data_summary(),
                    "action": "LODGE_FILING_COMPLETE",
                }

        # Step 3: Run Gemini LLM analysis for intent & contextual reasoning
        llm_analysis: Dict[str, Any] = {}
        if self.gemini.is_available():
            tools_executed.append("Tool: GeminiGovTechReasoner")
            llm_analysis = self.gemini.analyze_turn(
                message=cleaned_msg,
                current_domain=self.state.portal,
                collected_fields=self.state.collected_fields,
                missing_fields=self.state.missing_mandatory_fields,
            )
            if llm_analysis.get("reasoning_summary"):
                reasoning_trace.append(f"🧠 LLM Reasoning: {llm_analysis['reasoning_summary']}")

        llm_intent = llm_analysis.get("intent", "")
        llm_entities = llm_analysis.get("extracted_entities", {})

        # Step 4: Handle Conversational Greetings, Introductions, and General Inquiries
        is_greeting = cleaned_msg.lower() in [
            "hi", "hello", "hey", "namaste", "namaskar", "help", "who are you",
            "what can you do", "kaise ho", "kya kar sakte ho", "help me"
        ] or (
            not self.has_active_grievance
            and self.state.current_step == "UNINITIALIZED"
            and llm_intent == "GREETING_OR_INQUIRY"
        )

        if is_greeting and not self.has_active_grievance:
            reasoning_trace.append("💬 Conversational intake: citizen greeting or inquiry addressed")
            reply = llm_analysis.get("conversational_reply") or (
                "Namaste! I am **Sahayta (सहायता)**, an autonomous GovTech Action Agent for Bharat.\n\n"
                "I assist citizens by translating colloquial grievances into formal administrative petitions "
                "under **Article 350 of the Constitution of India** and automatically filling the appropriate portal sandbox:\n"
                "• **Central (CPGRAMS):** Railways (IRCTC/PNR), Banking, Telecom, India Post, EPFO, Passports\n"
                "• **State (NFSA / PDS):** Ration Card, Fair Price Shop dealer overcharging, biometric errors\n"
                "• **Public Utilities:** Electricity DISCOM (power cuts, faulty meter, billing) & Municipal Water (dirty water, pipeline leakage)\n\n"
                "Speak or type your complaint (e.g. *'Ration dealer in Varanasi overcharging'* or *'Train 12952 ticket refund delayed'*), "
                "and I will begin drafting your petition immediately."
            )
            return {
                "session_id": self.session_id,
                "status": "CONVERSATIONAL",
                "portal": "Awaiting Intake",
                "schema_id": "GOVTECH_CORE_V1",
                "collected_fields": self.state.collected_fields,
                "missing_fields": [],
                "agent_message": reply,
                "message": reply,
                "reasoning_trace": reasoning_trace,
                "tools_executed": tools_executed,
                "grounded_data": self.get_grounded_data_summary(),
                "action": "AWAITING_GRIEVANCE_INPUT",
            }

        # Step 5: Mark active grievance and resolve authority
        self.has_active_grievance = True

        if self.state.current_step == "UNINITIALIZED":
            # Dynamic Sovereign Governance Routing
            tools_executed.append("Tool: HierarchicalGovernanceRouter")
            tools_executed.append("Tool: EvidentiarySchemaSynthesizer")

            gov_auth, gov_reasoning = resolve_governance_authority(cleaned_msg)
            self.governance_authority = gov_auth
            reasoning_trace.extend(gov_reasoning)

            # Determine domain & language
            domain = llm_analysis.get("detected_domain") or classify_domain(cleaned_msg)
            lang, script = detect_script_and_lang(cleaned_msg)

            # Extract entities using both regex and LLM
            tools_executed.append("Tool: VernacularEntityExtractor")
            regex_entities = extract_entities(cleaned_msg, domain)
            merged_entities = dict(llm_entities)
            merged_entities.update(regex_entities)  # Regex guarantees strict formatting

            # Initialize state machine
            self.state.initialize_triage(
                domain=domain,
                lang=lang,
                initial_entities=merged_entities,
                raw_description=cleaned_msg,
            )

            reasoning_trace.append(f"🌐 Language Detected: {lang} ({script})")
            reasoning_trace.append(f"🏛️ Resolved Authority: {self.governance_authority.ministry_or_department} (Tier: {self.governance_authority.tier.value})")
            reasoning_trace.append(f"📋 Entities Extracted: {', '.join(self.state.collected_fields.keys()) or 'none'}")

        else:
            # Multi-turn conversation: ingest citizen reply
            tools_executed.append("Tool: VernacularEntityExtractor")
            regex_entities = extract_entities(cleaned_msg, self.state.portal or "CPGRAMS")
            merged_entities = dict(llm_entities)
            merged_entities.update(regex_entities)

            # If a single field was targeted and extracted is empty, assign directly
            if not merged_entities and self.state.last_elicited_field:
                merged_entities[self.state.last_elicited_field] = cleaned_msg

            self.state.ingest_citizen_reply(merged_entities)
            reasoning_trace.append(f"📥 Updated parameters: {', '.join(merged_entities.keys()) or 'turn ingested'}")

        # Check missing mandatory fields
        if self.state.missing_mandatory_fields:
            reasoning_trace.append(f"⚠️ Missing Evidentiary Fields ({len(self.state.missing_mandatory_fields)}): {', '.join(self.state.missing_mandatory_fields)}")
        else:
            reasoning_trace.append("✅ All mandatory evidentiary fields verified — transitioning to READY_FOR_DRAFT")

        # Step 6: If all parameters are complete, synthesize Article 350 petition
        if self.state.current_step in ["READY_FOR_DRAFT", "READY_FOR_REVIEW"]:
            tools_executed.append("Tool: Article350PetitionSynthesizer")
            draft = synthesize_administrative_letter(
                schema_id=self.state.schema_id,
                fields=self.state.collected_fields,
                lang=self.state.language,
            )
            self.state.draft = draft
            self.state.draft_letter = draft.full_letter_text
            reasoning_trace.append(f"📝 Formal administrative petition synthesized for {self.state.portal_name}")
            agent_msg = (
                f"I have verified all required particulars for {self.state.portal_name}. "
                f"A formal petition draft has been synthesized under Article 350 of the Constitution of India. "
                f"Please review the live form and draft on your right screen, and reply 'confirm' (or click the button) to officially lodge this grievance."
            )
            return {
                "session_id": self.session_id,
                "status": self.state.current_step,
                "portal": self.state.portal,
                "schema_id": self.state.schema_id,
                "collected_fields": self.state.collected_fields,
                "missing_fields": self.state.missing_mandatory_fields,
                "agent_message": agent_msg,
                "message": agent_msg,
                "draft": draft,
                "reasoning_trace": reasoning_trace,
                "tools_executed": tools_executed,
                "grounded_data": self.get_grounded_data_summary(),
                "action": "AWAITING_HITL_CONFIRMATION",
            }

        # Step 7: Solicit the next missing evidentiary parameter
        tools_executed.append("Tool: AdaptiveElicitationEngine")
        reasoning_trace.append(f"💬 Eliciting next field: {self.state.last_elicited_field}")
        next_q = self.state.get_next_question()

        # If LLM generated a friendly reply asking for this info, optionally combine or use standard question
        display_q = next_q
        if llm_analysis.get("conversational_reply") and len(self.state.collected_fields) > 1:
            display_q = f"{llm_analysis['conversational_reply']}\n\n{next_q}"

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
            "agent_message": display_q,
            "message": display_q,
            "reasoning_trace": reasoning_trace,
            "tools_executed": tools_executed,
            "grounded_data": self.get_grounded_data_summary(),
            "action": "TARGETED_ELICITATION",
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
    """CLI test entrypoint."""
    agent = SahaytaAgent()
    print("Sahayta GovTech AI Agent initialized with Gemini 2.5 Flash.")
    res = agent.chat("Namaste")
    print("Response:", res.get("agent_message"))


if __name__ == "__main__":
    main()
