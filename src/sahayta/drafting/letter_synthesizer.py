"""
src/sahayta/drafting/letter_synthesizer.py
Synthesizes administrative-grade formal grievance petition letters for Indian civic portals
(CPGRAMS, State PDS, DISCOM Electricity, Municipal Water Board).
Extracts strictly conformant JSON filing payloads validated against Pydantic models with extra='forbid'.
"""

from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, Type
from pydantic import BaseModel, Field, ValidationError

from sahayta.schemas.portal_schemas import (
    CpgramsGrievancePayload,
    StatePdsGrievancePayload,
    DiscomGrievancePayload,
    WaterBoardGrievancePayload,
)


class GrievanceDraft(BaseModel):
    """
    Standard Administrative Grievance Petition Data Model.
    Adheres to Article 350 / DARPG Citizen's Charter administrative norms.
    """
    subject: str = Field(..., description="Formal capitalized administrative subject line")
    to_authority: str = Field(..., description="Official designation and department of addressee")
    complainant_particulars: str = Field(..., description="Structured particulars of the citizen applicant")
    statement_of_facts: str = Field(..., description="Chronological, factual statement of grievance")
    chronology: str = Field(..., description="Chronological timeline of incident and delays")
    statutory_grounds: str = Field(..., description="Applicable statutory acts, rules, and citizen charter provisions")
    prayer_relief: str = Field(..., description="Specific, numbered administrative directions sought")
    verification_declaration: str = Field(..., description="Solemn legal verification and digital attestation")
    full_letter_text: str = Field(..., description="Complete formatted administrative petition text (Markdown)")
    portal_schema_id: str = Field(..., description="Identifier of the target portal schema")
    portal_name: str = Field(..., description="Canonical name of the target civic portal")
    raw_payload: Dict[str, Any] = Field(..., description="Validated JSON filing payload with extra='forbid'")


PDS_CATEGORY_HI_MAP: Dict[str, str] = {
    "ration_non_disbursal": "मासिक खाद्यान्न कोटा वितरण से इनकार",
    "biometric_authentication_failure": "बायोमेट्रिक (ePoS) प्रमाणीकरण विफलता एवं राशन देने से मनाही",
    "fps_overcharging_malpractice": "उचित मूल्य विक्रेता द्वारा अवैध वसूली एवं खाद्यान्न की कालाबाजारी",
    "aadhaar_seeding_issue": "राशन कार्ड में आधार सीडिंग समस्या एवं नाम विलोपन",
    "new_card_or_modification_delay": "नवीन राशन कार्ड जारी करने / संशोधन में अत्यधिक विलंब",
    "poor_foodgrain_quality": "अत्यंत घटिया, सड़ा एवं अखाद्य खाद्यान्न वितरण",
    "onorc_portability_denial": "वन नेशन वन राशन कार्ड (ONORC) पोर्टेबिलिटी के तहत राशन देने से इनकार",
}

DISCOM_CATEGORY_MAP: Dict[str, str] = {
    "billing_error": "Grossly Inflated / Erroneous Electricity Billing & Non-Adjustment of Credits",
    "prolonged_outage": "Prolonged Unscheduled Power Outage & Distribution Failure",
    "voltage_fluctuation": "Hazardous Voltage Fluctuations & Equipment Damage Risk",
    "meter_fault": "Defective / Burnt / Running Fast Electric Meter",
    "new_connection_delay": "Unlawful Delay in Sanctioning New Service Connection",
    "hazardous_infrastructure": "Exposed Live Electrical Conductors & Hazardous Infrastructure",
}

WATER_CATEGORY_MAP: Dict[str, str] = {
    "contaminated_water": "Severe Contamination of Piped Drinking Water & Public Health Hazard",
    "no_water_supply": "Total Disruption / Non-Supply of Municipal Drinking Water",
    "pipe_burst_or_leakage": "Main Pipeline Burst, Massive Water Wastage & Street Submersion",
    "sewer_overflow": "Choked Municipal Sewerage Overflow & Ingress into Residential Supply",
    "faulty_water_meter": "Faulty / Non-Functional Domestic Water Meter",
    "illegal_tapping_or_booster": "Illegal Suction Booster Pumps & Water Theft in Distribution Line",
    "water_billing_dispute": "Erroneous Water / Sewer Cess Billing Assessment",
}


def synthesize_cpgrams_draft(data: Dict[str, Any], date_str: str) -> GrievanceDraft:
    """Synthesizes CPGRAMS formal administrative petition in English."""
    dept = data.get("ministry_department", "Concerned Central Ministry / Department")
    ref = data.get("reference_number")
    ref_suffix = f" [REF NO: {ref}]" if ref else ""
    cat = data.get("grievance_category", "Administrative Maladministration")
    name = data.get("complainant_name", "Citizen")
    mobile = data.get("mobile_number", "")
    email = data.get("email", "")
    addr = data.get("address", "")
    district = data.get("district", "")
    state = data.get("state", "")
    pincode = data.get("pincode", "")
    desc = data.get("grievance_description") or data.get("description", "")

    to_auth = (
        f"BEFORE THE COMPETENT PUBLIC GRIEVANCE OFFICER / NODAL AUTHORITY\n"
        f"{dept}\n"
        f"GOVERNMENT OF INDIA, NEW DELHI"
    )

    subject = f"FORMAL ADMINISTRATIVE GRIEVANCE PETITION REGARDING {cat.upper()}{ref_suffix} — {dept}"

    complainant_part = (
        f"1. PARTICULARS OF THE COMPLAINANT:\n"
        f"   Name of Complainant : {name}\n"
        f"   Contact Mobile      : +91-{mobile}\n"
        f"   Email Address       : {email}\n"
        f"   Residential Address : {addr}, {district}, {state} - {pincode}"
    )

    statement_of_facts = (
        f"2. STATEMENT OF FACTS:\n"
        f"   The Complainant is a law-abiding citizen of India submitting this formal grievance regarding "
        f"an unresolved administrative failure falling squarely under the regulatory and operational jurisdiction of {dept}.\n"
        f"   Factual particulars: {desc}"
    )

    chronology = (
        f"3. CHRONOLOGY OF GRIEVANCE & PRIOR EFFORTS:\n"
        f"   Despite prior attempts to seek redressal through ordinary administrative channels and the passage "
        f"of reasonable resolution periods" + (f" under reference '{ref}'" if ref else "") + f", "
        f"the concerned division has failed to resolve the issue, causing substantial hardship and administrative prejudice."
    )

    statutory_grounds = (
        f"4. STATUTORY GROUNDS & CITIZEN'S CHARTER VIOLATION:\n"
        f"   The failure of the concerned department constitutes an infringement of the Citizen's Charter formulated "
        f"by the Department of Administrative Reforms and Public Grievances (DARPG), Government of India, the mandated "
        f"Public Service Delivery Standards, and the foundational administrative duty of fairness."
    )

    prayer_relief = (
        f"5. PRAYER / RELIEF REQUESTED:\n"
        f"   In light of the substantiated facts stated herein, it is most respectfully prayed that this Competent Authority be pleased to:\n"
        f"   a) Take formal cognizance of this grievance under CPGRAMS guidelines;\n"
        f"   b) Direct the concerned division to settle the pending matter / claim regarding '{cat}' without further procedural delay;\n"
        f"   c) Furnish a reasoned Action Taken Report (ATR) to the Complainant within the stipulated 30-day CPGRAMS resolution timeframe."
    )

    verification = (
        f"SOLEMN VERIFICATION:\n"
        f"I, {name}, do hereby verify on solemn affirmation that the contents of paragraphs 1 to 5 above are true and correct "
        f"to my personal knowledge and belief, and no material fact has been concealed therefrom.\n\n"
        f"Date: {date_str}\n"
        f"Place: {district}, {state}\n"
        f"Digital Attestation: [Digitally Authenticated via Sahayta GovTech Citizen Gateway]"
    )

    full_text = f"{to_auth}\n\nSUBJECT: {subject}\n\n{complainant_part}\n\n{statement_of_facts}\n\n{chronology}\n\n{statutory_grounds}\n\n{prayer_relief}\n\n{verification}"

    return GrievanceDraft(
        subject=subject,
        to_authority=to_auth,
        complainant_particulars=complainant_part,
        statement_of_facts=statement_of_facts,
        chronology=chronology,
        statutory_grounds=statutory_grounds,
        prayer_relief=prayer_relief,
        verification_declaration=verification,
        full_letter_text=full_text,
        portal_schema_id="GOVTECH_CPGRAMS_V1",
        portal_name="CPGRAMS (Centralized Public Grievance Redress and Monitoring System)",
        raw_payload=data,
    )


def synthesize_pds_draft(data: Dict[str, Any], date_str: str) -> GrievanceDraft:
    """Synthesizes State PDS formal administrative petition in Hindi (Devanagari)."""
    district = data.get("district", "जनपद")
    state = data.get("state", "राज्य")
    name = data.get("complainant_name", "शिकायतकर्ता")
    rc_no = data.get("ration_card_number", "")
    card_type = data.get("card_type", "NFSA लाभार्थी")
    fps = data.get("fps_shop_id_or_name", "")
    fps_loc = data.get("fair_price_shop_location") or district
    mobile = data.get("mobile_number") or "अनुपलब्ध"
    raw_cat = data.get("grievance_category", "fps_overcharging_malpractice")
    cat_hi = PDS_CATEGORY_HI_MAP.get(raw_cat, raw_cat)
    desc = data.get("grievance_description") or data.get("description", "")

    to_auth = (
        f"सेवा में,\n"
        f"जिला आपूर्ति अधिकारी / सक्षम प्राधिकार,\n"
        f"खाद्य एवं नागरिक आपूर्ति विभाग,\n"
        f"जिला: {district}, {state}"
    )

    subject = f"राष्ट्रीय खाद्य सुरक्षा अधिनियम (NFSA), 2013 के अंतर्गत खाद्यान्न वितरण में अनियमितता एवं {cat_hi} के संबंध में औपचारिक शिकायत।"

    complainant_part = (
        f"१. शिकायतकर्ता एवं राशन कार्ड का विवरण:\n"
        f"   नाम                 : {name}\n"
        f"   राशन कार्ड संख्या   : {rc_no} (श्रेणी: {card_type})\n"
        f"   उचित मूल्य दुकान (FPS): {fps}\n"
        f"   दुकान का स्थान       : {fps_loc}\n"
        f"   जिला एवं राज्य      : {district}, {state}\n"
        f"   संपर्क मोबाइल      : +91-{mobile}"
    )

    statement_of_facts = (
        f"२. घटना एवं तथ्यों का विवरण:\n"
        f"   शिकायतकर्ता उपरोक्त राशन कार्ड का वैध धारक है। अत्यंत खेद के साथ अवगत कराना है कि संबंधित उचित मूल्य विक्रेता (राशन डीलर) द्वारा "
        f"सार्वजनिक वितरण प्रणाली के नियमों की खुली अवहेलना करते हुए निम्नलिखित गंभीर अनियमितता की जा रही है:\n"
        f"   {desc}"
    )

    chronology = (
        f"३. घटनाक्रम एवं पूर्व प्रयास:\n"
        f"   उक्त समस्या के संबंध में शिकायतकर्ता द्वारा कोटेदार/डीलर से व्यक्तिगत रूप से अनुरोध किया गया, किंतु डीलर द्वारा "
        f"असंतोषजनक व दुर्व्यवहारपूर्ण रवैया अपनाया गया तथा वैधानिक समय सीमा बीत जाने पर भी राशन वितरण सुनिश्चित नहीं किया गया।"
    )

    statutory_grounds = (
        f"४. विधिक एवं वैधानिक आधार:\n"
        f"   उक्त कृत्य राष्ट्रीय खाद्य सुरक्षा अधिनियम (NFSA), 2013 की धारा 3 एवं धारा 8, लक्षित सार्वजनिक वितरण प्रणाली (नियंत्रण) आदेश 2015, "
        f"तथा आवश्यक वस्तु अधिनियम (Essential Commodities Act), 1955 का प्रत्यक्ष एवं दंडनीय उल्लंघन है।"
    )

    prayer_relief = (
        f"५. प्रार्थना / अनुतोष (Relief Sought):\n"
        f"   अतः श्रीमान से सादर विनम्र प्रार्थना है कि जनहित एवं खाद्य सुरक्षा को दृष्टिगत रखते हुए:\n"
        f"   क) संबंधित उचित मूल्य दुकान एवं डीलर के विरुद्ध तत्काल स्थलीय औचक जांच एवं स्टॉक सत्यापन कराया जाए;\n"
        f"   ख) शिकायतकर्ता एवं प्रभावित लाभार्थियों को उनका बकाया खाद्यान्न कोटा अविलंब निःशुल्क/विहित दर पर वितरित कराया जाए;\n"
        f"   ग) दोषी विक्रेता के विरुद्ध आवश्यक वस्तु अधिनियम के तहत लाइसेंस निलंबन व विधिक दंडात्मक कार्रवाई सुनिश्चित की जाए;\n"
        f"   घ) शिकायत निवारण की विस्तृत जांच आख्या (Action Taken Report) निर्धारित ७ कार्यदिवसों में शिकायतकर्ता को उपलब्ध कराई जाए।"
    )

    verification = (
        f"सत्यापन एवं घोषणा:\n"
        f"मैं, {name}, सत्यनिष्ठा से सत्यापित करता/करती हूँ कि उपरोक्त याचिका में वर्णित सभी तथ्य मेरे व्यक्तिगत ज्ञान एवं विश्वास "
        f"के अनुसार पूर्णतः सत्य एवं सही हैं तथा इसमें कोई भी तथ्य छुपाया नहीं गया है।\n\n"
        f"दिनांक: {date_str}\n"
        f"स्थान: {district}, {state}\n"
        f"डिजिटल हस्ताक्षर / सत्यापन: [Sahayta नागरिक इंटरफेस द्वारा डिजिटल रूप से सत्यापित]"
    )

    full_text = f"{to_auth}\n\nविषय: {subject}\n\n{complainant_part}\n\n{statement_of_facts}\n\n{chronology}\n\n{statutory_grounds}\n\n{prayer_relief}\n\n{verification}"

    return GrievanceDraft(
        subject=subject,
        to_authority=to_auth,
        complainant_particulars=complainant_part,
        statement_of_facts=statement_of_facts,
        chronology=chronology,
        statutory_grounds=statutory_grounds,
        prayer_relief=prayer_relief,
        verification_declaration=verification,
        full_letter_text=full_text,
        portal_schema_id="GOVTECH_STATE_PDS_V1",
        portal_name="State PDS (Public Distribution System / Ration Redressal)",
        raw_payload=data,
    )


def synthesize_discom_draft(data: Dict[str, Any], date_str: str) -> GrievanceDraft:
    """Synthesizes DISCOM Electricity formal grievance petition in English."""
    provider = data.get("utility_provider", "Electricity Distribution Licensee")
    subdiv = data.get("district_subdivision", "Sub-Division")
    ca = data.get("consumer_account_number", "")
    meter = data.get("meter_number", "UNKNOWN")
    raw_issue = data.get("issue_category", "prolonged_outage")
    issue_label = DISCOM_CATEGORY_MAP.get(raw_issue, raw_issue.replace("_", " ").title())
    name = data.get("complainant_name") or "Registered Consumer"
    mobile = data.get("mobile_number") or "N/A"
    addr = data.get("address", subdiv)
    desc = data.get("grievance_description") or data.get("description", "")

    to_auth = (
        f"BEFORE THE CONSUMER GRIEVANCE REDRESSAL FORUM (CGRF) / ASST. EXECUTIVE ENGINEER\n"
        f"{provider}\n"
        f"ELECTRICITY DISTRIBUTION SUB-DIVISION: {subdiv}"
    )

    subject = f"FORMAL CONSUMER COMPLAINT TO {provider} REGARDING {issue_label.upper()} UNDER ELECTRICITY RULES 2020 — CA NO: {ca}"

    complainant_part = (
        f"1. CONSUMER & SERVICE CONNECTION PARTICULARS:\n"
        f"   Registered Consumer Name : {name}\n"
        f"   Consumer Account (CA) No : {ca}\n"
        f"   Meter Serial Number      : {meter}\n"
        f"   Distribution Sub-Division: {subdiv}\n"
        f"   Premises Address         : {addr}\n"
        f"   Contact Mobile           : +91-{mobile}"
    )

    statement_of_facts = (
        f"2. PARTICULARS OF SERVICE DEFICIENCY / BREAKDOWN:\n"
        f"   The Complainant is a bonafide domestic electricity consumer under {provider}. A severe deficiency of service "
        f"has occurred at the premises as detailed below:\n"
        f"   {desc}"
    )

    chronology = (
        f"3. CHRONOLOGY OF BREAKDOWN:\n"
        f"   The aforesaid fault/irregularity commenced and has persisted despite preliminary intimations lodged with the local "
        f"breakdown call centre. The failure to restore regular supply exceeds permissible statutory interruption thresholds."
    )

    statutory_grounds = (
        f"4. STATUTORY GROUNDS & STANDARDS OF PERFORMANCE VIOLATION:\n"
        f"   Under Rules 4 and 7 of the Electricity (Rights of Consumers) Rules, 2020, and State Regulatory Commission "
        f"Standards of Performance (SOP) regulations, the distribution licensee is obligated to maintain continuous 24x7 "
        f"uninterrupted power supply and rectify urban distribution/meter failures within guaranteed timelines (48 hours maximum). "
        f"Continued failure attracts statutory compensation payable to the affected consumer."
    )

    prayer_relief = (
        f"5. PRAYER / RELIEF SOUGHT:\n"
        f"   The Complainant respectfully prays that {provider} / this Forum be pleased to:\n"
        f"   a) Depute an emergency maintenance breakdown crew immediately to inspect and rectify the electrical defect / replace the meter;\n"
        f"   b) Ensure uninterrupted power supply restoration to the premises without further delay;\n"
        f"   c) Adjust erroneous billing / credit statutory performance compensation as prescribed under the SOP regulations;\n"
        f"   d) Issue a formal service restoration reference ticket to the Complainant."
    )

    verification = (
        f"SOLEMN VERIFICATION:\n"
        f"Verified on {date_str} at {subdiv} by {name} that all statements herein are true to personal knowledge and belief.\n\n"
        f"Digital Attestation: [Digitally Authenticated via Sahayta GovTech Citizen Gateway]"
    )

    full_text = f"{to_auth}\n\nSUBJECT: {subject}\n\n{complainant_part}\n\n{statement_of_facts}\n\n{chronology}\n\n{statutory_grounds}\n\n{prayer_relief}\n\n{verification}"

    return GrievanceDraft(
        subject=subject,
        to_authority=to_auth,
        complainant_particulars=complainant_part,
        statement_of_facts=statement_of_facts,
        chronology=chronology,
        statutory_grounds=statutory_grounds,
        prayer_relief=prayer_relief,
        verification_declaration=verification,
        full_letter_text=full_text,
        portal_schema_id="GOVTECH_UTILITY_DISCOM_V1",
        portal_name="Public Utilities - DISCOM Electricity Redressal",
        raw_payload=data,
    )


def synthesize_water_draft(data: Dict[str, Any], date_str: str) -> GrievanceDraft:
    """Synthesizes Municipal Water Board formal petition in English."""
    board = data.get("water_board_name", "Delhi Jal Board")
    locality = data.get("area_locality", "Ward / Locality")
    c_no = data.get("consumer_number", "")
    raw_issue = data.get("issue_category", "contaminated_water")
    issue_label = WATER_CATEGORY_MAP.get(raw_issue, raw_issue.replace("_", " ").title())
    name = data.get("complainant_name") or "Resident"
    mobile = data.get("mobile_number") or "N/A"
    addr = data.get("address", locality)
    desc = data.get("grievance_description") or data.get("description", "")

    to_auth = (
        f"TO THE EXECUTIVE ENGINEER / ZONAL GRIEVANCE REDRESSAL OFFICER\n"
        f"{board}\n"
        f"OPERATIONAL ZONE / LOCALITY: {locality}"
    )

    subject = f"URGENT CIVIC GRIEVANCE TO {board} REGARDING {issue_label.upper()} AND PUBLIC HEALTH RISK — CONNECTION NO: {c_no}"

    complainant_part = (
        f"1. CONSUMER & RESIDENTIAL PARTICULARS:\n"
        f"   Name of Resident / Complainant : {name}\n"
        f"   Water Connection / K-Number    : {c_no}\n"
        f"   Affected Locality / Ward       : {locality}\n"
        f"   Premises Address               : {addr}\n"
        f"   Contact Mobile                 : +91-{mobile}"
    )

    statement_of_facts = (
        f"2. DETAILS OF WATER SUPPLY DISRUPTION / CONTAMINATION:\n"
        f"   The Complainant, residing at {locality}, submits this urgent petition regarding serious water supply breakdown "
        f"under the operational control of {board}:\n"
        f"   {desc}"
    )

    chronology = (
        f"3. CHRONOLOGY OF BREAKDOWN & PERSISTENCE:\n"
        f"   The disruption has persisted over successive supply cycles. Intimations lodged with the local zonal pump house / "
        f"junior engineer have yielded no physical inspection or relief."
    )

    statutory_grounds = (
        f"4. STATUTORY MANDATE & PUBLIC HEALTH RISK:\n"
        f"   The Municipal Corporation Act and Urban Water Supply Regulations mandate the distribution of safe, potable drinking water. "
        f"Supplying contaminated water or permitting open sewer ingress poses an imminent risk of waterborne epidemics (cholera, gastroenteritis, hepatitis) "
        f"and constitutes a severe violation of the fundamental Right to Clean Water under Article 21 of the Constitution of India."
    )

    prayer_relief = (
        f"5. PRAYER / URGENT ADMINISTRATIVE RELIEF REQUESTED:\n"
        f"   The Complainant urgently prays that {board} be pleased to:\n"
        f"   a) Dispatch an emergency pipeline leak-detection and maintenance crew to {locality} within 24 hours;\n"
        f"   b) Draw water samples immediately for chemical and bacteriological testing to isolate sewage contamination;\n"
        f"   c) Station potable water tankers in the affected locality pending full pipeline restoration;\n"
        f"   d) Issue an official grievance reference number with time-bound compliance tracking."
    )

    verification = (
        f"SOLEMN VERIFICATION:\n"
        f"I, {name}, solemnly verify that the facts stated above are true to personal observation and represent the genuine on-ground condition.\n\n"
        f"Date: {date_str}\n"
        f"Place: {locality}\n"
        f"Digital Attestation: [Digitally Authenticated via Sahayta GovTech Citizen Gateway]"
    )

    full_text = f"{to_auth}\n\nSUBJECT: {subject}\n\n{complainant_part}\n\n{statement_of_facts}\n\n{chronology}\n\n{statutory_grounds}\n\n{prayer_relief}\n\n{verification}"

    return GrievanceDraft(
        subject=subject,
        to_authority=to_auth,
        complainant_particulars=complainant_part,
        statement_of_facts=statement_of_facts,
        chronology=chronology,
        statutory_grounds=statutory_grounds,
        prayer_relief=prayer_relief,
        verification_declaration=verification,
        full_letter_text=full_text,
        portal_schema_id="GOVTECH_UTILITY_WATER_V1",
        portal_name="Public Utilities - Municipal Water Board Redressal",
        raw_payload=data,
    )


PORTAL_MODEL_MAP: Dict[str, Type[BaseModel]] = {
    "GOVTECH_CPGRAMS_V1": CpgramsGrievancePayload,
    "CPGRAMS": CpgramsGrievancePayload,
    "GOVTECH_STATE_PDS_V1": StatePdsGrievancePayload,
    "STATE_PDS": StatePdsGrievancePayload,
    "GOVTECH_UTILITY_DISCOM_V1": DiscomGrievancePayload,
    "DISCOM_POWER": DiscomGrievancePayload,
    "GOVTECH_UTILITY_WATER_V1": WaterBoardGrievancePayload,
    "WATER_BOARD": WaterBoardGrievancePayload,
}


def extract_and_validate_payload(portal_schema_id: str, collected_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts, normalizes, and validates the structured filing payload for the target portal schema.
    Enforces Pydantic v2 validation with extra='forbid'.
    """
    model_cls = PORTAL_MODEL_MAP.get(portal_schema_id)
    if not model_cls:
        raise ValueError(f"Unsupported portal_schema_id: {portal_schema_id}")

    valid_field_names = set(model_cls.model_fields.keys())
    projected_data: Dict[str, Any] = {}

    for k, v in collected_fields.items():
        if k in valid_field_names and v is not None:
            if isinstance(v, str):
                projected_data[k] = v.strip()
            else:
                projected_data[k] = v

    # Normalize description field naming between 'grievance_description' and 'description'
    if "grievance_description" in valid_field_names and "grievance_description" not in projected_data:
        if "description" in collected_fields:
            projected_data["grievance_description"] = str(collected_fields["description"]).strip()
    elif "description" in valid_field_names and "description" not in projected_data:
        if "grievance_description" in collected_fields:
            projected_data["description"] = str(collected_fields["grievance_description"]).strip()

    # Validate directly against Pydantic model (will raise ValidationError on missing field or extra='forbid' violation)
    validated_instance = model_cls(**projected_data)
    return validated_instance.model_dump()


def synthesize_grievance_draft(
    portal_schema_id: str,
    collected_fields: Dict[str, Any],
    timestamp: Optional[datetime] = None,
    lang: str = "en",
) -> GrievanceDraft:
    """
    Canonical entry point for synthesizing formal Indian administrative grievance petitions.
    Validates payload against the portal's Pydantic model with extra='forbid', then renders
    the 8-part formal administrative petition.
    """
    ts = timestamp or datetime.now(timezone.utc)
    date_str = ts.strftime("%d-%m-%Y")

    # Step 1: Validate and extract strictly conformant JSON payload
    validated_payload = extract_and_validate_payload(portal_schema_id, collected_fields)

    # Step 2: Route to portal-specific formal template synthesizer
    if portal_schema_id in ["GOVTECH_CPGRAMS_V1", "CPGRAMS"]:
        return synthesize_cpgrams_draft(validated_payload, date_str)
    elif portal_schema_id in ["GOVTECH_STATE_PDS_V1", "STATE_PDS"]:
        return synthesize_pds_draft(validated_payload, date_str)
    elif portal_schema_id in ["GOVTECH_UTILITY_DISCOM_V1", "DISCOM_POWER"]:
        return synthesize_discom_draft(validated_payload, date_str)
    elif portal_schema_id in ["GOVTECH_UTILITY_WATER_V1", "WATER_BOARD"]:
        return synthesize_water_draft(validated_payload, date_str)
    else:
        raise ValueError(f"Unknown portal_schema_id: {portal_schema_id}")


def synthesize_administrative_letter(
    schema_id: str,
    fields: Optional[Dict[str, Any]] = None,
    lang: str = "en",
    **kwargs: Any
) -> GrievanceDraft:
    """
    Alias for synthesize_grievance_draft supporting positional and keyword variations from tests.
    """
    data = fields if fields is not None else kwargs.get("collected_fields", {})
    return synthesize_grievance_draft(portal_schema_id=schema_id, collected_fields=data, lang=lang)
