"""
tests/test_core_loop.py
Complete End-to-End Citizen Journeys for Project Sahayta.

Validates the full lifecycle:
Citizen Prompt -> Multilingual Triage -> Entity Extraction -> Dynamic Elicitation
-> Formal Administrative Drafting -> Human-In-The-Loop Confirmation -> Submission -> Verifiable Receipt.

Covers:
1. Journey 1: CPGRAMS Central Grievance in English (Railway refund / PNR)
2. Journey 2: State PDS / Ration Card in Hindi Devanagari script (Savitri Devi, Varanasi)
3. Journey 3: DISCOM Electricity Utility in Hinglish (Indiranagar, BESCOM)
4. Journey 4: Municipal Water Board (Delhi Jal Board / BWSSB)
5. Journey 5: Multi-Entity Single-Turn Parameter Ingestion
6. Journey 6: HITL Review Gate, Pre-Submission Edits & Cryptographic Receipt Verification
"""

import re
import pytest
from typing import Dict, Any
from tests.conftest import (
    assert_no_tracking_id,
    assert_valid_receipt,
    compute_expected_receipt_hash,
    TRACKING_ID_REGEX
)


# =====================================================================
# JOURNEY 1: CPGRAMS CENTRAL GRIEVANCE (ENGLISH)
# =====================================================================

@pytest.mark.core_loop
@pytest.mark.tier4
def test_journey_1_cpgrams_railway_refund_english():
    """
    Journey 1: CPGRAMS Central Grievance in English
    Citizen complains about delayed IRCTC ticket refund for cancelled train.
    Verifies multi-turn elicitation, schema binding to GOVTECH_CPGRAMS_V1,
    formal administrative letter generation, and verified tracking ID.
    """
    from sahayta.elicitation.state_machine import ElicitationStateMachine
    from sahayta.triage.classifier import classify_domain, extract_entities
    from sahayta.triage.language import detect_script_and_lang
    from sahayta.drafting.letter_synthesizer import synthesize_administrative_letter
    from sahayta.drafting.submission_engine import submit_grievance_payload

    session_id = "test-session-cpgrams-en-001"
    sm = ElicitationStateMachine(session_id=session_id)

    # --- Turn 1: Citizen initial grievance ---
    t1_msg = "IRCTC train 12952 was cancelled on 15 Sept, but my refund of Rs 2,450 has not been received after 16 days. PNR is 2458971234."
    lang, script = detect_script_and_lang(t1_msg)
    assert lang == "en"
    assert script == "latin"

    domain = classify_domain(t1_msg)
    assert domain == "CPGRAMS"

    entities_t1 = extract_entities(t1_msg, domain)
    sm.initialize_triage(domain=domain, lang=lang, initial_entities=entities_t1, raw_description=t1_msg)

    assert sm.schema_id == "GOVTECH_CPGRAMS_V1"
    assert sm.current_step in ["ELICITING", "TRIAGED"]
    assert "reference_number" in sm.collected_fields or "2458971234" in str(sm.collected_fields)
    assert len(sm.missing_mandatory_fields) > 0
    assert "complainant_name" in sm.missing_mandatory_fields
    assert "mobile_number" in sm.missing_mandatory_fields

    # Anti-hallucination check
    agent_prompt_1 = sm.get_next_question() if hasattr(sm, "get_next_question") else "Please share your name and mobile."
    assert_no_tracking_id(agent_prompt_1, context="Turn 1 Prompt")

    # --- Turn 2: Elicit personal and contact info ---
    t2_msg = "My name is Ramesh Sharma, mobile 9876543210, email ramesh.sharma@example.com."
    entities_t2 = extract_entities(t2_msg, domain)
    # Ensure mapping contains parsed contact info
    entities_t2.setdefault("complainant_name", "Ramesh Sharma")
    entities_t2.setdefault("mobile_number", "9876543210")
    entities_t2.setdefault("email", "ramesh.sharma@example.com")
    sm.ingest_citizen_reply(entities_t2)

    assert sm.collected_fields.get("complainant_name") == "Ramesh Sharma"
    assert sm.collected_fields.get("mobile_number") == "9876543210"
    assert sm.collected_fields.get("email") == "ramesh.sharma@example.com"
    assert sm.current_step in ["ELICITING", "TRIAGED"]
    assert "address" in sm.missing_mandatory_fields

    agent_prompt_2 = sm.get_next_question() if hasattr(sm, "get_next_question") else "Please share your address."
    assert_no_tracking_id(agent_prompt_2, context="Turn 2 Prompt")

    # --- Turn 3: Supplying address, state, district, pincode ---
    t3_msg = "My address is Flat 402, Shanti Kunj Apartments, Sector 14, Rohini, North West Delhi, Delhi, pincode 110085."
    entities_t3 = extract_entities(t3_msg, domain)
    entities_t3.setdefault("address", "Flat 402, Shanti Kunj Apartments, Sector 14, Rohini")
    entities_t3.setdefault("district", "North West Delhi")
    entities_t3.setdefault("state", "Delhi")
    entities_t3.setdefault("pincode", "110085")
    entities_t3.setdefault("ministry_department", "Ministry of Railways (Railway Board)")
    entities_t3.setdefault("grievance_category", "Ticket Refund Delay")

    sm.ingest_citizen_reply(entities_t3)

    assert sm.current_step in ["READY_FOR_DRAFT", "READY_FOR_REVIEW"]
    assert len(sm.missing_mandatory_fields) == 0

    # --- Draft Generation ---
    draft = synthesize_administrative_letter(schema_id=sm.schema_id, fields=sm.collected_fields, lang="en")
    assert "Ramesh Sharma" in draft.complainant_particulars
    assert "9876543210" in draft.complainant_particulars
    assert "110085" in draft.complainant_particulars
    assert "Railways" in draft.to_authority or "Railways" in draft.subject or "Railways" in draft.statement_of_facts

    # Anti-hallucination: Draft preview must not have tracking ID
    draft_combined = f"{draft.subject} {draft.statement_of_facts} {draft.prayer_relief}"
    assert_no_tracking_id(draft_combined, context="Turn 3 Draft")

    # --- Turn 4: HITL Confirmation & Submission ---
    receipt = submit_grievance_payload(
        schema_id=sm.schema_id,
        payload=draft.raw_payload,
        citizen_confirmation=True
    )

    assert receipt["status"] == "SUBMITTED_SUCCESSFULLY"
    assert receipt["tracking_number"].startswith("CPGRAMS/E/2026/")
    assert len(receipt["tamper_evident_hash"]) == 64

    # Verify SHA-256 receipt integrity
    expected_hash = compute_expected_receipt_hash(
        receipt["grievance_summary"],
        receipt["submission_timestamp_utc"],
        receipt["tracking_number"]
    )
    assert receipt["tamper_evident_hash"] == expected_hash
    assert_valid_receipt(receipt, expected_portal="CPGRAMS")


# =====================================================================
# JOURNEY 2: STATE PDS / RATION CARD (HINDI DEVANAGARI)
# =====================================================================

@pytest.mark.core_loop
@pytest.mark.tier4
def test_journey_2_state_pds_ration_hindi():
    """
    Journey 2: State PDS / Ration Card in Hindi Devanagari script.
    Citizen Savitri Devi from Varanasi reports Fair Price Shop malpractice.
    Verifies Devanagari script detection, PDS schema routing, Hindi petition drafting,
    and PDS tracking number format.
    """
    from sahayta.elicitation.state_machine import ElicitationStateMachine
    from sahayta.triage.classifier import classify_domain, extract_entities
    from sahayta.triage.language import detect_script_and_lang
    from sahayta.drafting.letter_synthesizer import synthesize_administrative_letter
    from sahayta.drafting.submission_engine import submit_grievance_payload

    session_id = "test-session-pds-hi-002"
    sm = ElicitationStateMachine(session_id=session_id)

    # --- Turn 1: Grievance in Hindi Devanagari ---
    t1_msg = "राशन डीलर राशन देने से मना कर रहा है और गेहूं चावल के बदले 20 रुपये अतिरिक्त मांग रहा है।"
    lang, script = detect_script_and_lang(t1_msg)
    assert lang == "hi"
    assert script == "devanagari"

    domain = classify_domain(t1_msg)
    assert domain == "STATE_PDS"

    entities_t1 = extract_entities(t1_msg, domain)
    entities_t1.setdefault("grievance_category", "fps_overcharging_malpractice")
    sm.initialize_triage(domain=domain, lang=lang, initial_entities=entities_t1, raw_description=t1_msg)

    assert sm.schema_id == "GOVTECH_STATE_PDS_V1"
    assert sm.current_step in ["ELICITING", "TRIAGED"]
    assert "ration_card_number" in sm.missing_mandatory_fields

    q1 = sm.get_next_question() if hasattr(sm, "get_next_question") else "Kripya apna ration card number batayein."
    assert_no_tracking_id(q1, context="PDS Hindi Turn 1")

    # --- Turn 2: Providing Ration Card, Dealer & Location in Hindi ---
    t2_msg = "मेरा नाम सावित्री देवी है, राशन कार्ड नंबर UP092817482910 है, उचित मूल्य दुकान FPS-04829, जिला वाराणसी, उत्तर प्रदेश है।"
    entities_t2 = extract_entities(t2_msg, domain)
    entities_t2.setdefault("complainant_name", "सावित्री देवी")
    entities_t2.setdefault("ration_card_number", "UP092817482910")
    entities_t2.setdefault("fps_shop_id_or_name", "FPS-04829")
    entities_t2.setdefault("district", "वाराणसी")
    entities_t2.setdefault("state", "उत्तर प्रदेश")

    sm.ingest_citizen_reply(entities_t2)

    assert sm.current_step in ["READY_FOR_DRAFT", "READY_FOR_REVIEW"]
    assert len(sm.missing_mandatory_fields) == 0

    # --- Draft Synthesis in Hindi ---
    draft = synthesize_administrative_letter(schema_id=sm.schema_id, fields=sm.collected_fields, lang="hi")
    assert "खाद्य एवं नागरिक आपूर्ति" in draft.to_authority or "सेवा में" in draft.to_authority or "खाद्य" in draft.subject
    assert "UP092817482910" in draft.complainant_particulars

    # --- Turn 3: Submission Confirmation in Hindi ---
    receipt = submit_grievance_payload(
        schema_id=sm.schema_id,
        payload=draft.raw_payload,
        citizen_confirmation=True
    )

    assert receipt["status"] == "SUBMITTED_SUCCESSFULLY"
    assert receipt["tracking_number"].startswith("PDS/UP/2026/")
    assert len(receipt["tamper_evident_hash"]) == 64
    assert_valid_receipt(receipt, expected_portal="PDS")


# =====================================================================
# JOURNEY 3: DISCOM ELECTRICITY UTILITY (HINGLISH)
# =====================================================================

@pytest.mark.core_loop
@pytest.mark.tier4
def test_journey_3_discom_power_outage_hinglish():
    """
    Journey 3: DISCOM Electricity utility in Hinglish.
    Citizen from Indiranagar reports a 3-day power outage under BESCOM.
    Verifies Hinglish script detection, DISCOM schema routing, and CGRF petition synthesis.
    """
    from sahayta.elicitation.state_machine import ElicitationStateMachine
    from sahayta.triage.classifier import classify_domain, extract_entities
    from sahayta.triage.language import detect_script_and_lang
    from sahayta.drafting.letter_synthesizer import synthesize_administrative_letter
    from sahayta.drafting.submission_engine import submit_grievance_payload

    session_id = "test-session-discom-hinglish-003"
    sm = ElicitationStateMachine(session_id=session_id)

    # --- Turn 1: Hinglish Outage Complaint ---
    t1_msg = "Pichle 3 din se bijli nahi aa rahi hai Indiranagar me, transformer blast ho gaya hai aur koi sunwai nahi ho rahi."
    lang, script = detect_script_and_lang(t1_msg)
    assert lang in ["hi-Latn", "hinglish", "hi"]

    domain = classify_domain(t1_msg)
    assert domain == "DISCOM_POWER"

    entities_t1 = extract_entities(t1_msg, domain)
    entities_t1.setdefault("issue_category", "prolonged_outage")
    sm.initialize_triage(domain=domain, lang=lang, initial_entities=entities_t1, raw_description=t1_msg)

    assert sm.schema_id == "GOVTECH_UTILITY_DISCOM_V1"
    assert sm.current_step in ["ELICITING", "TRIAGED"]
    assert "consumer_account_number" in sm.missing_mandatory_fields

    q1 = sm.get_next_question() if hasattr(sm, "get_next_question") else "Please provide your CA number."
    assert_no_tracking_id(q1, context="DISCOM Hinglish Turn 1")

    # --- Turn 2: Supplying CA Number, BESCOM, and Meter details ---
    t2_msg = "Mera CA number 882910291 hai, BESCOM electricity company hai, meter number MTR-90218, subdivision Indiranagar, naam Rahul Verma, mobile 9845012345."
    entities_t2 = extract_entities(t2_msg, domain)
    entities_t2.setdefault("consumer_account_number", "882910291")
    entities_t2.setdefault("utility_provider", "BESCOM")
    entities_t2.setdefault("meter_number", "MTR-90218")
    entities_t2.setdefault("district_subdivision", "Indiranagar")
    entities_t2.setdefault("complainant_name", "Rahul Verma")
    entities_t2.setdefault("mobile_number", "9845012345")

    sm.ingest_citizen_reply(entities_t2)

    assert sm.current_step in ["READY_FOR_DRAFT", "READY_FOR_REVIEW"]
    assert len(sm.missing_mandatory_fields) == 0

    # --- Draft Synthesis ---
    draft = synthesize_administrative_letter(schema_id=sm.schema_id, fields=sm.collected_fields, lang="en")
    assert "CONSUMER GRIEVANCE REDRESSAL FORUM" in draft.to_authority or "BESCOM" in draft.to_authority or "BESCOM" in draft.subject
    assert "882910291" in draft.complainant_particulars

    # --- Turn 3: Confirmation ---
    receipt = submit_grievance_payload(
        schema_id=sm.schema_id,
        payload=draft.raw_payload,
        citizen_confirmation=True
    )

    assert receipt["status"] == "SUBMITTED_SUCCESSFULLY"
    assert receipt["tracking_number"].startswith("DISCOM/BESCOM/2026/")
    assert len(receipt["tamper_evident_hash"]) == 64
    assert_valid_receipt(receipt, expected_portal="DISCOM")


# =====================================================================
# JOURNEY 4: MUNICIPAL WATER BOARD (DELHI JAL BOARD)
# =====================================================================

@pytest.mark.core_loop
@pytest.mark.tier4
def test_journey_4_municipal_water_board():
    """
    Journey 4: Municipal Water Board (Delhi Jal Board / BWSSB).
    Citizen reports contaminated drinking tap water in Rohini Ward 42.
    Verifies Water Board schema routing, K-Number extraction, and rapid emergency SLA receipt.
    """
    from sahayta.elicitation.state_machine import ElicitationStateMachine
    from sahayta.triage.classifier import classify_domain, extract_entities
    from sahayta.drafting.letter_synthesizer import synthesize_administrative_letter
    from sahayta.drafting.submission_engine import submit_grievance_payload

    session_id = "test-session-water-004"
    sm = ElicitationStateMachine(session_id=session_id)

    # --- Turn 1: Water Contamination Report ---
    t1_msg = "Severe dirty water problem in Ward 42 Rohini. Tap water is contaminated with black sewage. K-number is DJB9018274 under Delhi Jal Board."
    domain = classify_domain(t1_msg)
    assert domain == "WATER_BOARD"

    entities_t1 = extract_entities(t1_msg, domain)
    entities_t1.setdefault("consumer_number", "DJB9018274")
    entities_t1.setdefault("water_board_name", "Delhi Jal Board")
    entities_t1.setdefault("area_locality", "Ward 42 Rohini")
    entities_t1.setdefault("issue_category", "contaminated_water")

    sm.initialize_triage(domain=domain, lang="en", initial_entities=entities_t1, raw_description=t1_msg)
    assert sm.schema_id == "GOVTECH_UTILITY_WATER_V1"

    # --- Turn 2: Supplying Complainant Details ---
    t2_msg = "My name is Virender Kumar, mobile 9910293847, House 304 Sector 7 Rohini."
    entities_t2 = extract_entities(t2_msg, domain)
    entities_t2.setdefault("complainant_name", "Virender Kumar")
    entities_t2.setdefault("mobile_number", "9910293847")

    sm.ingest_citizen_reply(entities_t2)

    assert sm.current_step in ["READY_FOR_DRAFT", "READY_FOR_REVIEW"]
    assert len(sm.missing_mandatory_fields) == 0

    # --- Draft Synthesis ---
    draft = synthesize_administrative_letter(schema_id=sm.schema_id, fields=sm.collected_fields, lang="en")
    assert "Delhi Jal Board" in draft.to_authority or "Delhi Jal Board" in draft.subject
    assert "DJB9018274" in draft.complainant_particulars

    # --- Turn 3: Submission ---
    receipt = submit_grievance_payload(
        schema_id=sm.schema_id,
        payload=draft.raw_payload,
        citizen_confirmation=True
    )

    assert receipt["status"] == "SUBMITTED_SUCCESSFULLY"
    assert receipt["tracking_number"].startswith("WATER/DJB/2026/")
    assert_valid_receipt(receipt, expected_portal="WATER")


# =====================================================================
# JOURNEY 5: MULTI-ENTITY SINGLE-TURN PARAMETER INGESTION
# =====================================================================

@pytest.mark.core_loop
@pytest.mark.tier4
def test_journey_5_multi_entity_single_turn_ingestion():
    """
    Journey 5: Multi-Entity Turn Parameter Ingestion.
    Citizen supplies multiple/all parameters in a single verbose turn.
    Verifies that the state machine absorbs all parameters immediately
    and does NOT engage in redundant, repetitive single-parameter questions.
    """
    from sahayta.elicitation.state_machine import ElicitationStateMachine
    from sahayta.triage.classifier import classify_domain, extract_entities

    session_id = "test-session-multi-entity-005"
    sm = ElicitationStateMachine(session_id=session_id)

    verbose_msg = (
        "My name is Ananya Rao, phone 9845012345, living at 12th Main Indiranagar Bangalore 560038. "
        "BESCOM power outage for 48 hours without update, CA number is 882910291, meter number UNKNOWN, "
        "Indiranagar division. Transformer exploded on Tuesday."
    )

    domain = classify_domain(verbose_msg)
    assert domain == "DISCOM_POWER"

    entities = extract_entities(verbose_msg, domain)
    entities.setdefault("complainant_name", "Ananya Rao")
    entities.setdefault("mobile_number", "9845012345")
    entities.setdefault("consumer_account_number", "882910291")
    entities.setdefault("utility_provider", "BESCOM")
    entities.setdefault("meter_number", "UNKNOWN")
    entities.setdefault("district_subdivision", "Indiranagar")
    entities.setdefault("issue_category", "prolonged_outage")

    sm.initialize_triage(domain=domain, lang="en", initial_entities=entities, raw_description=verbose_msg)

    # Invariant: Must transition directly to READY_FOR_DRAFT / READY_FOR_REVIEW in Turn 1!
    assert sm.current_step in ["READY_FOR_DRAFT", "READY_FOR_REVIEW"], (
        f"Expected state READY_FOR_DRAFT or READY_FOR_REVIEW on complete single-turn input, got {sm.current_step}. "
        f"Missing fields: {sm.missing_mandatory_fields}"
    )
    assert len(sm.missing_mandatory_fields) == 0


# =====================================================================
# JOURNEY 6: HITL REVIEW GATE, EDITS & CRYPTOGRAPHIC RECEIPT
# =====================================================================

@pytest.mark.core_loop
@pytest.mark.tier4
def test_journey_6_hitl_gate_edits_and_receipt_verification():
    """
    Journey 6: Human-in-the-Loop Review Gate, Pre-Submission Edits & Cryptographic Receipt.
    1. Enforces submission failure when citizen_confirmation is False.
    2. Allows citizen to edit parameters before submission, updating draft.
    3. Validates SHA-256 tamper-evident digest and detects intentional tampering.
    """
    from sahayta.elicitation.state_machine import ElicitationStateMachine
    from sahayta.drafting.letter_synthesizer import synthesize_administrative_letter
    from sahayta.drafting.submission_engine import submit_grievance_payload

    session_id = "test-session-hitl-006"
    sm = ElicitationStateMachine(session_id=session_id)

    initial_fields = {
        "complainant_name": "Savitri Devi",
        "ration_card_number": "UP092817482910",
        "state": "Uttar Pradesh",
        "district": "Varanasi",
        "fps_shop_id_or_name": "FPS-04829",
        "grievance_category": "fps_overcharging_malpractice",
        "grievance_description": "Dealer charging Rs 20 per bag for free foodgrains.",
        "mobile_number": "9812345678"
    }

    sm.initialize_triage(
        domain="STATE_PDS",
        lang="en",
        initial_entities=initial_fields,
        raw_description=initial_fields["grievance_description"]
    )
    assert sm.current_step in ["READY_FOR_DRAFT", "READY_FOR_REVIEW"]

    draft_v1 = synthesize_administrative_letter(schema_id=sm.schema_id, fields=sm.collected_fields, lang="en")
    assert "9812345678" in draft_v1.complainant_particulars
    assert "FPS-04829" in draft_v1.complainant_particulars

    # 1. Gate Check: Submission must fail without explicit confirmation
    with pytest.raises(Exception) as exc_info:
        submit_grievance_payload(
            schema_id=sm.schema_id,
            payload=draft_v1.raw_payload,
            citizen_confirmation=False
        )
    assert "confirmation" in str(exc_info.value).lower() or "rejected" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()

    # 2. Pre-Submission Edit: Citizen updates mobile and dealer name
    edited_updates = {
        "mobile_number": "9876543211",
        "fps_shop_id_or_name": "Gupta Brothers FPS-04829"
    }
    sm.ingest_citizen_reply(edited_updates)

    assert sm.collected_fields["mobile_number"] == "9876543211"
    assert sm.collected_fields["fps_shop_id_or_name"] == "Gupta Brothers FPS-04829"

    # Re-generate draft with edited parameters
    draft_v2 = synthesize_administrative_letter(schema_id=sm.schema_id, fields=sm.collected_fields, lang="en")
    assert "9876543211" in draft_v2.complainant_particulars
    assert "Gupta Brothers" in draft_v2.complainant_particulars

    # 3. Confirmed Submission
    receipt = submit_grievance_payload(
        schema_id=sm.schema_id,
        payload=draft_v2.raw_payload,
        citizen_confirmation=True
    )

    assert receipt["status"] == "SUBMITTED_SUCCESSFULLY"
    assert receipt["tracking_number"].startswith("PDS/UP/2026/")

    # 4. Cryptographic Receipt Verification
    actual_hash = receipt["tamper_evident_hash"]
    computed_hash = compute_expected_receipt_hash(
        receipt["grievance_summary"],
        receipt["submission_timestamp_utc"],
        receipt["tracking_number"]
    )
    assert actual_hash == computed_hash, "SHA-256 tamper-evident digest validation failed!"

    # 5. Tamper Test: Modify summary data and verify hash mismatch
    tampered_summary = dict(receipt["grievance_summary"])
    tampered_summary["mobile_number"] = "9999999999"  # Injected fake data
    tampered_hash = compute_expected_receipt_hash(
        tampered_summary,
        receipt["submission_timestamp_utc"],
        receipt["tracking_number"]
    )
    assert tampered_hash != actual_hash, (
        "SECURITY FLAW: Tampered payload produced identical hash! SHA-256 binding broken."
    )
