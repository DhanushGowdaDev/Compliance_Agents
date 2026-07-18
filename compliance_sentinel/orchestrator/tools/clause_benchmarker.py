"""
clause_benchmarker.py — Orchestrator Tool
Compares each clause against ~18 embedded market-standard DPA clause examples.
Fully offline — no LLM call required.
Output: {"clause_id": str, "benchmark_verdict": "aggressive"|"standard"|"lenient",
          "comparison_note": str, "area": str}
"""
from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Embedded market-standard DPA clause library (~18 entries)
# Each entry: area, standard signals, aggressive signals, lenient signals
# ---------------------------------------------------------------------------
_LIBRARY: list[dict] = [
    {
        "area": "subprocessor_notice",
        "keywords": ["subprocessor", "sub-processor", "third party processor", "subcontractor"],
        "standard": ["30 days", "prior written notice", "right to object", "list of subprocessors"],
        "aggressive": ["without notice", "no prior notice", "sole discretion", "at any time without"],
        "lenient": ["60 days notice", "controller written consent required", "prior approval", "written consent before"],
        "standard_note": "Market standard requires 30-day prior notice with right to object (GDPR Art. 28(2)).",
    },
    {
        "area": "breach_notification",
        "keywords": ["breach", "security incident", "data breach", "personal data breach", "unauthorized access"],
        "standard": ["72 hours", "without undue delay", "competent supervisory authority", "notify controller"],
        "aggressive": ["commercially reasonable time", "30 days", "no obligation to notify", "best efforts"],
        "lenient": ["24 hours", "48 hours", "immediately upon", "within one business day"],
        "standard_note": "Market standard is 72-hour notification per GDPR Art. 33.",
    },
    {
        "area": "liability_cap",
        "keywords": ["liability", "indemnif", "limitation", "aggregate", "cap", "damages"],
        "standard": ["twelve months", "12 months", "fees paid", "mutual limitation", "both parties"],
        "aggressive": ["unlimited liability", "no cap", "uncapped", "shall not limit", "sole liability on"],
        "lenient": ["three months", "3 months", "lesser of", "de minimis", "minimum liability"],
        "standard_note": "Market standard caps mutual liability at 12 months' fees paid.",
    },
    {
        "area": "data_retention",
        "keywords": ["retain", "retention", "deletion", "destroy", "return data", "erasure"],
        "standard": ["90 days", "30 days after termination", "upon request", "certify deletion"],
        "aggressive": ["as required by law", "commercially reasonable", "indefinitely", "no obligation to delete"],
        "lenient": ["immediately upon termination", "within 7 days", "real-time deletion"],
        "standard_note": "Market standard: delete/return data within 30-90 days of termination with written certification.",
    },
    {
        "area": "cross_border_transfer",
        "keywords": ["transfer", "cross-border", "international transfer", "third country", "adequacy"],
        "standard": ["standard contractual clauses", "SCC", "adequacy decision", "binding corporate rules", "BCR"],
        "aggressive": ["no transfer restriction", "vendor may transfer", "without restriction", "global processing"],
        "lenient": ["data localisation", "no transfer permitted", "EU-only processing"],
        "standard_note": "Market standard cites SCCs or adequacy decision for cross-border transfers (GDPR Ch. V).",
    },
    {
        "area": "audit_rights",
        "keywords": ["audit", "inspection", "assessment", "right to audit", "third-party audit"],
        "standard": ["annual audit", "30 days notice", "reasonable notice", "third-party auditor", "SOC 2"],
        "aggressive": ["no audit rights", "vendor discretion", "audit at vendor's sole", "no inspection"],
        "lenient": ["audit at any time", "unrestricted audit", "immediate access", "without notice"],
        "standard_note": "Market standard grants annual audit right with 30-day notice, or acceptance of SOC 2/ISO 27001.",
    },
    {
        "area": "termination_for_breach",
        "keywords": ["terminat", "notice period", "cure period", "for cause", "material breach"],
        "standard": ["30 days notice", "cure period", "material breach", "written notice"],
        "aggressive": ["immediate termination", "no cure period", "terminate without notice", "at any time"],
        "lenient": ["90 days cure", "60 days notice", "cure within 60"],
        "standard_note": "Market standard: 30-day written notice with cure period for material breach.",
    },
    {
        "area": "sla_uptime",
        "keywords": ["uptime", "availability", "SLA", "service level", "response time"],
        "standard": ["99.9%", "99.5%", "service credit", "response time", "measurable metric"],
        "aggressive": ["best efforts", "commercially reasonable", "no SLA", "no uptime guarantee"],
        "lenient": ["99.99%", "five nines", "zero downtime", "100% availability"],
        "standard_note": "Market standard SLA is 99.9% monthly uptime with defined service credits.",
    },
    {
        "area": "security_measures",
        "keywords": ["security", "encryption", "access control", "monitoring", "penetration test"],
        "standard": ["encryption at rest", "encryption in transit", "access control", "annual penetration", "SOC 2"],
        "aggressive": ["commercially reasonable", "industry standard", "appropriate measures", "reasonable efforts"],
        "lenient": ["military grade", "quantum encryption", "air-gapped", "zero trust architecture required"],
        "standard_note": "Market standard specifies encryption, access control, monitoring, annual pen testing.",
    },
    {
        "area": "ccpa_service_provider",
        "keywords": ["service provider", "business purpose", "sell", "share", "personal information", "CCPA"],
        "standard": ["service provider", "business purpose only", "shall not sell", "shall not share", "CCPA"],
        "aggressive": ["may use data", "no restriction on use", "vendor's discretion", "no CCPA designation"],
        "lenient": ["contractor", "strict no-use obligation", "data isolation required"],
        "standard_note": "Market standard explicitly designates vendor as CCPA Service Provider with no-sell certification.",
    },
    {
        "area": "governing_law",
        "keywords": ["governing law", "jurisdiction", "applicable law", "dispute resolution"],
        "standard": ["courts of", "jurisdiction of", "governing law shall be", "arbitration"],
        "aggressive": ["vendor's sole discretion", "no governing law", "vendor's home jurisdiction"],
        "lenient": ["buyer's jurisdiction", "mutual agreement", "international arbitration"],
        "standard_note": "Market standard specifies explicit governing law and jurisdiction for dispute resolution.",
    },
    {
        "area": "force_majeure",
        "keywords": ["force majeure", "act of god", "pandemic", "beyond reasonable control", "extraordinary"],
        "standard": ["beyond reasonable control", "acts of government", "natural disaster", "defined list"],
        "aggressive": ["any event vendor deems", "sole discretion", "including market conditions", "broad discretion"],
        "lenient": ["strictly defined", "physical destruction only", "no force majeure"],
        "standard_note": "Market standard force majeure covers specifically enumerated events, not broad discretion.",
    },
    {
        "area": "assignment",
        "keywords": ["assign", "assignment", "transfer rights", "successor", "change of control"],
        "standard": ["consent required", "prior written consent", "not to be unreasonably withheld", "change of control"],
        "aggressive": ["either party may assign", "without consent", "unrestricted assignment"],
        "lenient": ["assignment prohibited", "no assignment permitted without court order"],
        "standard_note": "Market standard requires prior written consent for assignment, with carveout for corporate restructuring.",
    },
    {
        "area": "payment_terms",
        "keywords": ["payment", "invoice", "due", "net 30", "net 60", "currency", "fees"],
        "standard": ["net 30", "net 60", "USD", "30 days after invoice", "specific currency"],
        "aggressive": ["immediately due", "due upon demand", "vendor's discretion", "no defined currency"],
        "lenient": ["net 90", "net 120", "buyer's preferred currency"],
        "standard_note": "Market standard specifies Net-30/60 payment terms in a defined currency.",
    },
    {
        "area": "price_escalation",
        "keywords": ["price", "fee", "rate", "escalation", "increase", "change pricing"],
        "standard": ["CPI", "index-tied", "annual cap", "not to exceed", "maximum increase"],
        "aggressive": ["at any time", "sole discretion", "without limit", "unrestricted", "any amount"],
        "lenient": ["price locked", "no increases", "fixed for term"],
        "standard_note": "Market standard caps price increases at CPI or a fixed annual percentage.",
    },
    {
        "area": "auto_renewal",
        "keywords": ["auto-renew", "automatic renewal", "renew", "opt-out", "non-renewal"],
        "standard": ["60 days notice", "30 days notice", "opt-out period", "written notice to cancel"],
        "aggressive": ["automatically renews", "silent renewal", "no opt-out specified", "unless terminated"],
        "lenient": ["180 days notice", "no auto-renewal", "explicit consent required"],
        "standard_note": "Market standard requires 30-60 day opt-out window before auto-renewal activates.",
    },
    {
        "area": "liquidated_damages",
        "keywords": ["liquidated damages", "penalty", "damages clause", "pre-estimated loss"],
        "standard": ["proportionate", "genuine pre-estimate", "reasonable estimate", "capped at"],
        "aggressive": ["multiple of annual", "unlimited penalty", "disproportionate", "punitive"],
        "lenient": ["nominal damages", "de minimis", "no damages clause"],
        "standard_note": "Market standard liquidated damages must be a genuine pre-estimate of loss, not punitive.",
    },
    {
        "area": "data_subject_rights",
        "keywords": ["data subject", "access request", "erasure", "rectification", "portability", "DSAR"],
        "standard": ["assist controller", "30 days", "reasonable assistance", "data subject request"],
        "aggressive": ["vendor's discretion", "no obligation to assist", "commercially reasonable"],
        "lenient": ["immediate response", "24 hours", "dedicated DSAR team required"],
        "standard_note": "Market standard requires vendor assistance with DSARs within 30 days (GDPR Art. 12).",
    },
]

# ---------------------------------------------------------------------------
# Benchmarking logic
# ---------------------------------------------------------------------------

def _detect_area(clause_text: str) -> list[dict]:
    """Return all library entries whose keywords appear in the clause."""
    text_lower = clause_text.lower()
    matches = []
    for entry in _LIBRARY:
        if any(kw.lower() in text_lower for kw in entry["keywords"]):
            matches.append(entry)
    return matches


def _score_text(clause_lower: str, signals: list[str]) -> int:
    return sum(1 for s in signals if s.lower() in clause_lower)


def benchmark_clause(clause_id: str, clause_text: str) -> dict[str, Any]:
    """
    Compare a clause against the embedded DPA standard library.

    Returns:
        {
          "clause_id": str,
          "area": str,
          "benchmark_verdict": "aggressive"|"standard"|"lenient"|"not_applicable",
          "comparison_note": str,
        }
    """
    text_lower = clause_text.lower()
    matches = _detect_area(clause_text)

    if not matches:
        return {
            "clause_id": clause_id,
            "area": "general",
            "benchmark_verdict": "not_applicable",
            "comparison_note": "Clause does not correspond to any monitored DPA provision area.",
        }

    # Use the first (most relevant) match
    entry = matches[0]
    area = entry["area"]

    agg_score  = _score_text(text_lower, entry["aggressive"])
    std_score  = _score_text(text_lower, entry["standard"])
    len_score  = _score_text(text_lower, entry["lenient"])

    if agg_score > std_score and agg_score >= len_score:
        verdict = "aggressive"
        note = (
            f"Clause contains vendor-favourable language "
            f"({', '.join(s for s in entry['aggressive'] if s.lower() in text_lower)}). "
            f"{entry['standard_note']}"
        )
    elif len_score > std_score and len_score > agg_score:
        verdict = "lenient"
        note = (
            f"Clause contains buyer-favourable / overly strict language. "
            f"{entry['standard_note']}"
        )
    else:
        verdict = "standard"
        note = (
            f"Clause aligns with market practice for {area.replace('_', ' ')}. "
            f"{entry['standard_note']}"
        )

    return {
        "clause_id": clause_id,
        "area": area,
        "benchmark_verdict": verdict,
        "comparison_note": note,
    }


if __name__ == "__main__":
    import json, sys
    text = sys.argv[1] if len(sys.argv) > 1 else "Vendor may transfer data internationally without restriction."
    print(json.dumps(benchmark_clause("test", text), indent=2))
