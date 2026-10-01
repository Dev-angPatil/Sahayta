"""
src/sahayta/triage/governance_router.py
Dynamic Hierarchical Governance & Jurisdiction Engine for Project Sahayta.
Scales across Union (Central), State, and Local (Municipal/Panchayat) tiers
without rigid hardcoded lists. Dynamically synthesizes evidentiary requirements
and Citizen's Charter SLAs.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import re

from pydantic import BaseModel, Field


class SovereignTier(str, Enum):
    UNION = "Union Government (Central)"
    STATE = "State Government"
    LOCAL = "Local Body (Municipal / Panchayat)"


class GovernanceAuthority(BaseModel):
    tier: SovereignTier = Field(..., description="Sovereign tier of administrative responsibility")
    ministry_or_department: str = Field(..., description="Responsible Ministry, Department, or Directorate")
    nodal_entity: str = Field(..., description="Operational unit, utility, board, or agency")
    competent_officer: str = Field(..., description="Designated Public Grievance Officer / Appellate authority")
    statutory_act: str = Field(..., description="Primary governing statutory legislation")
    standard_sla_days: int = Field(..., description="Citizen's Charter standard resolution window in days")
    escalation_avenue: str = Field(..., description="Appellate statutory body if SLA breached")
    schema_id: str = Field(..., description="Target evidentiary filing schema identifier")
    required_evidence_fields: List[str] = Field(..., description="Mandatory parameters required for administrative cognizance")


# Comprehensive Subject Allocation Matrix grounded in 7th Schedule & Citizen's Charters
SUBJECT_GOVERNANCE_CATALOG: List[Dict[str, Any]] = [
    {
        "patterns": [
            r"\b(?:train|railway|irctc|pnr|coach|berth|loco|station\s+master|tatkal)\b",
            r"रेलवे", r"ट्रेन", r"आईआरसीटीसी", r"पीएनआर"
        ],
        "tier": SovereignTier.UNION,
        "ministry": "Ministry of Railways (Railway Board)",
        "nodal": "Indian Railway Catering and Tourism Corporation / Zonal Railways",
        "officer": "Executive Director (Public Grievances), Railway Board",
        "act": "The Railways Act, 1989 & Citizen's Charter of Indian Railways",
        "sla_days": 30,
        "escalation": "Appellate Authority, DARPG / Railway Claims Tribunal",
        "schema_id": "GOVTECH_CPGRAMS_V1",
        "fields": ["complainant_name", "mobile_number", "email", "address", "state", "district", "pincode", "ministry_department", "grievance_category", "grievance_description"],
    },
    {
        "patterns": [
            r"\b(?:speed\s+post|india\s+post|post\s+office|dak\s*ghar|postman|postal)\b",
            r"डाकघर", r"स्पीड\s*पोस्ट", r"डाक"
        ],
        "tier": SovereignTier.UNION,
        "ministry": "Department of Posts (Ministry of Communications)",
        "nodal": "India Post / Postal Circle Office",
        "officer": "Senior Superintendent of Post Offices (SSPO)",
        "act": "The Indian Post Office Act, 1898 & Citizen's Charter of India Post",
        "sla_days": 30,
        "escalation": "Chief Postmaster General / DARPG Appellate Nodal Cell",
        "schema_id": "GOVTECH_CPGRAMS_V1",
        "fields": ["complainant_name", "mobile_number", "email", "address", "state", "district", "pincode", "ministry_department", "grievance_category", "grievance_description"],
    },
    {
        "patterns": [
            r"\b(?:epfo|provident\s+fund|uan|pf\s+withdrawal|pension|epf)\b",
            r"ईपीएफओ", r"भविष्य\s*निधि", r"पेंशन"
        ],
        "tier": SovereignTier.UNION,
        "ministry": "Ministry of Labour and Employment",
        "nodal": "Employees' Provident Fund Organisation (EPFO)",
        "officer": "Regional P.F. Commissioner (Grievance Management)",
        "act": "Employees' Provident Funds and Miscellaneous Provisions Act, 1952",
        "sla_days": 20,
        "escalation": "Central P.F. Commissioner / EPF Appellate Tribunal",
        "schema_id": "GOVTECH_CPGRAMS_V1",
        "fields": ["complainant_name", "mobile_number", "email", "address", "state", "district", "pincode", "ministry_department", "grievance_category", "grievance_description"],
    },
    {
        "patterns": [
            r"\b(?:bank|atm|sbi|pnb|loan|cibil|emi|fraud\s+transaction|banking\s+ombudsman)\b",
            r"बैंक", r"ऋण"
        ],
        "tier": SovereignTier.UNION,
        "ministry": "Department of Financial Services (Ministry of Finance)",
        "nodal": "Public Sector Banks Division / Reserve Bank of India",
        "officer": "Banking Ombudsman, Reserve Bank of India (RBI)",
        "act": "Reserve Bank - Integrated Ombudsman Scheme, 2021 & Banking Regulation Act",
        "sla_days": 30,
        "escalation": "Appellate Authority under RBI Ombudsman Scheme",
        "schema_id": "GOVTECH_CPGRAMS_V1",
        "fields": ["complainant_name", "mobile_number", "email", "address", "state", "district", "pincode", "ministry_department", "grievance_category", "grievance_description"],
    },
    {
        "patterns": [
            r"\b(?:ration|rashan|kotedar|fair\s+price\s+shop|fps|epos|nfsa|pmgkay|onorc|gehu|chawal|foodgrain)\b",
            r"राशन", r"कोटेदार", r"खाद्यान्न", r"उचित\s*मूल्य", r"गेहूं", r"चावल"
        ],
        "tier": SovereignTier.STATE,
        "ministry": "Department of Food, Civil Supplies & Consumer Affairs",
        "nodal": "District Supply Office / State PDS Directorate",
        "officer": "District Grievance Redressal Officer (DGRO) / District Supply Officer",
        "act": "National Food Security Act (NFSA), 2013, Sections 14, 15 & 16",
        "sla_days": 7,
        "escalation": "State Food Commission (NFSA Sec 16) / Appellate Authority",
        "schema_id": "GOVTECH_STATE_PDS_V1",
        "fields": ["complainant_name", "ration_card_number", "state", "district", "fps_shop_id_or_name", "grievance_category", "grievance_description"],
    },
    {
        "patterns": [
            r"\b(?:electricity|bijli|bescom|tpddl|bses|brpl|bypl|msedcl|uppcl|dhbvn|uhbvn|cesc|tangedco|transformer|power\s+cut|outage|electric\s+meter|voltage)\b",
            r"बिजली", r"विद्युत", r"पावर\s*कट", r"ट्रांसफार्मर"
        ],
        "tier": SovereignTier.STATE,
        "ministry": "State Department of Energy / State Electricity Regulatory Commission (SERC)",
        "nodal": "State Electricity Distribution Company (DISCOM)",
        "officer": "Executive Engineer (O&M) / Consumer Grievance Redressal Forum (CGRF)",
        "act": "The Electricity Act, 2003 (Section 42(5)) & Electricity (Rights of Consumers) Rules 2020",
        "sla_days": 2,
        "escalation": "Electricity Ombudsman under SERC Regulations",
        "schema_id": "GOVTECH_UTILITY_DISCOM_V1",
        "fields": ["consumer_account_number", "utility_provider", "meter_number", "district_subdivision", "issue_category", "grievance_description"],
    },
    {
        "patterns": [
            r"\b(?:water\s+supply|drinking\s+water|sewer|sewerage|delhi\s+jal\s+board|djb|bwssb|hmwssb|cmwssb|jal\s+sansthan|jal\s+nigam|pipe\s+burst|dirty\s+water|paani|pani)\b",
            r"जल\s*बोर्ड", r"पानी", r"पेयजल", r"सीवर", r"गंदा\s*पानी", r"दूषित\s*जल"
        ],
        "tier": SovereignTier.LOCAL,
        "ministry": "Urban Local Body (Municipal Corporation / City Jal Board)",
        "nodal": "Municipal Water Supply and Sewerage Board",
        "officer": "Superintending Engineer / Municipal Commissioner",
        "act": "Municipal Corporation Act & Citizen's Charter Standards for Potable Water Supply",
        "sla_days": 1,
        "escalation": "Municipal Commissioner / Mayor's Redressal Cell",
        "schema_id": "GOVTECH_UTILITY_WATER_V1",
        "fields": ["consumer_number", "water_board_name", "area_locality", "issue_category", "grievance_description"],
    },
]

# Fallback Generic Union Governance Authority
DEFAULT_UNION_AUTHORITY = GovernanceAuthority(
    tier=SovereignTier.UNION,
    ministry_or_department="Centralized Public Grievance Redress and Monitoring System (CPGRAMS)",
    nodal_entity="Department of Administrative Reforms and Public Grievances (DARPG)",
    competent_officer="Nodal Grievance Officer, Concerned Central Ministry",
    statutory_act="Constitution of India Article 350 & Citizen's Charter Guidelines",
    standard_sla_days=30,
    escalation_avenue="Appellate Authority, DARPG, Government of India",
    schema_id="GOVTECH_CPGRAMS_V1",
    required_evidence_fields=["complainant_name", "mobile_number", "email", "address", "state", "district", "pincode", "ministry_department", "grievance_category", "grievance_description"],
)


def resolve_governance_authority(complaint_text: str) -> Tuple[GovernanceAuthority, List[str]]:
    """
    Dynamically analyzes citizen complaint text to deduce:
    1. Sovereign Tier (Union / State / Local)
    2. Competent Ministry or Department
    3. Statutory Act and SLA
    4. Required Evidentiary Parameters
    Returns (GovernanceAuthority, reasoning_steps).
    """
    reasoning: List[str] = []
    text_lower = complaint_text.lower()

    reasoning.append("🏛️ Initiating Hierarchical Sovereign Jurisdiction Analysis...")

    matched_subject = None
    max_score = 0

    for subject in SUBJECT_GOVERNANCE_CATALOG:
        score = 0
        for pattern in subject["patterns"]:
            if re.search(pattern, text_lower if pattern.isascii() else complaint_text):
                score += 3
        if score > max_score:
            max_score = score
            matched_subject = subject

    if matched_subject and max_score > 0:
        tier_val = matched_subject["tier"]
        ministry_val = matched_subject["ministry"]
        nodal_val = matched_subject["nodal"]
        sla_val = matched_subject["sla_days"]
        act_val = matched_subject["act"]

        reasoning.append(f"⚖️ Resolved Sovereign Tier: {tier_val.value}")
        reasoning.append(f"🏢 Competent Authority: {ministry_val}")
        reasoning.append(f"🎯 Operational Nodal Entity: {nodal_val}")
        reasoning.append(f"📜 Governing Statute: {act_val} (Statutory SLA: {sla_val} Days)")

        auth = GovernanceAuthority(
            tier=tier_val,
            ministry_or_department=ministry_val,
            nodal_entity=nodal_val,
            competent_officer=matched_subject["officer"],
            statutory_act=act_val,
            standard_sla_days=sla_val,
            escalation_avenue=matched_subject["escalation"],
            schema_id=matched_subject["schema_id"],
            required_evidence_fields=matched_subject["fields"],
        )
        return auth, reasoning

    # Fallback to CPGRAMS Central
    reasoning.append("🌐 Broad Central Subject Detected — Routing to CPGRAMS Central Grievance Registry")
    reasoning.append(f"📜 Governing Statute: {DEFAULT_UNION_AUTHORITY.statutory_act}")
    return DEFAULT_UNION_AUTHORITY, reasoning
