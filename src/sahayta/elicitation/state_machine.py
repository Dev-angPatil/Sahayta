"""
src/sahayta/elicitation/state_machine.py
Deterministic Dynamic Elicitation State Machine:
- Strict missing mandatory field invariant: M = R \ C
- Multi-entity ingestion on every conversational turn
- Localized targeted question bank (English, Hindi Devanagari, Hinglish)
- Clean state lifecycle from UNINITIALIZED to SUBMITTED
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Union

from sahayta.schemas.portal_schemas import (
    CpgramsGrievancePayload,
    StatePdsGrievancePayload,
    DiscomGrievancePayload,
    WaterBoardGrievancePayload,
)
from sahayta.triage.classifier import extract_entities, triage_request
from sahayta.triage.language import detect_language_and_script


# Schema Mandatory Field Registries (R_S) matching model is_required() fields
SCHEMA_REQUIRED_FIELDS: Dict[str, List[str]] = {
    "GOVTECH_CPGRAMS_V1": [
        "complainant_name",
        "mobile_number",
        "email",
        "address",
        "state",
        "district",
        "pincode",
        "ministry_department",
        "grievance_category",
        "grievance_description",
    ],
    "GOVTECH_STATE_PDS_V1": [
        "complainant_name",
        "ration_card_number",
        "state",
        "district",
        "fps_shop_id_or_name",
        "grievance_category",
        "grievance_description",
    ],
    "GOVTECH_UTILITY_DISCOM_V1": [
        "consumer_account_number",
        "utility_provider",
        "meter_number",
        "district_subdivision",
        "issue_category",
        "grievance_description",
    ],
    "GOVTECH_UTILITY_WATER_V1": [
        "consumer_number",
        "water_board_name",
        "area_locality",
        "issue_category",
        "grievance_description",
    ],
}

DOMAIN_TO_SCHEMA = {
    "CPGRAMS": "GOVTECH_CPGRAMS_V1",
    "STATE_PDS": "GOVTECH_STATE_PDS_V1",
    "DISCOM_POWER": "GOVTECH_UTILITY_DISCOM_V1",
    "WATER_BOARD": "GOVTECH_UTILITY_WATER_V1",
}

DOMAIN_TO_NAME = {
    "CPGRAMS": "Centralized Public Grievance Redress and Monitoring System (CPGRAMS)",
    "STATE_PDS": "State Public Distribution System (PDS / Ration)",
    "DISCOM_POWER": "Public Utilities - DISCOM Electricity Redressal",
    "WATER_BOARD": "Public Utilities - Municipal Water Board Redressal",
}

# Localized Question Bank for Targeted Elicitation
QUESTION_BANK: Dict[str, Dict[str, str]] = {
    # CPGRAMS Fields
    "complainant_name": {
        "en": "May I know your full legal name for the official grievance record?",
        "hi": "कृपया आधिकारिक शिकायत के लिए अपना पूरा नाम बताएं।",
        "hi-Latn": "Official record ke liye kripya apna poora legal naam batayein.",
    },
    "mobile_number": {
        "en": "Please provide your 10-digit mobile number for SMS tracking updates.",
        "hi": "कृपया एसएमएस ट्रैकिंग अपडेट के लिए अपना 10 अंकों का मोबाइल नंबर प्रदान करें।",
        "hi-Latn": "SMS tracking updates ke liye apna 10-digit mobile number batayein.",
    },
    "email": {
        "en": "What is your email address to receive the official filing receipt?",
        "hi": "आधिकारिक रसीद प्राप्त करने के लिए आपका ईमेल पता क्या है?",
        "hi-Latn": "Official filing receipt paane ke liye apna email address batayein.",
    },
    "address": {
        "en": "Please share your complete residential address including house number and street.",
        "hi": "कृपया अपना पूरा आवासीय पता (मकान नंबर और सड़क सहित) दर्ज करें।",
        "hi-Latn": "Kripya apna poora residential address (makan number aur street sahit) batayein.",
    },
    "state": {
        "en": "In which State or Union Territory do you reside?",
        "hi": "आप किस राज्य या केंद्र शासित प्रदेश में रहते हैं?",
        "hi-Latn": "Aap kis State ya Union Territory mein rehte hain?",
    },
    "district": {
        "en": "Which district does this complaint pertain to?",
        "hi": "यह शिकायत किस जिले से संबंधित है?",
        "hi-Latn": "Yeh shikayat kis district se related hai?",
    },
    "pincode": {
        "en": "What is your 6-digit postal PIN code?",
        "hi": "आपका 6 अंकों का पोस्टल पिन कोड क्या है?",
        "hi-Latn": "Aapka 6-digit postal PIN code kya hai?",
    },
    "ministry_department": {
        "en": "Which Central Ministry or Department is responsible for this service (e.g., Railways, Telecom, Banking)?",
        "hi": "इस सेवा के लिए कौन सा केंद्रीय मंत्रालय या विभाग जिम्मेदार है (जैसे रेलवे, दूरसंचार, बैंक)?",
        "hi-Latn": "Is service ke liye kaunsa Central Ministry ya Department zimmedar hai (e.g., Railways, Telecom, Banking)?",
    },
    "grievance_category": {
        "en": "Could you specify the broad category of your grievance (e.g., Ticket Refund Delay, Pension Disbursal, Service Outage)?",
        "hi": "कृपया अपनी शिकायत की श्रेणी स्पष्ट करें (जैसे टिकट रिफंड, पेंशन, सेवा में बाधा)?",
        "hi-Latn": "Kripya apni shikayat ki category batayein (e.g., Ticket Refund, Pension, Service Outage)?",
    },
    "grievance_description": {
        "en": "Please describe the exact details and facts of your complaint.",
        "hi": "कृपया अपनी शिकायत का विस्तृत विवरण दर्ज करें।",
        "hi-Latn": "Kripya apni shikayat ki poori details batayein.",
    },
    
    # State PDS Fields
    "ration_card_number": {
        "en": "Could you please provide your 8 to 16 digit Ration Card Number?",
        "hi": "कृपया अपना राशन कार्ड नंबर प्रदान करें।",
        "hi-Latn": "Kripya apna Ration Card number batayein.",
    },
    "fps_shop_id_or_name": {
        "en": "What is the name or shop number of your Fair Price Shop dealer?",
        "hi": "आपके राशन डीलर का नाम या उचित मूल्य दुकान का नंबर क्या है?",
        "hi-Latn": "Aapke ration dealer ka naam ya shop ID kya hai?",
    },
    
    # DISCOM Fields
    "consumer_account_number": {
        "en": "Please share your Electricity Consumer Account (CA) or Connection Number.",
        "hi": "कृपया अपना बिजली उपभोक्ता खाता (CA) या कनेक्शन नंबर दर्ज करें।",
        "hi-Latn": "Kripya apna bijli Consumer Account (CA) ya Connection number batayein.",
    },
    "utility_provider": {
        "en": "Which electricity distribution company supplies power to your area (e.g., BESCOM, TPDDL, BSES, UPPCL)?",
        "hi": "आपके क्षेत्र में बिजली आपूर्ति करने वाली कंपनी कौन सी है (जैसे BESCOM, TPDDL, BSES, UPPCL)?",
        "hi-Latn": "Aapke area mein kaunsi bijli company supply karti hai (e.g., BESCOM, TPDDL, BSES, UPPCL)?",
    },
    "meter_number": {
        "en": "What is your physical electric meter number? (If meter is burnt or inaccessible, type 'UNKNOWN')",
        "hi": "आपका बिजली मीटर नंबर क्या है? (यदि मीटर जल गया है या दिखाई नहीं दे रहा, तो 'UNKNOWN' लिखें)",
        "hi-Latn": "Aapka electric meter number kya hai? (Agar meter jal gaya hai toh 'UNKNOWN' likhein)",
    },
    "district_subdivision": {
        "en": "Which electricity sub-division or operational zone covers your premises (e.g., Indiranagar division)?",
        "hi": "आपके परिसर का बिजली उप-मंडल (Sub-division) या संभाग कौन सा है?",
        "hi-Latn": "Aapka electricity sub-division ya operational zone kaunsa hai (e.g., Indiranagar division)?",
    },
    "issue_category": {
        "en": "What type of electrical issue are you facing (e.g., prolonged_outage, billing_error, voltage_fluctuation)?",
        "hi": "आप किस प्रकार की बिजली समस्या का सामना कर रहे हैं (जैसे लगातार बिजली कटौती, बिलिंग त्रुटि)?",
        "hi-Latn": "Aap kis tarah ki electricity issue face kar rahe hain (e.g., prolonged_outage, billing_error)?",
    },
    
    # Water Board Fields
    "consumer_number": {
        "en": "Please provide your Water Connection Number / K-Number.",
        "hi": "कृपया अपना जल कनेक्शन नंबर या K-नंबर दर्ज करें।",
        "hi-Latn": "Kripya apna Water Connection Number ya K-Number batayein.",
    },
    "water_board_name": {
        "en": "Which municipal authority manages your water supply (e.g., Delhi Jal Board, BWSSB)?",
        "hi": "आपके क्षेत्र में जलापूर्ति कौन सा जल बोर्ड करता है (जैसे दिल्ली जल बोर्ड, BWSSB)?",
        "hi-Latn": "Aapke area mein paani supply kaunsa board karta hai (e.g., Delhi Jal Board, BWSSB)?",
    },
    "area_locality": {
        "en": "Which locality, ward, or sector is facing this water issue (e.g., Ward 42 Rohini)?",
        "hi": "किस मोहल्ले, वार्ड या सेक्टर में पानी की यह समस्या आ रही है (जैसे वार्ड 42 रोहिणी)?",
        "hi-Latn": "Kis locality, ward ya sector mein yeh paani ki problem aa rahi hai (e.g., Ward 42 Rohini)?",
    },
}


class ElicitationStateMachine:
    """
    Stateful conversational automaton tracking a citizen session.
    Guarantees:
    1. Invariant M = R \ C enforced on every step.
    2. Zero arbitrary inquiries (only schema-required fields elicited).
    3. Multi-entity single-turn ingestion.
    4. State progression to READY_FOR_DRAFT / READY_FOR_REVIEW when M is empty.
    """

    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.current_step: str = "UNINITIALIZED"
        self.portal: Optional[str] = None
        self.schema_id: Optional[str] = None
        self.portal_name: Optional[str] = None
        self.language: str = "en"
        self.script: str = "latin"
        
        self.collected_fields: Dict[str, Any] = {}
        self.missing_mandatory_fields: List[str] = []
        self.last_elicited_field: Optional[str] = None
        self.raw_initial_complaint: str = ""
        
        self.draft: Optional[Any] = None
        self.draft_letter: Optional[str] = None
        self.receipt: Optional[Dict[str, Any]] = None

    def initialize_triage(
        self,
        domain: str,
        lang: str,
        initial_entities: Dict[str, Any],
        raw_description: str
    ) -> None:
        """
        Initializes state machine directly from triage classification output.
        """
        self.portal = domain
        self.schema_id = DOMAIN_TO_SCHEMA.get(domain, "GOVTECH_CPGRAMS_V1")
        self.portal_name = DOMAIN_TO_NAME.get(domain, domain)
        self.language = lang
        self.raw_initial_complaint = raw_description

        self.collected_fields = dict(initial_entities)
        if "grievance_description" not in self.collected_fields and "description" not in self.collected_fields:
            self.collected_fields["grievance_description"] = raw_description.strip()

        self.refresh_missing_fields()

    def initialize_session(self, initial_complaint: str) -> Dict[str, Any]:
        """
        Initializes session from raw citizen input message:
        - Runs triage_request (including Gate 0 check)
        - Computes initial missing fields M = R \ C
        - Sets state to ELICITING or READY_FOR_DRAFT
        """
        self.raw_initial_complaint = initial_complaint
        triage_res = triage_request(initial_complaint)

        if not triage_res["is_valid_civic_grievance"]:
            self.current_step = "TERMINATED_REJECTED"
            return triage_res

        self.initialize_triage(
            domain=triage_res["domain"],
            lang=triage_res["detected_language"],
            initial_entities=triage_res["extracted_entities"],
            raw_description=initial_complaint
        )
        return triage_res

    def refresh_missing_fields(self) -> None:
        """
        Strictly computes M = R \ C.
        If M is empty, transitions to READY_FOR_DRAFT / READY_FOR_REVIEW.
        If M is non-empty, transitions to ELICITING and selects next field.
        """
        if not self.schema_id:
            return

        required = SCHEMA_REQUIRED_FIELDS.get(self.schema_id, [])
        self.missing_mandatory_fields = [
            field for field in required
            if field not in self.collected_fields
            or self.collected_fields[field] is None
            or str(self.collected_fields[field]).strip() == ""
        ]

        if len(self.missing_mandatory_fields) == 0:
            self.current_step = "READY_FOR_DRAFT"
            self.last_elicited_field = None
        else:
            self.current_step = "ELICITING"
            self.last_elicited_field = self.missing_mandatory_fields[0]

    def ingest_citizen_reply(self, reply: Union[Dict[str, Any], str]) -> None:
        """
        Ingests citizen reply, supporting both structured dictionary of updates
        and raw natural language utterance.
        """
        if isinstance(reply, dict):
            for k, v in reply.items():
                if v is not None and str(v).strip() != "":
                    self.collected_fields[k] = v
        elif isinstance(reply, str):
            # Extract entities from utterance
            turn_entities = extract_entities(reply, self.portal or "CPGRAMS")
            for k, v in turn_entities.items():
                if v is not None and str(v).strip() != "":
                    self.collected_fields[k] = v

            # If a single field was targeted and wasn't populated by entity extractor,
            # assign clean text directly if reasonable
            if self.last_elicited_field and self.last_elicited_field not in self.collected_fields:
                cleaned = reply.strip().strip(".।")
                if self.last_elicited_field == "complainant_name" and len(cleaned) < 50:
                    self.collected_fields["complainant_name"] = cleaned.title()
                elif self.last_elicited_field == "address" and len(cleaned) >= 5:
                    self.collected_fields["address"] = cleaned
                elif self.last_elicited_field == "district" and len(cleaned) < 40:
                    self.collected_fields["district"] = cleaned.title()
                elif self.last_elicited_field == "meter_number" and len(cleaned) < 30:
                    self.collected_fields["meter_number"] = cleaned.upper()
                elif self.last_elicited_field == "ration_card_number" and re.match(r"^[A-Za-z0-9]{8,16}$", cleaned):
                    self.collected_fields["ration_card_number"] = cleaned.upper()
                elif self.last_elicited_field == "consumer_account_number" and re.match(r"^[A-Za-z0-9\-\/]{5,20}$", cleaned):
                    self.collected_fields["consumer_account_number"] = cleaned

            # Re-check language from turn
            new_lang, new_script = detect_language_and_script(reply)
            if new_lang != "en":
                self.language = new_lang
                self.script = new_script

        self.refresh_missing_fields()

    def ingest_turn(self, citizen_text: str) -> None:
        """Alias for ingest_citizen_reply with string input."""
        self.ingest_citizen_reply(citizen_text)

    def get_next_question(self) -> str:
        """
        Generates targeted, localized elicitation question for self.last_elicited_field.
        """
        if not self.last_elicited_field:
            return ""

        field_prompts = QUESTION_BANK.get(self.last_elicited_field, {})
        return field_prompts.get(
            self.language,
            field_prompts.get("en", f"Please provide your {self.last_elicited_field}.")
        )

    def generate_next_question(self) -> str:
        """Alias for get_next_question."""
        return self.get_next_question()
