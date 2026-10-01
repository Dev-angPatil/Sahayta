"""
src/sahayta/llm/gemini_client.py
Gemini 2.5 Flash LLM Client for Project Sahayta.
Provides contextual conversational dialogue, multilingual intent classification,
and canonical entity extraction for Indian civic grievance redressal.
"""

from __future__ import annotations
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger("sahayta.llm")

# Load environment variable from .env if present
def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception as e:
            logger.warning("Failed to parse .env file: %s", e)

_load_env_file()

DEFAULT_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_MODEL = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """You are Sahayta (सहायता), an autonomous, empathetic GovTech Action Agent for Bharat (India).
Your purpose is to help citizens resolve real-world civic grievances across Union (CPGRAMS, Railways, Banking, Telecom, EPFO, Post), State (PDS Ration Card, Food Supplies), and Local/Utility (DISCOM Electricity, Municipal Water Board) jurisdictions.

Key Capabilities:
1. Converse fluently in Hindi (Devanagari), Hinglish, or English depending on how the citizen speaks.
2. If the citizen gives a greeting, asks who you are, asks how Sahayta works, or asks general civic questions:
   - Provide a warm, clear, empathetic explanation.
   - Explain that you help them formulate an official administrative grievance under Article 350 of the Constitution of India, verify missing parameters, and prepare a live verifiable petition docket.
   - Invite them to explain their issue (e.g. ration dealer overcharging, train ticket refund delayed, electricity blackout, muddy tap water).
3. If the citizen describes a grievance or provides details:
   - Identify the primary domain (CPGRAMS, STATE_PDS, DISCOM_POWER, WATER_BOARD).
   - Extract all mentioned parameters accurately (names, phone numbers, email, addresses, districts, states, PIN codes, PNRs, Consumer Account numbers, Ration card numbers, Fair price shop IDs, electricity boards).
   - Generate an empathetic, reassuring conversational message acknowledging what they said and gently asking for any missing detail required for official cognizance.
4. Output strictly valid JSON matching the requested schema.
"""


class GeminiClient:
    """
    Client for interacting with Google Gemini 2.5 Flash API.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or DEFAULT_API_KEY
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def analyze_turn(
        self,
        message: str,
        current_domain: Optional[str] = None,
        collected_fields: Optional[Dict[str, Any]] = None,
        missing_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyzes a citizen utterance using Gemini 2.5 Flash.
        Returns structured analysis containing intent, domain, reply, and extracted entities.
        """
        if not self.is_available():
            return {}

        collected_str = json.dumps(collected_fields or {})
        missing_str = ", ".join(missing_fields or [])

        prompt = f"""Citizen Input: \"\"\"{message}\"\"\"

Current Session State:
- Active Domain: {current_domain or 'None (Unassigned)'}
- Already Collected Parameters: {collected_str}
- Pending Mandatory Parameters: {missing_str or 'None'}

Return a JSON object with this exact structure:
{{
  "intent": "GREETING_OR_INQUIRY" | "GRIEVANCE" | "ELICITATION_ANSWER" | "CONFIRMATION",
  "detected_domain": "CPGRAMS" | "STATE_PDS" | "DISCOM_POWER" | "WATER_BOARD" | null,
  "conversational_reply": "Empathetic, clear vernacular reply to the citizen in their language",
  "extracted_entities": {{
    "complainant_name": null,
    "mobile_number": null,
    "email": null,
    "address": null,
    "state": null,
    "district": null,
    "pincode": null,
    "ration_card_number": null,
    "fps_shop_id_or_name": null,
    "consumer_account_number": null,
    "meter_number": null,
    "utility_provider": null,
    "consumer_number": null,
    "water_board_name": null,
    "area_locality": null,
    "reference_number": null,
    "ministry_department": null,
    "grievance_category": null,
    "grievance_description": null
  }},
  "reasoning_summary": "1 concise sentence explaining the cognitive deduction"
}}
"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
            },
        }

        url = f"{self.base_url}?key={self.api_key}"
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
                        parsed = json.loads(raw_text)
                        # Clean out null entity values
                        if "extracted_entities" in parsed and isinstance(parsed["extracted_entities"], dict):
                            parsed["extracted_entities"] = {
                                k: v for k, v in parsed["extracted_entities"].items()
                                if v is not None and str(v).strip() != ""
                            }
                        return parsed
                else:
                    logger.warning("Gemini API call returned status %s: %s", resp.status_code, resp.text[:200])
        except Exception as exc:
            logger.warning("Gemini API execution error: %s", exc)

        return {}


# Module-level singleton
_client_instance: Optional[GeminiClient] = None

def get_gemini_client() -> GeminiClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = GeminiClient()
    return _client_instance
