"""
src/sahayta/triage/fake_detector.py
Gate 0 Rejection Engine: Detects and rejects fictional ministries, fake departments,
fraudulent schemes, and out-of-scope commercial/personal disputes.
"""

from __future__ import annotations
import re
from typing import Optional
from sahayta.schemas.rejection import RejectionCode, TriageRejectionResponse


# Fictional, pop-culture, and satirical government bodies
FICTIONAL_MINISTRY_PATTERNS = [
    (r"\bministry\s+of\s+magic\b", "Ministry of Magic"),
    (r"\bdepartment\s+of\s+mysteries\b", "Department of Mysteries"),
    (r"\bazkaban\s+(?:prison|board)?\b", "Azkaban"),
    (r"\bministry\s+of\s+silly\s+walks\b", "Ministry of Silly Walks"),
    (r"\bministry\s+of\s+(?:truth|peace|love|plenty)\b", "Ministry of Truth"),
    (r"\b(?:ministry|department)\s+of\s+time\s+travel\b", "Department of Time Travel"),
    (r"(?:टाइम\s*ट्रेवल\s*विभाग|समय\s*यात्रा\s*मंत्रालय)", "Department of Time Travel (समय यात्रा विभाग)"),
    (r"\bministry\s+of\s+supernatural(?:\s+affairs)?\b", "Ministry of Supernatural Affairs"),
    (r"\b(?:ministry|department)\s+of\s+witchcraft\b", "Ministry of Witchcraft"),
    (r"\bdepartment\s+of\s+alien(?:\s+affairs)?\b", "Department of Alien Affairs"),
    (r"\b(?:ministry|department)\s+of\s+ufos?\b", "Department of UFOs"),
    (r"\bgalactic\s+federation\b", "Galactic Federation"),
    (r"\bstarfleet\b", "Starfleet"),
    (r"\bhogwarts\b", "Hogwarts"),
]

# Modern plausible-sounding fake / non-existent government ministries
PLAUSIBLE_FAKE_MINISTRY_PATTERNS = [
    (r"\bministry\s+of\s+social\s+media\b", "Ministry of Social Media"),
    (r"\bdepartment\s+of\s+(?:instagram|facebook|twitter|tiktok)\b", "Department of Social Media"),
    (r"\bministry\s+of\s+memes\b", "Ministry of Memes"),
    (r"\bdepartment\s+of\s+viral\s+trends\b", "Department of Viral Trends"),
    (r"\bministry\s+of\s+artificial\s+intelligence(?:\s+(?:and|\&)\s+robots)?\b", "Ministry of Artificial Intelligence and Robots"),
    (r"\bdepartment\s+of\s+cryptocurrency\b", "Department of Cryptocurrency"),
    (r"\bministry\s+of\s+(?:web3|bitcoin)\b", "Ministry of Web3/Cryptocurrency"),
    (r"\b(?:central\s+)?department\s+of\s+dating(?:\s+and\s+matrimony)?\b", "Department of Dating and Matrimony"),
    (r"\bministry\s+of\s+romance\b", "Ministry of Romance"),
    (r"\bministry\s+of\s+internet\s+complaints\b", "Ministry of Internet Complaints"),
    (r"\bministry\s+of\s+whatsapp(?:\s+forward)?\s+verification\b", "Ministry of WhatsApp Forward Verification"),
    (r"\bcentral\s+drone\s+delivery\s+ministry\b", "Central Drone Delivery Ministry"),
    (r"\bministry\s+of\s+sleep(?:\s+and\s+relaxation)?\b", "Ministry of Sleep"),
    (r"\bministry\s+of\s+gossip(?:\s+redressal)?\b", "Ministry of Gossip Redressal"),
]

# Fraudulent, phishing, and scam welfare schemes
SCAM_SCHEME_PATTERNS = [
    (r"\b(?:pm|pradhan\s+mantri)?\s*free\s+bitcoin(?:\s+(?:yojana|scheme))?\b", "PM Free Bitcoin Yojana"),
    (r"\b(?:pm|pradhan\s+mantri)?\s*crypto(?:\s+(?:yojana|scheme))?\b", "Pradhan Mantri Crypto Scheme"),
    (r"\b(?:pm|pradhan\s+mantri)?\s*free\s+iphone(?:\s+2026)?(?:\s+(?:yojana|scheme))?\b", "Pradhan Mantri Free iPhone Scheme"),
    (r"\bfree\s+smartphone(?:\s+distribution)?(?:\s+(?:scheme|2026|yojana))?\b", "Free Smartphone Distribution Scheme 2026"),
    (r"\b(?:pm|pradhan\s+mantri)?\s*free\s+(?:5g\s+)?recharge(?:\s+(?:yojana|scheme))?\b", "PM Free 5G Recharge Yojana"),
    (r"\b(?:pm|pradhan\s+mantri)?\s*lottery\s+scheme\b", "Pradhan Mantri Lottery Scheme"),
    (r"\b(?:pm\s+)?kbc\s+(?:pm\s+)?(?:lottery|jackpot)(?:\s+yojana)?\b", "KBC PM Jackpot Yojana"),
    (r"\b(?:pm|pradhan\s+mantri)?\s*crore\s*pati\s+bano\s+yojana\b", "PM Crorepati Bano Yojana"),
    (r"\b(?:pm|pradhan\s+mantri)?\s*ghar\s+baithe\s+paisa\s+kamao(?:\s+(?:yojana|scheme))?\b", "PM Ghar Baithe Paisa Kamao Yojana"),
    (r"(?:प्रधानमंत्री\s*)?घर\s*बैठे\s*पैसा\s*(?:कमाओ|कमाएं)?", "प्रधानमंत्री घर बैठे पैसा कमाओ योजना"),
    (r"\bnational\s+work[\-\s]from[\-\s]home\s+cash\s+grant\b", "National Work-From-Home Cash Grant"),
    (r"\bnational\s+online\s+gaming\s+cash\s+prize\b", "National Online Gaming Cash Prize"),
    (r"\baviator\s+double\s+money\b", "Aviator Double Money Scheme"),
    (r"\b(?:pm|pradhan\s+mantri)?\s*free\s+gold\s+coin(?:\s+scheme)?\b", "PM Free Gold Coin Scheme"),
    (r"\bzero\s+tax\s+guaranteed\s+wealth\s+scheme\b", "Zero Tax Guaranteed Wealth Scheme"),
]

# Out-of-scope non-civic private, commercial, and personal matters
OUT_OF_SCOPE_DISPUTE_PATTERNS = [
    r"\b(?:padosi|neighbor|roommate|dost|friend)\b.*?\b(?:udhar|borrowed|loan|paisa|money|rent)\b.*?\b(?:wapas|return|dena|pay|won't|refuses)",
    r"\b(?:borrowed|lent)\b.*?\b(?:refuses|won't|not\s+returning|pay\s+back|return)",
    r"\b(?:aviator|1xbet|dream11|teen\s+patti|betting|casino|gambling)\b",
    r"\b(?:give\s+me\s+a\s+(?:.*?\b)?job|naukri\s+chahiye|hire\s+me|unemployed\s+give\s+me\s+job)\b",
]


def check_gate_zero(text: str) -> Optional[TriageRejectionResponse]:
    """
    Executes Gate 0 deterministic screening on raw citizen input.
    Returns TriageRejectionResponse if any rejection condition triggers,
    or None if the complaint passes Gate 0.
    """
    if not text or not text.strip():
        return None

    # Check scams FIRST (scams take precedence over mentions of real ministries)
    for pattern, name in SCAM_SCHEME_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return TriageRejectionResponse(
                status="REJECTED",
                rejection_code=RejectionCode.FRAUDULENT_OR_FICTITIOUS_SCHEME,
                is_valid_civic_grievance=False,
                rejected_entity=name,
                message=f"Rejection: '{name}' is a fraudulent or non-existent scheme and phishing campaign.",
                reason="Identified as a known lottery, phishing, or unauthorized financial scheme targeting citizens.",
                suggested_action="Do not share personal details, bank accounts, or OTPs. Legitimate government schemes are hosted exclusively on .gov.in domains."
            )

    # Check Fictional / Pop-Culture Ministries
    for pattern, name in FICTIONAL_MINISTRY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return TriageRejectionResponse(
                status="REJECTED",
                rejection_code=RejectionCode.FAKE_GOVERNMENT_BODY,
                is_valid_civic_grievance=False,
                rejected_entity=name,
                message=f"Rejection: '{name}' is a fictional or satirical body and does not exist in the Government of India.",
                reason="Entity failed validation against the official Central Ministries and Departments Schema Registry.",
                suggested_action="Please file grievances only regarding recognized Central Ministries (Railways, Telecom, Banking, Posts), State PDS, or Public Utilities."
            )

    # Check Plausible-Sounding Fake Ministries
    for pattern, name in PLAUSIBLE_FAKE_MINISTRY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return TriageRejectionResponse(
                status="REJECTED",
                rejection_code=RejectionCode.FAKE_GOVERNMENT_BODY,
                is_valid_civic_grievance=False,
                rejected_entity=name,
                message=f"Rejection: '{name}' is not an authorized or existent Ministry/Department under the Government of India or State Governments.",
                reason="No statutory department or administrative division exists under this title.",
                suggested_action="Verify your concern with official civic portals such as CPGRAMS (pgportal.gov.in) or consumer forums."
            )

    # Check Out-of-Scope Personal & Commercial Disputes
    for pattern in OUT_OF_SCOPE_DISPUTE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return TriageRejectionResponse(
                status="REJECTED",
                rejection_code=RejectionCode.OUT_OF_SCOPE_COMMERCIAL_DISPUTE,
                is_valid_civic_grievance=False,
                rejected_entity="Private / Commercial Dispute",
                message="Rejection: Personal debts, private financial disputes, online gambling losses, and employment solicitations fall outside public grievance redressal.",
                reason="The matter lacks public administrative or statutory service delivery jurisdiction.",
                suggested_action="For personal monetary disputes, approach a civil court or legal aid; for cyber fraud/betting, lodge a report at cybercrime.gov.in."
            )

    return None


def check_rejections(text: str) -> Optional[TriageRejectionResponse]:
    """Alias for check_gate_zero to match test harness."""
    return check_gate_zero(text)
