"""
redline_generator.py — Orchestrator Tool
For every clause rated Red or Amber, calls NIM to generate a concrete fallback rewrite.
Output: {"clause_id": str, "original_text": str, "suggested_redline": str, "rule_id_addressed": str}
"""
from __future__ import annotations

import json
import os
import re
import time
from openai import OpenAI

_SYSTEM = """You are a senior data privacy and commercial contracts lawyer specialising in
SaaS Vendor Data Processing Agreements (DPAs) under GDPR and CCPA/CPRA.

Given a non-compliant contract clause and the rule it violates, rewrite the clause
to fix the specific compliance issue while keeping the commercial intent intact.

Return ONLY valid JSON (no markdown fences, no prose):
{
  "clause_id": "<the clause_id passed in>",
  "original_text": "<first 120 chars of original>",
  "suggested_redline": "<complete rewritten clause — market-standard, enforceable>",
  "rule_id_addressed": "<rule id that triggered the redline>"
}"""


def _client() -> tuple[OpenAI, str]:
    key = os.environ.get("NIM_API_KEY")
    if not key:
        raise EnvironmentError("NIM_API_KEY not set")
    base = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1/")
    model = os.environ.get("DEFAULT_MODEL", "meta/llama-3.3-70b-instruct")
    return OpenAI(api_key=key, base_url=base), model


def generate_redline(
    clause_id: str,
    clause_text: str,
    rule_id: str,
    agent_name: str,
    reason: str,
) -> dict:
    """Generate a suggested redline for a non-compliant clause."""
    try:
        client, model = _client()
    except EnvironmentError:
        return _fallback(clause_id, clause_text, rule_id)

    prompt = (
        f"clause_id: {clause_id}\n"
        f"rule_violated: {rule_id} ({agent_name})\n"
        f"reason_flagged: {reason}\n\n"
        f"Original clause text:\n{clause_text}"
    )

    delays = [0, 5, 15]
    last_exc: Exception | None = None
    raw = ""
    for attempt, delay in enumerate(delays, 1):
        if delay:
            time.sleep(delay)
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": _SYSTEM},
                          {"role": "user",   "content": prompt}],
                temperature=0.2,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            raw = resp.choices[0].message.content.strip()
            last_exc = None
            break
        except Exception as exc:
            last_exc = exc
            if ("429" in str(exc) or "rate" in str(exc).lower()) and attempt < len(delays):
                continue
            break

    if last_exc or not raw:
        return _fallback(clause_id, clause_text, rule_id)

    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        try:
            result = json.loads(raw + '"}')
        except json.JSONDecodeError:
            try:
                result = json.loads(raw + '}')
            except json.JSONDecodeError:
                return _fallback(clause_id, clause_text, rule_id, raw)

    result.setdefault("clause_id", clause_id)
    result.setdefault("original_text", clause_text[:120])
    result.setdefault("suggested_redline", "")
    result.setdefault("rule_id_addressed", rule_id)
    return result


def _fallback(clause_id, clause_text, rule_id, raw="") -> dict:
    return {
        "clause_id": clause_id,
        "original_text": clause_text[:120],
        "suggested_redline": f"[Redline unavailable — review {rule_id} manually. Raw: {raw[:100]}]",
        "rule_id_addressed": rule_id,
    }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import sys
    result = generate_redline(
        clause_id="5",
        clause_text=sys.argv[1] if len(sys.argv) > 1 else "Client shall indemnify Vendor without any cap.",
        rule_id="R1",
        agent_name="legal_agent",
        reason="Unlimited/uncapped indemnification.",
    )
    print(json.dumps(result, indent=2))
