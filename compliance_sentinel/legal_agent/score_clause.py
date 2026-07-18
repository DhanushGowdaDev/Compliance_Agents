"""
score_clause.py — Legal Agent Tool
Calls NVIDIA NIM (OpenAI-compatible) with clause text + embedded legal rules.
Returns strict JSON: {clause_id, agent, rating, rule_id, reason}
"""
from __future__ import annotations

import json
import os
import re
import time

from openai import OpenAI  # type: ignore

# ---------------------------------------------------------------------------
# Rules (verbatim from spec)
# ---------------------------------------------------------------------------
_RULES = """
R1 — Indemnification Scope:
  Indemnification clause must define scope, cap, and exceptions; unlimited/uncapped
  liability for one party = Red.

R2 — Limitation of Liability:
  Limitation of liability clause must exist and be mutual; one-sided or absent = Red.

R3 — Termination:
  Termination clause must specify notice period AND cure period for breach;
  missing cure period = Amber.

R4 — Governing Law / Jurisdiction:
  Governing law/jurisdiction clause must be explicit; absent = Amber.

R5 — Force Majeure:
  Force majeure clause should exist and not be overly broad; missing = Amber.

R6 — Assignment:
  Assignment clause should require consent for assignment; silent/unrestricted
  assignment = Amber.
""".strip()

_SYSTEM_PROMPT = f"""You are the Legal Agent in the Compliance Sentinel contract risk-scoring swarm.
Evaluate the contract clause provided by the user against the following rules:

{_RULES}

Instructions:
- Return ONLY valid JSON — no markdown fences, no prose, no commentary.
- Rate the clause Red, Amber, or Green based on the highest-risk rule triggered.
- If no rule applies, return Green with rule_id "N/A".
- The "reason" field must be exactly one sentence that quotes or directly references
  the actual clause text. Never hallucinate clause language.
- Never cite a rule not in the list above.

Output schema (return ONLY this JSON, nothing else):
{{
  "clause_id": "<the clause_id passed in>",
  "agent": "legal_agent",
  "rating": "Red|Amber|Green",
  "rule_id": "R1|R2|R3|R4|R5|R6|N/A",
  "reason": "<one sentence grounded in clause text>"
}}"""


def _get_client() -> tuple[OpenAI, str]:
    """Return (client, model_name) reading from environment."""
    api_key = os.environ.get("NIM_API_KEY")
    if not api_key:
        raise EnvironmentError("NIM_API_KEY not set. Add it to .env")
    base_url = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    model = os.environ.get("DEFAULT_MODEL", "nvidia/llama-3.3-70b-instruct")
    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model


def score_clause(clause_id: str, clause_text: str) -> dict:
    """
    Score a contract clause for legal risk using NVIDIA NIM.

    Args:
        clause_id: The clause identifier (e.g. "1", "2.1", "Section 3").
        clause_text: The full text of the clause.

    Returns:
        dict with keys: clause_id, agent, rating, rule_id, reason.
    """
    client, model = _get_client()

    user_message = (
        f"clause_id: {clause_id}\n\n"
        f"Clause text:\n{clause_text}"
    )

    # Retry up to 3 times with exponential backoff on rate-limit errors
    _retry_delays = [5, 15, 30]
    last_exc: Exception | None = None
    raw = ""

    for attempt, delay in enumerate([0] + _retry_delays, start=1):
        if delay:
            time.sleep(delay)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.0,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content.strip()
            last_exc = None
            break
        except Exception as exc:
            last_exc = exc
            err = str(exc)
            if ("429" in err or "rate" in err.lower()) and attempt <= len(_retry_delays):
                continue  # wait and retry
            raise

    if last_exc is not None:
        raise last_exc

    # Strip markdown fences if the model wraps output anyway
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Try a basic repair for truncated JSON
        try:
            result = json.loads(raw + '"}')
        except json.JSONDecodeError:
            try:
                result = json.loads(raw + '}')
            except json.JSONDecodeError:
                return {
                    "clause_id": clause_id,
                    "agent": "legal_agent",
                    "rating": "Amber",
                    "rule_id": "N/A",
                    "reason": "The local LLM returned an incomplete JSON response due to token limit or formatting issues. Try using a larger model or check the prompt.",
                }

    result.setdefault("clause_id", clause_id)
    result.setdefault("agent", "legal_agent")
    result.setdefault("rating", "Green")
    result.setdefault("rule_id", "N/A")
    result.setdefault("reason", "")
    return result


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
    if len(sys.argv) < 3:
        print("Usage: python score_clause.py <clause_id> <clause_text>")
        sys.exit(1)
    out = score_clause(sys.argv[1], sys.argv[2])
    print(json.dumps(out, indent=2))
