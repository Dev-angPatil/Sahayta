# VISION.md — Project Sahayta

> **Build AI Agents. Solve Real Problems. Create Impact for Bharat.**

---

## 1. Executive Summary
In India, hundreds of millions of citizens interact with government portals annually to resolve civic grievances, access food security under the Public Distribution System (PDS), dispute utility bills, and seek administrative relief. However, the administrative landscape is fragmented across thousands of central, state, and local portals (CPGRAMS, Aaple Sarkar, Jan Sunwai, state DISCOMs, municipal boards). 

Most citizens either abandon grievances due to confusing interfaces, legalistic jargon, and unclear jurisdiction, or fall prey to fraudulent touts and cyber scams. Traditional AI chatbots offer minimal help: they act as search engines that output generic hyperlinks (*"Please visit pgportal.gov.in"*), shifting the cognitive and procedural burden back onto the vulnerable citizen.

**Sahayta** is an autonomous, action-oriented GovTech AI Agent that fundamentally redefines citizen-state engagement. Rather than merely answering questions, Sahayta:
1. **Understands** unstructured citizen complaints in natural vernacular languages (English, Hindi, Hinglish).
2. **Triages** issues to the verified statutory authority across 56 Union Ministries and State utilities.
3. **Guards against Hallucinations & Scams** via deterministic Gate 0 blacklists and grounded Pydantic schema whitelists.
4. **Elicits** only missing mandatory data through progressive, targeted dialogue.
5. **Synthesizes** formal administrative petitions adhering to Constitution of India Article 350 and DARPG Citizen's Charter standards.
6. **Executes** submission through a Human-in-the-Loop (HITL) review gate, delivering a verifiable cryptographic filing receipt with statutory resolution timelines.

---

## 2. Target Citizen Personas & Problem Scenarios

### Persona 1: Savitri Devi (Rural Citizen, Uttar Pradesh)
- **Problem:** Denied monthly subsidized foodgrains by local Fair Price Shop (FPS) dealer under the National Food Security Act (NFSA).
- **Current Barrier:** Cannot navigate English-centric portals, unaware of the District Supply Officer’s grievance channel, fears retaliation.
- **Sahayta Experience:** Savitri speaks or types in Hindi (*"FPS1042 dealer ne monthly ration dene se mana kar diya"*). Sahayta identifies State PDS jurisdiction, solicits ration card number, synthesizes a formal petition under NFSA Section 15, and lodges the complaint with an official tracking token.

### Persona 2: Ramesh Sharma (Urban Commuter, Mumbai)
- **Problem:** Train cancelled by Indian Railways; IRCTC refund of Rs. 2,450 delayed for over 16 days.
- **Current Barrier:** Railway refund portal gives automated boilerplate responses without resolution.
- **Sahayta Experience:** Ramesh types his PNR and complaint. Sahayta maps this directly to CPGRAMS (Ministry of Railways, DARPG), validates PNR format, gathers contact details, drafts an administrative complaint citing the Passenger Charter, and files it with a 60-day statutory redressal guarantee.

### Persona 3: Ananya Rao (Apartment Resident, Bengaluru)
- **Problem:** Exposed live power wire and sparking distribution transformer outside residence.
- **Current Barrier:** DISCOM IVR phone lines constantly busy; danger is immediate.
- **Sahayta Experience:** Explains location and Consumer ID. Sahayta flags the issue as Hazardous Infrastructure under Section 42(5) of the Electricity Act 2003, drafts an urgent rectification directive to the Executive Engineer, and files an emergency grievance.

---

## 3. Core Anti-Hallucination & Grounding Principles

Government portals demand 100% precision. Fabricated tracking IDs, invented departments, or hallucinated schemes cause immense civic harm. Sahayta enforces a zero-hallucination guarantee:
1. **Gate 0 Verification:** Rejects pop-culture ministries (Ministry of Magic, Department of Time Travel), plausible fake bodies (Ministry of Memes, Department of Cryptocurrency), and financial scams (PM Free iPhone Scheme, PM Bitcoin Yojana) with HTTP 422 and actionable safety advisories.
2. **Strict Schema Whitelisting:** Every target portal enforces a rigid Pydantic v2 schema with `extra="forbid"`. The agent can never invent arbitrary fields or demand irrelevant documents.
3. **Zero Pre-Submission Tracking Numbers:** Tracking IDs are strictly produced by the submission engine post-confirmation, preventing phantom reference numbers.
4. **Statutory Anchoring:** Every petition is grounded in real Indian law (NFSA 2013, Electricity Act 2003, Article 350, Consumer Protection Act 2019).

---

## 4. Success Criteria & Impact Metrics for Bharat

| Metric | Baseline (Manual Portals / Generic Chatbots) | Sahayta Impact |
|---|---|---|
| **Filing Completion Time** | 45–90 minutes (multiple forms, confusion) | Under 3 minutes |
| **Grievance Rejection Rate** | >35% due to missing mandatory fields or wrong jurisdiction | <2% (100% schema completeness guaranteed) |
| **Vernacular Inclusion** | Low (overwhelmingly formal bureaucratic English) | High (Seamless Hindi, Hinglish, English ingestion) |
| **Administrative Quality** | Informal, emotional complaints often dismissed | Article 350 compliant petitions with legal prayers |
| **Scam Protection** | Vulnerable to phishing and fake government schemes | 100% deterministic rejection of unverified bodies |
