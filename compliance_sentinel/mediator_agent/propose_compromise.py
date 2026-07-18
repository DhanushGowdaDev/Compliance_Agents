"""
propose_compromise.py — Mediator Agent Tool
Triggered when a clause is Red-rated and a buyer redline exists.
Calls NIM to generate 1-2 negotiation compromise options.
"""
from __future__ import annotations

import json
import os
import re
import time
from openai import OpenAI

_SYSTEM = """You are a neutral commercial contract mediator specialising in SaaS DPAs.
Your job is to propose compromise language between a Vendor's original position
and a Buyer's desired redline for a Data Processing Agreement clause.

Identify each party's UNDERLYING INTEREST (not just stated position) and
propose 1-2 compromise options that partially satisfy both.

Return ONLY a valid JSON array (no markdown fences, no prose):
[
  {
    "clause_id": "<id>",
    "compromise_text": "<full rewritten clause text>",
    "buyer_risk_reduction": <1-5>,
    "vendor_effort_cost": <1-5>,
    "deal_speed_score": <1-5>,
    "rationale": "<one sentence explaining the balance>"
  }
]

Scoring:
- buyer_risk_reduction: 5=fully eliminates buyer risk, 1=minimal improvement
- vendor_effort_cost: 5=low cost/easy for vendor, 1=very burdensome
- deal_speed_score: 5=very likely to close negotiation, 1=will cause further back-and-forth"""


def _client() -> tuple[OpenAI, str]:
    key = os.environ.get("NIM_API_KEY")
    if not key:
        raise EnvironmentError("NIM_API_KEY not set")
    base = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1/")
    model = os.environ.get("DEFAULT_MODEL", "meta/llama-3.3-70b-instruct")
    return OpenAI(api_key=key, base_url=base), model


def propose_compromise(
    clause_id: str,
    clause_text: str,
    suggested_redline: str,
    rule_id: str,
    agent_name: str,
    reason: str,
) -> list[dict]:
    """
    Generate compromise options between vendor's clause and buyer's redline.

    Args:
        clause_id: Clause identifier.
        clause_text: Vendor's original clause text.
        suggested_redline: Buyer's desired language (from redline_generator).
        rule_id: The compliance rule that triggered the conflict.
        agent_name: Which specialist agent flagged this.
        reason: One-line reason for the flag.

    Returns:
        List of 1-2 compromise option dicts.
    """
    try:
        client, model = _client()
    except EnvironmentError:
        return _fallback(clause_id)

    prompt = (
        f"clause_id: {clause_id}\n"
        f"compliance_rule: {rule_id} ({agent_name})\n"
        f"issue: {reason}\n\n"
        f"VENDOR ORIGINAL POSITION:\n{clause_text}\n\n"
        f"BUYER DESIRED REDLINE:\n{suggested_redline}"
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
                temperature=0.3,
                max_tokens=2048,
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
        return _fallback(clause_id)

    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        options = json.loads(raw)
    except json.JSONDecodeError:
        try:
            options = json.loads(raw + '"}]')
        except json.JSONDecodeError:
            try:
                options = json.loads(raw + '}]')
            except json.JSONDecodeError:
                return _fallback(clause_id)

    if isinstance(options, dict):
        options = [options]
    for opt in options:
        opt.setdefault("clause_id", clause_id)
        opt.setdefault("compromise_text", "")
        opt.setdefault("buyer_risk_reduction", 3)
        opt.setdefault("vendor_effort_cost", 3)
        opt.setdefault("deal_speed_score", 3)
        opt.setdefault("rationale", "")
    return options[:2]


def _fallback(clause_id: str) -> list[dict]:
    return [{
        "clause_id": clause_id,
        "compromise_text": "[Compromise unavailable — review manually]",
        "buyer_risk_reduction": 0,
        "vendor_effort_cost": 0,
        "deal_speed_score": 0,
        "rationale": "Mediator call failed — manual review required.",
    }]


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    result = propose_compromise(
        clause_id="5",
        clause_text="Client shall indemnify Vendor without any cap on liability.",
        suggested_redline="Each party's aggregate liability is capped at 12 months' fees paid in the prior year.",
        rule_id="R1", agent_name="legal_agent",
        reason="Uncapped one-sided indemnification.",
    )
    print(json.dumps(result, indent=2))
