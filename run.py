#!/usr/bin/env python3
"""
run.py — Universal aiKart Sandbox Entrypoint for Sahayta.
Conforms to aiKart v1 specification:
- Reads /aikart/input.json or AIKART_INPUT env var
- Executes Sahayta GovTech triage, elicitation, Article 350 drafting & SHA-256 notary
- Writes /aikart/output.json
- Exits 0 on success
"""

import sys
from sahayta.aikart_runner import run

if __name__ == "__main__":
    sys.exit(run())
