"""
swarm.py — Compliance Sentinel Swarm (v2)
Orchestrates: PDF extract → clause split → parallel agent scoring
            → benchmarking → redline generation → mediation → aggregation
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

_HERE = Path(__file__).parent
load_dotenv(_HERE / ".env")
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# --- Orchestrator tools
from orchestrator.pdf_extractor   import extract_text
from orchestrator.clause_splitter import split_clauses
from orchestrator.aggregator      import aggregate
from orchestrator.tools.clause_benchmarker import benchmark_clause
from orchestrator.tools.redline_generator  import generate_redline
from orchestrator.tools.audit_logger       import (
    log_rating, log_redline, log_benchmark, log_compromise, get_audit_trail
)

# --- Specialist agents
from legal_agent.score_clause          import score_clause as legal_score
from data_privacy_agent.score_clause   import score_clause as privacy_score
from commercial_agent.score_clause     import score_clause as commercial_score

# --- Mediator
from mediator_agent.propose_compromise import propose_compromise

# ---------------------------------------------------------------------------
AGENTS = {
    "orchestrator":       {"role": "Orchestrator"},
    "legal_agent":        {"role": "Legal risk",        "scorer": legal_score},
    "data_privacy_agent": {"role": "Data privacy",      "scorer": privacy_score},
    "commercial_agent":   {"role": "Commercial/SLA",    "scorer": commercial_score},
}
SPECIALIST_AGENTS = ["legal_agent", "data_privacy_agent", "commercial_agent"]

_DB = _HERE / "output" / "audit.db"


# ---------------------------------------------------------------------------
def _score(agent: str, clause: dict) -> dict:
    return AGENTS[agent]["scorer"](clause["id"], clause["text"])


def run_swarm(
    pdf_path: str,
    output_dir: str = "output",
    contract_id: str = "contract",
    sequential: bool = False,
    delay_seconds: float = 0.0,
) -> dict[str, Any]:
    """
    Full DPA analysis pipeline.

    Steps:
      1. Extract PDF text
      2. Split into clauses
      3. Parallel fan-out to legal / data_privacy / commercial agents
      4. Benchmark every clause (offline, no LLM)
      5. Generate redlines for Red/Amber clauses (LLM)
      6. Mediate Red clauses (LLM)
      7. Log everything to SQLite
      8. Aggregate into buyer_view + vendor_view + scorecard
    """
    out_dir = Path(output_dir) / contract_id
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = _HERE / "output" / "audit.db"

    # ── 1. Extract ──────────────────────────────────────────────────────────
    print(f"\n[Orchestrator] Extracting: {pdf_path}")
    raw_text = extract_text(pdf_path)
    print(f"[Orchestrator] {len(raw_text):,} chars extracted.")

    # ── 2. Split ─────────────────────────────────────────────────────────────
    print("[Orchestrator] Splitting into clauses…")
    clauses = split_clauses(raw_text)
    print(f"[Orchestrator] {len(clauses)} clauses identified.")
    for c in clauses[:4]:
        print(f"  • [{c['id']}] {c['text'][:70].strip()!r}…")
    if len(clauses) > 4:
        print(f"  … and {len(clauses)-4} more.")

    # ── 3. Parallel agent fan-out ────────────────────────────────────────────
    tasks = [(agent, clause) for clause in clauses for agent in SPECIALIST_AGENTS]
    total = len(tasks)
    mode  = "sequential" if sequential else "parallel"
    print(f"\n[Orchestrator] Scoring {len(clauses)} clauses × 3 agents = {total} calls ({mode})…")

    responses: list[dict] = []

    def _run(agent: str, clause: dict, idx: int) -> dict:
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        result = _score(agent, clause)
        r, rid = result.get("rating","?"), result.get("rule_id","N/A")
        em = {"Red":"🔴","Amber":"🟡","Green":"🟢"}.get(r,"❓")
        print(f"  [{idx:3d}/{total}] {em} clause={clause['id']:5s} {agent:<22s} {rid}")
        return result

    if sequential:
        for idx, (agent, clause) in enumerate(tasks, 1):
            try:
                responses.append(_run(agent, clause, idx))
            except Exception as exc:
                print(f"  [ERR] {agent} × {clause['id']}: {exc}")
                responses.append({"clause_id": clause["id"], "agent": agent,
                                   "rating": "Amber", "rule_id": "N/A",
                                   "reason": f"[Error: {exc}]"})
    else:
        workers = min(12, total)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            fmap = {ex.submit(_score, ag, cl): (ag, cl, i)
                    for i, (ag, cl) in enumerate(tasks, 1)}
            for fut in concurrent.futures.as_completed(fmap):
                ag, cl, i = fmap[fut]
                try:
                    r = fut.result()
                    responses.append(r)
                    em = {"Red":"🔴","Amber":"🟡","Green":"🟢"}.get(r.get("rating",""),"❓")
                    print(f"  [{i:3d}/{total}] {em} clause={cl['id']:5s} {ag:<22s} {r.get('rule_id','N/A')}")
                except Exception as exc:
                    print(f"  [ERR] {ag} × {cl['id']}: {exc}")
                    responses.append({"clause_id": cl["id"], "agent": ag,
                                       "rating": "Amber", "rule_id": "N/A",
                                       "reason": f"[Error: {exc}]"})

    # Log ratings
    for r in responses:
        try:
            log_rating(contract_id, r["clause_id"], r.get("agent",""),
                       r.get("rating",""), r.get("rule_id",""), r.get("reason",""), db_path)
        except Exception:
            pass

    # ── 4. Benchmark all clauses (offline) ──────────────────────────────────
    print(f"\n[Orchestrator] Benchmarking {len(clauses)} clauses (offline)…")
    benchmarks: dict[str, dict] = {}
    for clause in clauses:
        b = benchmark_clause(clause["id"], clause["text"])
        benchmarks[clause["id"]] = b
        try:
            log_benchmark(contract_id, clause["id"], b, db_path)
        except Exception:
            pass
        verdict = b.get("benchmark_verdict","")
        em = {"aggressive":"🔴","standard":"🟢","lenient":"🟡"}.get(verdict,"⬜")
        print(f"  {em} [{clause['id']:5s}] {verdict:12s}  {b.get('area','')}")

    # ── 5. Redlines for Red / Amber clauses ─────────────────────────────────
    # Pick the highest-risk rating per clause across all agents
    worst: dict[str, dict] = {}
    order = {"Red": 0, "Amber": 1, "Green": 2}
    for r in responses:
        cid = r["clause_id"]
        if cid not in worst or order.get(r["rating"], 2) < order.get(worst[cid]["rating"], 2):
            worst[cid] = r

    redline_candidates = [r for r in worst.values() if r["rating"] in ("Red","Amber")]
    redlines: dict[str, dict] = {}

    if redline_candidates:
        print(f"\n[Orchestrator] Generating redlines for {len(redline_candidates)} clauses…")
        clause_map = {c["id"]: c["text"] for c in clauses}
        for r in redline_candidates:
            cid = r["clause_id"]
            rl = generate_redline(
                cid, clause_map.get(cid,""), r.get("rule_id",""),
                r.get("agent",""), r.get("reason",""),
            )
            redlines[cid] = rl
            try:
                log_redline(contract_id, cid, rl, db_path)
            except Exception:
                pass
            ok = "✏" if "unavailable" not in rl.get("suggested_redline","") else "⚠"
            print(f"  {ok} [{cid}] {rl.get('suggested_redline','')[:70]}…")

    # ── 6. Mediation on Red clauses ─────────────────────────────────────────
    red_clauses = [r for r in worst.values() if r["rating"] == "Red"]
    compromises: dict[str, list] = {}
    clause_map = {c["id"]: c["text"] for c in clauses}

    if red_clauses:
        print(f"\n[Orchestrator] Mediating {len(red_clauses)} Red clauses…")
        for r in red_clauses:
            cid = r["clause_id"]
            redline_text = redlines.get(cid, {}).get("suggested_redline", "")
            if not redline_text or "unavailable" in redline_text:
                continue
            opts = propose_compromise(
                cid, clause_map.get(cid, ""), redline_text,
                r.get("rule_id",""), r.get("agent",""), r.get("reason",""),
            )
            compromises[cid] = opts
            try:
                log_compromise(contract_id, cid, opts, db_path)
            except Exception:
                pass
            print(f"  ⚖ [{cid}] {len(opts)} option(s) generated.")

    # ── 7. Aggregate ─────────────────────────────────────────────────────────
    print(f"\n[Orchestrator] Aggregating {len(responses)} ratings…")
    result = aggregate(
        responses,
        benchmarks=benchmarks,
        redlines=redlines,
        compromises=compromises,
        contract_id=contract_id,
        output_dir=str(out_dir),
    )

    s = result["summary"]
    print(f"\n{'='*60}")
    print(f"  COMPLIANCE SENTINEL — {contract_id}")
    print(f"{'='*60}")
    print(f"  Total  : {s['total']}  🔴 {s['red']}  🟡 {s['amber']}  🟢 {s['green']}")
    print(f"  HTML   : {result['html_path']}")
    print(f"  Buyer  : {result['buyer_path']}")
    print(f"  Vendor : {result['vendor_path']}")
    print(f"{'='*60}\n")
    return result
