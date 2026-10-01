# 🇮🇳 Sahayta — Action-Oriented GovTech AI Agent for Bharat

[![BharatAgentic Hackathon](https://img.shields.io/badge/BharatAgentic-aiKart%202026-orange.svg)](https://aikart.in)
[![Category](https://img.shields.io/badge/Category-Citizen%20%26%20GovTech-blue.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](#)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

> **"Identify a meaningful problem. Build an intelligent agent. Give it the ability to reason and act. Create measurable impact for Bharat."**

**Sahayta** is an autonomous, action-oriented GovTech AI Agent built for the **BharatAgentic Hackathon (powered by aiKart)**. Moving beyond passive informational chatbots that merely provide web links, Sahayta understands unstructured citizen complaints in natural vernacular languages (English, Hindi, Hinglish), triages them into verified central and state portal schemas, interactively elicits missing particulars, synthesizes formal administrative petitions (compliant with Article 350 of the Constitution of India and DARPG standards), and automates filing with a Human-in-the-Loop confirmation gate.

---

## 🌟 Key Differentiators: Beyond Simple Chatbots

| Dimension | Standard Chatbot | Sahayta GovTech Agent |
|---|---|---|
| **Action Capability** | Passive text output (*"Visit pgportal.gov.in"*) | Active execution: Triages, elicits gaps, formats petition, and generates verified filing payload |
| **Hallucination Risk** | High: Inventing fake schemes, false tracking IDs, or wrong URLs | **Zero**: Strictly grounded against 56 Union Ministries and Pydantic v2 schemas (`extra='forbid'`) |
| **Scam / Fraud Screening** | Vulnerable to user deception | Deterministic **Gate 0 screening**: Rejects pop-culture ministries, fake subsidies, and cyber scams |
| **Administrative Quality** | Fragmented citizen text | Synthesizes formal administrative petitions with statutory citations (NFSA 2013, Electricity Act 2003) |
| **Citizen Accountability** | None | Verifiable cryptographic filing receipt with SHA-256 integrity token and statutory deadlines |

---

## 🏛️ Supported Grounded Civic Portals

1. **CPGRAMS Central Public Grievance Portal (`GOVTECH_CPGRAMS_V1`)**
   - *Authority:* Department of Administrative Reforms and Public Grievances (DARPG), Government of India.
   - *Domains:* Railways (IRCTC refunds, PNR disputes), Telecom (DoT, BSNL, SIM fraud), Banking (DFS, SBI, public sector banks), Passport (MEA), Posts.
   - *Statute:* Constitution of India (Article 350) & Citizen's Charter 60-day resolution standard.

2. **State Public Distribution System (`STATE_PDS_V1`)**
   - *Authority:* Department of Food, Civil Supplies & Consumer Affairs.
   - *Domains:* Ration non-disbursal, ePoS biometric failures, dealer overcharging, delayed card modification.
   - *Statute:* National Food Security Act (NFSA) 2013, Sections 15 & 16.

3. **State Electricity Distribution Company (`DISCOM_POWER_V1`)**
   - *Authority:* State Electricity Regulatory Commission (SERC) / DISCOM Consumer Forum.
   - *Domains:* Prolonged outages, billing disputes, defective meters, hazardous infrastructure.
   - *Statute:* Electricity Act 2003, Section 42(5) (CGRF Norms).

4. **Municipal Water Supply & Sewerage Board (`MUNICIPAL_WATER_V1`)**
   - *Authority:* Municipal Corporation / City Jal Board.
   - *Domains:* Contaminated drinking water, supply failure, pipeline leakage, sewer overflows.
   - *Statute:* Municipal Corporation Citizen's Charter for Potable Water Supply.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+
- Git
- (Optional) Docker

### Local Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Dev-angPatil/Sahayta.git
   cd Sahayta
   ```

2. **Create and Activate a Virtual Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -e .
   ```

4. **Run the Sahayta Application:**
   ```bash
   uvicorn sahayta.api.app:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Open in Browser:**
   - **Interactive Web Interface:** Navigate to `http://localhost:8000`
   - **Interactive OpenAPI / Swagger Documentation:** Navigate to `http://localhost:8000/docs`

---

## 🐳 Running via Docker (Submission Method 1)

Sahayta includes a production-ready, minimal Docker container:

```bash
# Build the Docker image
docker build -t sahayta-agent:latest .

# Run the container
docker run -p 8000:8000 sahayta-agent:latest

# Verify health
curl -f http://localhost:8000/health
```

---

## 🔌 API Reference & Usage (Submission Method 2)

### 1. Health Probe
```bash
curl -X GET http://localhost:8000/health
```
**Response:**
```json
{
  "status": "healthy",
  "service": "sahayta",
  "version": "1.0.0",
  "category": "Citizen & GovTech"
}
```

### 2. Triage & Interactive Chat (`POST /api/v1/agent/chat`)
```bash
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_demo_01",
    "message": "IRCTC train 12952 was cancelled on 15 Sept, but my refund of Rs 2,450 has not been received after 16 days. PNR is 2458971234."
  }'
```
**Response:**
```json
{
  "session_id": "sess_demo_01",
  "status": "ELICITING",
  "portal": "CPGRAMS",
  "schema_id": "GOVTECH_CPGRAMS_V1",
  "collected_fields": {
    "reference_number": "2458971234",
    "disputed_amount": 2450.0
  },
  "missing_fields": [
    "complainant_name",
    "mobile_number"
  ],
  "agent_message": "Namaste. I have mapped your grievance to CPGRAMS (Ministry of Railways). To complete your petition, please provide your Full Name."
}
```

### 3. Anti-Hallucination & Scam Rejection Example
```bash
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_scam_01",
    "message": "How do I claim my 50000 rupees subsidy under PM Free Bitcoin Yojana?"
  }'
```
**Response (HTTP 422 Unprocessable Entity):**
```json
{
  "status": "REJECTED",
  "rejection_code": "FRAUDULENT_OR_FICTITIOUS_SCHEME",
  "is_valid_civic_grievance": false,
  "flagged_entity": "Pm Free Bitcoin Yojana",
  "message": "The scheme or program 'Pm Free Bitcoin Yojana' is not an authorized Indian government initiative.",
  "official_advice": "Never share bank account or OTP details. Verify authentic schemes at myscheme.gov.in."
}
```

### 4. Direct Filing Execution (`POST /api/v1/agent/submit`)
```bash
curl -X POST http://localhost:8000/api/v1/agent/submit \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_demo_01",
    "citizen_confirmation": true
  }'
```
**Response:**
```json
{
  "status": "SUBMITTED",
  "receipt": {
    "tracking_number": "CPGRAMS/2026/0912401",
    "submission_timestamp": "2026-10-01T14:55:00Z",
    "statutory_resolution_deadline": "2026-11-30T14:55:00Z",
    "sha256_integrity_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "advice_to_citizen": "Your grievance has been officially registered with CPGRAMS under Article 350. Please preserve your tracking reference."
  }
}
```

---

## 📦 Hackathon Submission Artifacts

1. **Agent Manifest (Method 1):** [`agent_manifest.yaml`](./agent_manifest.yaml)
2. **Container Dockerfile (Method 1):** [`Dockerfile`](./Dockerfile)
3. **Interactive Swagger Docs (Method 2):** Accessible at `http://localhost:8000/docs`

---

## 📄 License
This project is licensed under the Apache 2.0 License — see the [LICENSE](LICENSE) file for details.
