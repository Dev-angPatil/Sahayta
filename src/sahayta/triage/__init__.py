"""
src/sahayta/triage/__init__.py
Multilingual Triage, Gate 0 Rejection, and Entity Extraction.
"""

from sahayta.triage.language import detect_language_and_script, detect_script_and_lang
from sahayta.triage.fake_detector import check_gate_zero, check_rejections
from sahayta.triage.classifier import classify_domain, extract_entities, triage_request

__all__ = [
    "detect_language_and_script",
    "detect_script_and_lang",
    "check_gate_zero",
    "check_rejections",
    "classify_domain",
    "extract_entities",
    "triage_request",
]
