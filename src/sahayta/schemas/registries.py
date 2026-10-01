"""
src/sahayta/schemas/registries.py
Canonical Whitelists & Blacklists for Indian Civic Grievance Triage.
Contains 56 official Union Ministries, DISCOMs catalog, Water Boards catalog,
and deterministic blacklists for fictional bodies, fake departments, scams, and out-of-scope disputes.
"""

from __future__ import annotations
import re
from typing import Dict, List, Optional, Tuple, Any
from sahayta.schemas.rejection import RejectionCode


# =====================================================================
# 1. 56 OFFICIAL CANONICAL UNION MINISTRIES & DEPARTMENTS
# =====================================================================

CENTRAL_MINISTRIES_WHITELIST: List[Dict[str, Any]] = [
    {"name": "Ministry of Agriculture and Farmers Welfare", "acronym": "MoAFW", "hindi": "कृषि एवं किसान कल्याण मंत्रालय", "keywords": ["agriculture", "farmer", "kisan", "pm-kisan", "crop insurance", "pmfby", "fasal bima", "msp", "krishi"]},
    {"name": "Ministry of Chemicals and Fertilizers", "acronym": "MoCF", "hindi": "रसायन एवं उर्वरक मंत्रालय", "keywords": ["fertilizer", "urea", "chemical", "pharma", "nppa", "medicine price", "dbt fertilizer"]},
    {"name": "Ministry of Civil Aviation", "acronym": "MoCA", "hindi": "नागर विमानन मंत्रालय", "keywords": ["airport", "flight", "dgca", "airline", "aai", "airfare", "baggage loss", "air travel", "udan"]},
    {"name": "Ministry of Coal", "acronym": "MoC", "hindi": "कोयला मंत्रालय", "keywords": ["coal", "coal india", "cil", "mining", "coal linkage"]},
    {"name": "Ministry of Commerce and Industry", "acronym": "MoCI", "hindi": "वाणिज्य एवं उद्योग मंत्रालय", "keywords": ["commerce", "industry", "export", "import", "dpiit", "patent", "trademark", "sez", "gem portal", "startup"]},
    {"name": "Ministry of Communications", "acronym": "MoC", "hindi": "संचार मंत्रालय", "keywords": ["telecom", "dot", "bsnl", "mtnl", "posts", "india post", "speed post", "sim", "broadband", "mnp", "sanchar saathi"]},
    {"name": "Ministry of Consumer Affairs, Food and Public Distribution", "acronym": "MoCAF&PD", "hindi": "उपभोक्ता मामले, खाद्य और सार्वजनिक वितरण मंत्रालय", "keywords": ["consumer affairs", "national consumer helpline", "nch", "bis", "consumer forum", "unfair trade", "rationing", "nfsa", "fci"]},
    {"name": "Ministry of Corporate Affairs", "acronym": "MCA", "hindi": "कॉर्पोरेट कार्य मंत्रालय", "keywords": ["mca21", "company registration", "roc", "director din", "corporate fraud", "sfio", "insolvency", "ibbi"]},
    {"name": "Ministry of Culture", "acronym": "MoC", "hindi": "संस्कृति मंत्रालय", "keywords": ["culture", "asi", "archaeological survey", "monument", "national museum", "cultural grant", "heritage"]},
    {"name": "Ministry of Defence", "acronym": "MoD", "hindi": "रक्षा मंत्रालय", "keywords": ["defence", "army", "navy", "air force", "cantonment board", "sparsh pension", "orop", "drdo", "sainik school"]},
    {"name": "Ministry of Development of North Eastern Region", "acronym": "MDoNER", "hindi": "उत्तर पूर्वी क्षेत्र विकास मंत्रालय", "keywords": ["doner", "north east", "assam", "manipur", "meghalaya", "tripura", "mdo-ner"]},
    {"name": "Ministry of Earth Sciences", "acronym": "MoES", "hindi": "पृथ्वी विज्ञान मंत्रालय", "keywords": ["earth sciences", "imd", "weather forecast", "cyclone alert", "monsoon", "oceanography"]},
    {"name": "Ministry of Education", "acronym": "MoE", "hindi": "शिक्षा मंत्रालय", "keywords": ["education", "cbse", "ugc", "nta", "neet", "jee", "school", "university", "ncert", "higher education", "scholarship"]},
    {"name": "Ministry of Electronics and Information Technology", "acronym": "MeitY", "hindi": "इलेक्ट्रॉनिकी और सूचना प्रौद्योगिकी मंत्रालय", "keywords": ["meity", "uidai", "aadhaar", "digilocker", "cert-in", "cyber security", "it rules", "semiconductor"]},
    {"name": "Ministry of Environment, Forest and Climate Change", "acronym": "MoEFCC", "hindi": "पर्यावरण, वन और जलवायु परिवर्तन मंत्रालय", "keywords": ["environment", "forest", "pollution", "cpcb", "wildlife", "climate change", "crz clearance", "air quality"]},
    {"name": "Ministry of External Affairs", "acronym": "MEA", "hindi": "विदेश मंत्रालय", "keywords": ["external affairs", "passport", "psk", "visa", "consular", "embassy", "high commission", "overseas citizen", "oci", "pcc"]},
    {"name": "Ministry of Finance", "acronym": "MoF", "hindi": "वित्त मंत्रालय", "keywords": ["finance", "income tax", "cbdt", "gst", "cbic", "banking", "dfs", "sbi", "pnb", "nationalised bank", "insurance", "lic", "ed", "customs", "pension", "nps"]},
    {"name": "Ministry of Fisheries, Animal Husbandry and Dairying", "acronym": "MoFAHD", "hindi": "मत्स्यपालन, पशुपालन और डेयरी मंत्रालय", "keywords": ["fisheries", "dairy", "animal husbandry", "pashupalan", "poultry", "milk cooperative", "kcc animal"]},
    {"name": "Ministry of Food Processing Industries", "acronym": "MoFPI", "hindi": "खाद्य प्रसंस्करण उद्योग मंत्रालय", "keywords": ["food processing", "cold chain", "mega food park", "pmksy", "pm fme"]},
    {"name": "Ministry of Health and Family Welfare", "acronym": "MoHFW", "hindi": "स्वास्थ्य एवं परिवार कल्याण मंत्रालय", "keywords": ["health", "cghs", "aiims", "pm-jay", "ayushman bharat", "vaccine", "fssai", "drug control", "medical hospital"]},
    {"name": "Ministry of Heavy Industries", "acronym": "MHI", "hindi": "भारी उद्योग मंत्रालय", "keywords": ["heavy industries", "fame subsidy", "ev subsidy", "bhel", "automotive standard"]},
    {"name": "Ministry of Home Affairs", "acronym": "MHA", "hindi": "गृह मंत्रालय", "keywords": ["home affairs", "central police", "crpf", "bsf", "cisf", "disaster management", "ndrf", "cybercrime portal", "fcra", "immigration"]},
    {"name": "Ministry of Housing and Urban Affairs", "acronym": "MoHUA", "hindi": "आवासन और शहरी कार्य मंत्रालय", "keywords": ["urban affairs", "pmay-u", "housing", "pm svanidhi", "cpwd", "metro rail", "smart cities", "swachh bharat urban"]},
    {"name": "Ministry of Information and Broadcasting", "acronym": "MIB", "hindi": "सूचना एवं प्रसारण मंत्रालय", "keywords": ["information broadcasting", "doordarshan", "all india radio", "cbfc", "broadcast grievance", "ott regulation", "press council"]},
    {"name": "Ministry of Jal Shakti", "acronym": "MoJS", "hindi": "जल शक्ति मंत्रालय", "keywords": ["jal shakti", "jal jeevan mission", "namami gange", "cwc", "ground water", "inter-state river", "drinking water"]},
    {"name": "Ministry of Labour and Employment", "acronym": "MoLE", "hindi": "श्रम और रोजगार मंत्रालय", "keywords": ["labour", "employment", "epfo", "pf claim", "provident fund", "esic", "uan", "shram suvidha", "e-shram", "minimum wages"]},
    {"name": "Ministry of Law and Justice", "acronym": "MoLJ", "hindi": "विधि एवं न्याय मंत्रालय", "keywords": ["law", "justice", "e-courts", "legal aid", "nalsa", "bar council", "notary", "judicial"]},
    {"name": "Ministry of Micro, Small and Medium Enterprises", "acronym": "MSME", "hindi": "सूक्ष्म, लघु और मध्यम उद्यम मंत्रालय", "keywords": ["msme", "udyam registration", "udyog aadhaar", "kvic", "coir board", "msme samadhaan", "delayed payment"]},
    {"name": "Ministry of Mines", "acronym": "MoM", "hindi": "खान मंत्रालय", "keywords": ["mines", "ibm", "mineral concession", "gsi", "geological survey", "mining lease"]},
    {"name": "Ministry of Minority Affairs", "acronym": "MoMA", "hindi": "अल्पसंख्यक कार्य मंत्रालय", "keywords": ["minority affairs", "scholarship", "haj committee", "waqf board", "usttad", "nai roshni"]},
    {"name": "Ministry of New and Renewable Energy", "acronym": "MNRE", "hindi": "नवीन और नवीकरणीय ऊर्जा मंत्रालय", "keywords": ["renewable energy", "solar subsidy", "rooftop solar", "pm-surya ghar", "wind energy", "solar pump", "pm-kusum"]},
    {"name": "Ministry of Panchayati Raj", "acronym": "MoPR", "hindi": "पंचायती राज मंत्रालय", "keywords": ["panchayati raj", "gram panchayat", "e-gram swaraj", "swamitva", "rural local body"]},
    {"name": "Ministry of Parliamentary Affairs", "acronym": "MoPA", "hindi": "संसदीय कार्य मंत्रालय", "keywords": ["parliamentary affairs", "parliament session", "lok sabha", "rajya sabha questions"]},
    {"name": "Ministry of Personnel, Public Grievances and Pensions", "acronym": "MoPPGP", "hindi": "कार्मिक, लोक शिकायत तथा पेंशन मंत्रालय", "keywords": ["darpg", "cpgrams", "dopt", "ssc", "upsc", "central pension", "cpao", "administrative reforms"]},
    {"name": "Ministry of Petroleum and Natural Gas", "acronym": "MoPNG", "hindi": "पेट्रोलियम और प्राकृतिक गैस मंत्रालय", "keywords": ["petroleum", "lpg", "domestic gas", "indane", "bharat gas", "hp gas", "petrol pump", "cng", "ujjwala", "png"]},
    {"name": "Ministry of Planning", "acronym": "MoP", "hindi": "योजना मंत्रालय", "keywords": ["planning", "niti aayog", "evaluation", "statistical planning"]},
    {"name": "Ministry of Power", "acronym": "MoP", "hindi": "विद्युत मंत्रालय", "keywords": ["power", "national grid", "central electricity authority", "cea", "rec", "pfc", "powergrid", "rdss"]},
    {"name": "Ministry of Railways", "acronym": "MoR", "hindi": "रेल मंत्रालय", "keywords": ["railway", "train", "irctc", "pnr", "railway board", "passenger reservation", "coach", "railway station", "refund"]},
    {"name": "Ministry of Road Transport and Highways", "acronym": "MoRTH", "hindi": "सड़क परिवहन एवं राजमार्ग मंत्रालय", "keywords": ["road transport", "highway", "nhai", "national highway", "toll", "fastag", "vahan", "sarathi", "driving license"]},
    {"name": "Ministry of Rural Development", "acronym": "MoRD", "hindi": "ग्रामीण विकास मंत्रालय", "keywords": ["rural development", "mgnrega", "pmay-g", "rural housing", "nrlm", "pmgsy", "rural roads"]},
    {"name": "Ministry of Science and Technology", "acronym": "MoST", "hindi": "विज्ञान और प्रौद्योगिकी मंत्रालय", "keywords": ["science technology", "dst", "dbt", "csir", "scientific research", "inspire scholarship"]},
    {"name": "Ministry of Ports, Shipping and Waterways", "acronym": "MoPSW", "hindi": "पत्तन, पोत परिवहन और जलमार्ग मंत्रालय", "keywords": ["ports", "shipping", "waterways", "major port", "inland waterways", "iwai", "sagarmala"]},
    {"name": "Ministry of Skill Development and Entrepreneurship", "acronym": "MSDE", "hindi": "कौशल विकास और उद्यमशीलता मंत्रालय", "keywords": ["skill development", "pmkvy", "nsdc", "iti", "apprenticeship", "skill india"]},
    {"name": "Ministry of Social Justice and Empowerment", "acronym": "MSJE", "hindi": "सामाजिक न्याय और अधिकारिता मंत्रालय", "keywords": ["social justice", "empowerment", "sc scholarship", "disability", "divyangjan", "depwd", "elderly welfare"]},
    {"name": "Ministry of Statistics and Programme Implementation", "acronym": "MoSPI", "hindi": "सांख्यिकी और कार्यक्रम कार्यान्वयन मंत्रालय", "keywords": ["statistics", "mospi", "mplads", "cso", "nsso", "economic census"]},
    {"name": "Ministry of Steel", "acronym": "MoS", "hindi": "इस्पात मंत्रालय", "keywords": ["steel", "sail", "rashtriya ispat nigam", "steel plant", "iron ore"]},
    {"name": "Ministry of Textiles", "acronym": "MoT", "hindi": "वस्त्र मंत्रालय", "keywords": ["textiles", "handloom", "handicraft", "cotton", "jute", "silk board", "weavers"]},
    {"name": "Ministry of Tourism", "acronym": "MoT", "hindi": "पर्यटन मंत्रालय", "keywords": ["tourism", "incredible india", "itdc", "swadesh darshan", "prasad scheme", "hotel classification"]},
    {"name": "Ministry of Tribal Affairs", "acronym": "MoTA", "hindi": "जनजातीय कार्य मंत्रालय", "keywords": ["tribal affairs", "trifed", "eklavya model school", "forest rights act", "fra", "st scholarship"]},
    {"name": "Ministry of Women and Child Development", "acronym": "MWCD", "hindi": "महिला एवं बाल विकास मंत्रालय", "keywords": ["women child development", "poshan", "anganwadi", "child helpline", "mission vatsalya", "mission shakti", "sukanya"]},
    {"name": "Ministry of Youth Affairs and Sports", "acronym": "MYAS", "hindi": "युवा कार्यक्रम और खेल मंत्रालय", "keywords": ["sports", "youth affairs", "khelo india", "sai", "nss", "nehru yuva kendra", "sports federation"]},
    {"name": "Ministry of Ayush", "acronym": "AYUSH", "hindi": "आयुष मंत्रालय", "keywords": ["ayush", "ayurveda", "yoga", "unani", "siddha", "homeopathy", "ayush hospital", "cnam", "national ayush mission"]},
    {"name": "Ministry of Cooperation", "acronym": "MoC", "hindi": "सहकारिता मंत्रालय", "keywords": ["cooperation", "cooperative society", "crsc", "multi-state cooperative", "pacs", "national cooperative database"]},
    {"name": "Department of Atomic Energy", "acronym": "DAE", "hindi": "परमाणु ऊर्जा विभाग", "keywords": ["atomic energy", "barc", "npcil", "nuclear power", "heavy water", "dae"]},
    {"name": "Department of Space", "acronym": "DoS", "hindi": "अंतरिक्ष विभाग", "keywords": ["space", "isro", "satellite", "launch vehicle", "in-space", "antrix", "chandrayaan"]},
    {"name": "Prime Minister's Office / Cabinet Secretariat", "acronym": "PMO", "hindi": "प्रधानमंत्री कार्यालय", "keywords": ["pmo", "prime minister office", "cabinet secretariat", "public grievances pmo", "national relief fund"]},
]

# =====================================================================
# 2. DISCOM PROVIDERS & WATER BOARDS
# =====================================================================

DISCOM_PROVIDERS_WHITELIST = [
    "BSES Rajdhani Power Limited (BRPL)", "BSES Yamuna Power Limited (BYPL)",
    "Tata Power Delhi Distribution Limited (TPDDL)", "Bangalore Electricity Supply Company (BESCOM)",
    "Maharashtra State Electricity Distribution Co. Ltd (MSEDCL)", "Adani Electricity Mumbai Limited (AEML)",
    "Dakshin Haryana Bijli Vitran Nigam (DHBVN)", "Uttar Haryana Bijli Vitran Nigam (UHBVN)",
    "Paschimanchal Vidyut Vitran Nigam Limited (PVVNL)", "Madhyanchal Vidyut Vitran Nigam Limited (MVVNL)",
    "Dakshinanchal Vidyut Vitran Nigam Limited (DVVNL)", "Purvanchal Vidyut Vitran Nigam Limited (PuVVNL)",
    "Calcutta Electric Supply Corporation (CESC)", "Tamil Nadu Generation and Distribution Corporation (TANGEDCO)",
    "Punjab State Power Corporation Limited (PSPCL)", "Torrent Power", "JVVNL", "AVVNL", "JDVVNL", "TSSPDCL"
]

WATER_BOARDS_WHITELIST = [
    "Delhi Jal Board (DJB)", "Bangalore Water Supply and Sewerage Board (BWSSB)",
    "Hyderabad Metropolitan Water Supply & Sewerage Board (HMWSSB)",
    "Brihanmumbai Municipal Corporation Hydraulic Dept (BMC)",
    "Chennai Metro Water Supply & Sewerage Board (CMWSSB)",
    "Kolkata Municipal Corporation Water Supply Dept (KMC)",
    "UP Jal Nigam / Lucknow Jal Sansthan", "Kerala Water Authority (KWA)",
    "Pune Municipal Corporation Water Supply (PMC)", "Ahmedabad Municipal Corporation Water Works (AMC)"
]

# =====================================================================
# 3. BLACKLIST REGEX PATTERNS
# =====================================================================

FICTIONAL_MINISTRIES_REGEX = (
    r"(?i)\b("
    r"ministry\s+of\s+magic|department\s+of\s+mysteries|azkaban|"
    r"ministry\s+of\s+silly\s+walks|ministry\s+of\s+(?:truth|peace|love|plenty)|"
    r"(?:ministry|department)\s+of\s+time\s+travel|टाइम\s*ट्रेवल\s*विभाग|समय\s*यात्रा\s*मंत्रालय|"
    r"ministry\s+of\s+supernatural(?:\s+affairs)?|(?:ministry|department)\s+of\s+witchcraft|"
    r"department\s+of\s+alien(?:\s+affairs)?|(?:ministry|department)\s+of\s+ufos?|"
    r"galactic\s+federation|starfleet|teleportation|invisibility|jedi|hogwarts"
    r")\b"
)

PLAUSIBLE_FAKE_MINISTRIES_REGEX = (
    r"(?i)\b("
    r"ministry\s+of\s+social\s+media|department\s+of\s+(?:instagram|facebook|twitter|tiktok)|"
    r"ministry\s+of\s+memes|department\s+of\s+viral\s+trends|"
    r"ministry\s+of\s+artificial\s+intelligence(?:\s+(?:and|\&)\s+robots)?|robot\s+grievance|"
    r"department\s+of\s+cryptocurrency|ministry\s+of\s+(?:web3|bitcoin)|"
    r"(?:central\s+)?department\s+of\s+dating(?:\s+and\s+matrimony)?|ministry\s+of\s+romance|"
    r"ministry\s+of\s+internet\s+complaints|department\s+of\s+wi-?fi\s+redressal|"
    r"ministry\s+of\s+whatsapp(?:\s+forward)?\s+verification|fake\s+news\s+redressal\s+ministry|"
    r"central\s+drone\s+delivery\s+ministry|ministry\s+of\s+sleep(?:\s+and\s+relaxation)?|"
    r"ministry\s+of\s+gossip(?:\s+redressal)?|mohalla\s+chugli\s+department|"
    r"ministry\s+of\s+netflix|department\s+of\s+personal\s+luck"
    r")\b"
)

FRAUDULENT_SCHEMES_REGEX = (
    r"(?i)\b("
    r"(?:pm|pradhan\s+mantri)?\s*free\s+bitcoin(?:\s+(?:yojana|scheme))?|"
    r"(?:pm|pradhan\s+mantri)?\s*crypto(?:\s+(?:yojana|scheme))?|"
    r"(?:pm|pradhan\s+mantri)?\s*free\s+iphone(?:\s+2026)?(?:\s+(?:yojana|scheme))?|"
    r"free\s+smartphone(?:\s+distribution)?(?:\s+(?:scheme|2026|yojana))?|"
    r"(?:pm|pradhan\s+mantri)?\s*free\s+(?:5g\s+)?recharge(?:\s+(?:yojana|scheme))?|"
    r"free\s+3-?month\s+(?:jio|airtel)\s+recharge|"
    r"(?:pm|pradhan\s+mantri)?\s*lottery\s+scheme|"
    r"(?:pm\s+)?kbc\s+(?:pm\s+)?(?:lottery|jackpot)(?:\s+yojana)?|"
    r"(?:pm|pradhan\s+mantri)?\s*crore\s*pati\s+bano\s+yojana|"
    r"(?:pm|pradhan\s+mantri)?\s*ghar\s+baithe\s+paisa\s+kamao(?:\s+(?:yojana|scheme))?|"
    r"(?:प्रधानमंत्री\s*)?घर\s*बैठे\s*पैसा\s*(?:कमाओ|कमाएं)?|"
    r"national\s+work[\-\s]from[\-\s]home\s+cash\s+grant|"
    r"national\s+online\s+gaming\s+cash\s+prize|aviator\s+double\s+money|"
    r"(?:pm|pradhan\s+mantri)?\s*free\s+gold\s+coin(?:\s+scheme)?|"
    r"zero\s+tax\s+guaranteed\s+wealth\s+scheme"
    r")\b"
)

OUT_OF_SCOPE_REGEX = (
    r"(?i)\b("
    r"(?:padosi|neighbor|roommate|dost|friend)\b.*?\b(?:udhar|borrowed|loan|paisa|money)\b.*?\b(?:wapas|return|dena|pay\s+back|won't\s+pay|not\s+return)|"
    r"(?:borrowed|lent)\b.*?\b(?:refuses\s+to\s+return|won't\s+pay\s+back|not\s+returning)|"
    r"(?:aviator|1xbet|dream11|teen\s+patti|betting\s+app|online\s+casino|gambling)|"
    r"(?:give\s+me\s+a\s+job|naukri\s+chahiye|hire\s+me|unemployed\s+give\s+me\s+job|give\s+me\s+a\s+(?:peon|clerk)\s+job)"
    r")\b"
)


# =====================================================================
# 4. REJECTION CHECK HELPER
# =====================================================================

def check_rejection(text: str) -> Optional[Tuple[RejectionCode, str, str]]:
    """
    Checks if an input matches any blacklisted fictional body, scam, or out-of-scope dispute.
    Returns: (RejectionCode, matched_entity, explanation) or None if clean.
    """
    if not text:
        return None

    # 1. Fictional / Pop-culture Ministries
    m_fic = re.search(FICTIONAL_MINISTRIES_REGEX, text)
    if m_fic:
        entity = m_fic.group(0).strip().title()
        return (
            RejectionCode.FAKE_GOVERNMENT_BODY,
            entity,
            f"'{entity}' is a fictional, satirical, or pop-culture entity."
        )

    # 2. Plausible fake bodies
    m_fake = re.search(PLAUSIBLE_FAKE_MINISTRIES_REGEX, text)
    if m_fake:
        entity = m_fake.group(0).strip().title()
        return (
            RejectionCode.FAKE_GOVERNMENT_BODY,
            entity,
            f"'{entity}' does not exist in the official Union or State government directories."
        )

    # 3. Fraudulent schemes
    m_scam = re.search(FRAUDULENT_SCHEMES_REGEX, text)
    if m_scam:
        scheme = m_scam.group(0).strip().title()
        return (
            RejectionCode.FRAUDULENT_OR_FICTITIOUS_SCHEME,
            scheme,
            f"'{scheme}' is an identified fraudulent scam, phishing campaign, or fake lottery."
        )

    # 4. Out-of-scope commercial/personal disputes
    m_oos = re.search(OUT_OF_SCOPE_REGEX, text)
    if m_oos:
        return (
            RejectionCode.OUT_OF_SCOPE_COMMERCIAL_DISPUTE,
            "Private / Commercial Dispute",
            "Matter involves private debts, personal loans, online gaming/betting losses, or job solicitations outside public grievance redressal."
        )

    return None
