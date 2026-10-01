"""
src/sahayta/aikart_runner.py
Official aiKart "Try Me Now" Sandbox Headless Runner.
Conforms strictly to aikart.dev/v1 specification:
- Reads /aikart/input.json or AIKART_INPUT environment variable.
- Executes full agentic workflow (Gate 0 -> Governance Router -> Evidentiary Elicitation -> Article 350 Petition -> Cryptographic Receipt).
- Writes { "format": "markdown", "response": "..." } to /aikart/output.json.
- Exits with return code 0.
"""

from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from sahayta.agent import SahaytaAgent
from sahayta.drafting.letter_synthesizer import synthesize_administrative_letter
from sahayta.drafting.submission_engine import submit_grievance_payload


def load_aikart_input() -> Dict[str, Any]:
    """Loads input payload from /aikart/input.json or AIKART_INPUT env var."""
    # 1. Check /aikart/input.json
    aikart_path = Path("/aikart/input.json")
    if aikart_path.exists():
        try:
            with open(aikart_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed reading /aikart/input.json: {e}\n")

    # 2. Check environment variable AIKART_INPUT
    env_input = os.environ.get("AIKART_INPUT")
    if env_input:
        try:
            return json.loads(env_input)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed parsing AIKART_INPUT env: {e}\n")

    # 3. Fallback to stdin if piped
    if not sys.stdin.isatty():
        try:
            content = sys.stdin.read().strip()
            if content:
                return json.loads(content)
        except Exception:
            pass

    # Default fallback demonstration complaint
    return {
        "complaint": "Train 12952 refund of Rs 2450 delayed for 16 days. PNR 2490182910. Complainant Ramesh Sharma, mobile 9876543210, email ramesh@gmail.com, living at Sector 14 Rohini Delhi 110085.",
        "language": "English"
    }


def write_aikart_output(markdown_content: str) -> None:
    """Writes JSON payload to /aikart/output.json (or fallback /tmp/aikart/output.json)."""
    output_payload = {
        "format": "markdown",
        "response": markdown_content
    }

    target_paths = [
        Path("/aikart/output.json"),
        Path("/tmp/aikart_output.json"),
        Path("aikart_output.json")
    ]

    written = False
    for p in target_paths:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(output_payload, f, indent=2, ensure_ascii=False)
            written = True
            break
        except Exception:
            continue

    if not written:
        # Final fallback: stdout json
        print(json.dumps(output_payload))


def run() -> int:
    """Main execution loop for aiKart sandbox."""
    data = load_aikart_input()
    complaint = data.get("complaint") or data.get("message") or ""
    language = data.get("language", "English")

    if not complaint.strip():
        md = "### Sahayta GovTech Agent\n\nNo complaint text provided in `/aikart/input.json`."
        write_aikart_output(md)
        return 0

    agent = SahaytaAgent()
    result = agent.chat(complaint)

    # Format Markdown Output
    lines = []
    lines.append("# Sahayta — Autonomous GovTech Civic Action Agent")
    lines.append("*Impact for Bharat • Powered by aiKart Agentic Platform*\n")

    # Rejection Handling
    if result.get("status") == "REJECTED":
        lines.append("## 🚫 Gate 0 Security & Fraud Guardrail Notice")
        lines.append(f"**Status:** `REJECTED (HTTP 422)`")
        lines.append(f"**Flagged Entity:** `{result.get('rejected_entity')}`")
        lines.append(f"**Rejection Code:** `{result.get('rejection_code')}`")
        lines.append(f"\n> **Advisory:** {result.get('agent_message')}")
        lines.append(f"\n**Legitimate Statutory Redressal:** {result.get('official_advice')}")
        write_aikart_output("\n".join(lines))
        return 0

    # 1. Cognitive Reasoning Trace
    lines.append("## 1. 🧠 Agent Reasoning & Governance Resolution")
    trace = result.get("reasoning_trace", [])
    for step in trace:
        lines.append(f"- {step}")

    # 2. Autonomous Tools Executed
    tools = result.get("tools_executed", [])
    if tools:
        lines.append("\n## 2. 🛠️ Autonomous Tools Executed")
        for tool in tools:
            lines.append(f"- `{tool}`")

    # 3. Grounded Governance Data
    grounded = result.get("grounded_data", {})
    if grounded:
        lines.append("\n## 3. 📊 Grounded Administrative Jurisdiction")
        lines.append(f"| Governance Layer | Resolved Value |")
        lines.append(f"|---|---|")
        lines.append(f"| **Sovereign Tier** | {grounded.get('sovereign_tier', '-')} |")
        lines.append(f"| **Competent Authority** | {grounded.get('ministry_or_department', '-')} |")
        lines.append(f"| **Nodal Operational Entity** | {grounded.get('nodal_entity', '-')} |")
        lines.append(f"| **Governing Statute** | {grounded.get('statutory_act', '-')} |")
        lines.append(f"| **Statutory SLA** | **{grounded.get('standard_sla_days', 30)} Days** |")
        lines.append(f"| **Appellate Body** | {grounded.get('escalation_avenue', '-')} |")

    # 4. Formal Petition Draft (Article 350 Standard)
    draft = result.get("draft")
    if not draft and agent.state.collected_fields:
        # Synthesize on the fly for sandbox display
        try:
            draft = synthesize_administrative_letter(
                schema_id=agent.state.schema_id or "GOVTECH_CPGRAMS_V1",
                fields=agent.state.collected_fields,
                lang=agent.state.language,
            )
        except Exception:
            draft = None

    if draft:
        lines.append("\n## 4. 📝 Formal Administrative Petition (Article 350 Standards)")
        lines.append(f"```text\n{draft.full_letter_text}\n```")

    # 5. Missing Fields if Eliciting
    missing = result.get("missing_fields", [])
    if missing:
        lines.append("\n## ⚠️ Missing Evidentiary Parameters")
        lines.append(f"The target administrative body requires the following additional fields before official lodgement:")
        for m in missing:
            lines.append(f"- `{m}`")
        lines.append(f"\n**Next Question to Citizen:** *\"{result.get('agent_message')}\"*")
    else:
        # Mint receipt for final demonstration
        try:
            receipt = agent.submit(citizen_confirmation=True)
            lines.append("\n## 5. 🔐 Official Verifiable Filing Docket")
            lines.append(f"- **Tracking Reference Number:** `{receipt['tracking_number']}`")
            lines.append(f"- **Filing Timestamp (UTC):** `{receipt['submission_timestamp_utc']}`")
            lines.append(f"- **Statutory Redressal Deadline:** **{receipt['resolution_deadline_utc']}**")
            lines.append(f"- **Tamper-Evident SHA-256 Hash:** `{receipt['tamper_evident_hash']}`")
            lines.append(f"\n> **Citizen Actionable Advice:** {receipt['advice_to_citizen']}")
        except Exception as e:
            lines.append(f"\n*Receipt Generation Note: {e}*")

    write_aikart_output("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(run())
