"""
src/sahayta/triage/language.py
High-precision script and vernacular detection for Indian civic complaints:
- English ('en', 'latin')
- Hindi in Devanagari script ('hi', 'devanagari')
- Hinglish code-mixed in Latin script ('hi-Latn', 'hinglish')
"""

from __future__ import annotations
import re
from typing import Tuple

# Devanagari Unicode Block: U+0900 to U+097F
DEVANAGARI_START = "\u0900"
DEVANAGARI_END = "\u097F"

# Pure Indic grammatical particles, pronouns, auxiliaries, and civic verbs (Latin script).
# Shared English words like 'ration', 'card', 'bill', 'meter', 'court' are strictly excluded
# to avoid false-positive Hinglish classifications on standard Indian English complaints.
PURE_HINGLISH_MARKERS = {
    # Auxiliaries & Copulas
    "hai", "hain", "tha", "thi", "the", "nahi", "nhi", "nahe", "mat",
    "raha", "rahi", "rahe", "kar", "kare", "karo", "karein", "karna", "kiya",
    "hoga", "hogi", "hoge", "hua", "hui", "hue", "gaya", "gayi", "gaye",
    "aaya", "aayi", "aaye", "diya", "diye", "liya", "liye", "batao", "batayein",
    "bataiye", "kijiye", "kardo", "kariye", "sunwai", "fas",
    
    # Pronouns & Demonstratives
    "mera", "meri", "mere", "mujhe", "mujhko", "hum", "humara", "humare", "humari",
    "aap", "aapka", "aapke", "aapki", "tum", "tumhara", "tumhe",
    "yeh", "ye", "voh", "woh", "wo", "iska", "iske", "iski", "uska", "uske", "uski",
    "inhe", "unhe", "unka", "unke", "unki", "koi", "kuch",
    "kya", "kyu", "kyun", "kaise", "kab", "kaha", "kahan", "kaun", "kitna", "kitni", "kitne",
    
    # Prepositions / Postpositions / Conjunctions
    "se", "ko", "me", "mein", "par", "pe", "ke", "ka", "ki", "bhi", "tak", "aur", "ya", "lekin", "magar",
    
    # Vernacular Civic Nouns / Adjectives
    "bijli", "paani", "pani", "gehu", "chawal", "rashan", "kotedar", "dukan", "bhandar",
    "pichle", "din", "mahina", "mahine", "mahino", "tarikh", "kripya", "kirpya",
    "shikayat", "sahab", "adhikari", "samasya", "pareshani", "dikkat", "kharaab",
    "kharab", "band", "katoti", "ganda", "badbu", "nal", "paisa", "rupaye",
    "bohot", "bahut", "zyada", "jyada", "kam", "phuk", "fus", "chori", "jana", "de"
}


def detect_language_and_script(text: str) -> Tuple[str, str]:
    """
    Analyzes citizen complaint text and returns a tuple of (language_code, script_name):
    - ('hi', 'devanagari'): Hindi text written in Devanagari script
    - ('hi-Latn', 'hinglish'): Code-mixed Indic text written in Latin script
    - ('en', 'latin'): Standard Indian or Global English text
    """
    if not text or not text.strip():
        return ("en", "latin")

    # 1. Unicode Devanagari Block Inspection
    devanagari_chars = sum(1 for c in text if DEVANAGARI_START <= c <= DEVANAGARI_END)
    alpha_chars = sum(1 for c in text if c.isalpha())

    if devanagari_chars >= 3 or (alpha_chars > 0 and (devanagari_chars / alpha_chars) >= 0.15):
        return ("hi", "devanagari")

    # 2. Latin-script Hinglish Lexical Analysis
    raw_tokens = text.split()
    normalized_words = [re.sub(r"[^a-zA-Z]", "", w).lower() for w in raw_tokens]
    valid_words = [w for w in normalized_words if len(w) > 0]

    if not valid_words:
        return ("en", "latin")

    hinglish_hits = sum(1 for w in valid_words if w in PURE_HINGLISH_MARKERS)
    ratio = hinglish_hits / len(valid_words)

    if (len(valid_words) <= 3 and hinglish_hits >= 1) or hinglish_hits >= 2 or ratio >= 0.08:
        return ("hi-Latn", "hinglish")

    return ("en", "latin")


def detect_script_and_lang(text: str) -> Tuple[str, str]:
    """Alias for detect_language_and_script to match test calls."""
    return detect_language_and_script(text)
