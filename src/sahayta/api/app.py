"""
src/sahayta/api/app.py
Production-Grade FastAPI REST API for Project Sahayta.
Provides OpenAPI-documented endpoints for Chat, Elicitation, Formal Drafting, Submission,
and static dashboard hosting.
"""

from __future__ import annotations
import os
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from sahayta.agent import SahaytaAgent

app = FastAPI(
    title="Sahayta - GovTech Citizen Action Agent API",
    description=(
        "Intelligent, action-oriented GovTech AI Agent for Indian civic grievance redressal "
        "(CPGRAMS Central Grievance, State PDS/Ration, DISCOM Electricity, Municipal Water Board). "
        "Transforms colloquial complaints into verified administrative petitions with zero hallucinations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend interoperability
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active session cache
sessions: Dict[str, SahaytaAgent] = {}


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Unique citizen session identifier")
    message: str = Field(..., description="Citizen natural language complaint or elicitation answer")


class SubmitRequest(BaseModel):
    session_id: str = Field(..., description="Active session ID with a synthesized grievance draft")
    citizen_confirmation: bool = Field(default=True, description="Explicit citizen confirmation to lodge filing")


@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
def health_check() -> Dict[str, str]:
    """Health check endpoint for liveness & readiness probes."""
    return {
        "status": "healthy",
        "service": "sahayta",
        "version": "1.0.0",
        "category": "Citizen & GovTech",
    }


@app.get("/api/v1/portals", tags=["Portals"])
def list_portals() -> Dict[str, Any]:
    """Lists all verified Indian civic portals registered in Sahayta."""
    return {
        "portals": [
            {
                "id": "GOVTECH_CPGRAMS_V1",
                "name": "CPGRAMS Central Public Grievance Portal",
                "authority": "Department of Administrative Reforms and Public Grievances (DARPG)",
                "statutory_act": "Citizen's Charter & Article 350 of the Constitution of India",
                "domains": ["Railways", "Banking", "Telecommunications", "Passport", "Post"]
            },
            {
                "id": "STATE_PDS_V1",
                "name": "State Public Distribution System (PDS / Ration Card)",
                "authority": "Department of Food, Civil Supplies & Consumer Affairs",
                "statutory_act": "National Food Security Act (NFSA) 2013, Section 15 & 16",
                "domains": ["Ration Non-Disbursal", "ePoS Biometric Failure", "Fair Price Shop Overcharging", "Aadhaar Seeding"]
            },
            {
                "id": "DISCOM_POWER_V1",
                "name": "State Electricity Distribution Company (DISCOM)",
                "authority": "State Electricity Regulatory Commission",
                "statutory_act": "Electricity Act 2003, Section 42(5) (Consumer Grievance Redressal Forum)",
                "domains": ["Prolonged Outage", "Erroneous Billing", "Defective Meter", "Hazardous Infrastructure"]
            },
            {
                "id": "MUNICIPAL_WATER_V1",
                "name": "Municipal Water Supply & Sewerage Board",
                "authority": "Municipal Corporation / Jal Board",
                "statutory_act": "Municipal Corporation Act & Citizen Charter Standards of Potable Water Supply",
                "domains": ["Contaminated Water", "Supply Failure", "Pipeline Leakage", "Sewer Overflow"]
            }
        ]
    }


@app.post("/api/v1/agent/chat", tags=["Agent"])
def chat_with_agent(req: ChatRequest):
    """
    Main conversational endpoint:
    - Triages citizen grievances across languages (English, Hindi, Hinglish).
    - Checks Gate 0 guardrails for fake ministries or scam schemes (returns 422 if detected).
    - Solicits missing required schema fields.
    - Synthesizes formal administrative petition when fields are complete.
    """
    sess_id = req.session_id or f"sess_{os.urandom(4).hex()}"
    if sess_id not in sessions:
        sessions[sess_id] = SahaytaAgent(session_id=sess_id)

    agent = sessions[sess_id]
    result = agent.chat(req.message)

    # If rejected by Gate 0 / anti-hallucination guardrail, return HTTP 422
    if result.get("status") == "REJECTED":
        return JSONResponse(status_code=422, content=result)

    # Ensure draft is serialized if present
    if "draft" in result and hasattr(result["draft"], "model_dump"):
        result["draft"] = result["draft"].model_dump()

    return result


@app.post("/api/v1/agent/submit", tags=["Agent"])
def submit_grievance(req: SubmitRequest):
    """
    Executes official grievance lodgement following citizen HITL review.
    Returns verifiable tracking ID, SHA-256 integrity receipt, and statutory resolution deadline.
    """
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    agent = sessions[req.session_id]
    try:
        receipt = agent.submit(citizen_confirmation=req.citizen_confirmation)
        return {
            "status": "SUBMITTED",
            "receipt": receipt,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# Static UI mounting
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", tags=["UI"])
    def serve_ui():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Sahayta UI template under compilation."}
