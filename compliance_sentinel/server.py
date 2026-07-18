"""
server.py — Compliance Sentinel Dashboard API
Run: python server.py
Then open: http://localhost:8765
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from dotenv import load_dotenv
load_dotenv(_HERE / ".env")

from orchestrator.tools.audit_logger import get_audit_trail, log_override

# ---------------------------------------------------------------------------
app = FastAPI(title="Compliance Sentinel API", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

_OUTPUT = _HERE / "output"
_DASH   = _HERE / "dashboard"


# ── Static dashboard files ───────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    return FileResponse(str(_DASH / "index.html"))


# ── List available contracts ─────────────────────────────────────────────────
@app.get("/api/contracts")
def list_contracts():
    if not _OUTPUT.exists():
        return {"contracts": []}
    contracts = []
    for p in sorted(_OUTPUT.iterdir(), reverse=True):
        if p.is_dir() and (p / "buyer_view.json").exists():
            try:
                bv = json.loads((p / "buyer_view.json").read_text())
                contracts.append({
                    "id":      p.name,
                    "summary": bv.get("summary", {}),
                })
            except Exception:
                contracts.append({"id": p.name})
    return {"contracts": contracts}


# ── Scorecard / risk map ─────────────────────────────────────────────────────
@app.get("/api/scorecard/{contract_id}")
def get_scorecard(contract_id: str, view: str = "buyer"):
    fname = "buyer_view.json" if view == "buyer" else "vendor_view.json"
    path  = _OUTPUT / contract_id / fname
    if not path.exists():
        raise HTTPException(404, f"{fname} not found for contract '{contract_id}'")
    return JSONResponse(content=json.loads(path.read_text()))


# ── Full scorecard (all agents merged) ───────────────────────────────────────
@app.get("/api/scorecard/{contract_id}/full")
def get_full_scorecard(contract_id: str):
    path = _OUTPUT / contract_id / "scorecard.json"
    if not path.exists():
        raise HTTPException(404, "scorecard.json not found")
    return JSONResponse(content=json.loads(path.read_text()))


# ── Audit trail ──────────────────────────────────────────────────────────────
@app.get("/api/audit/{contract_id}")
def get_audit(contract_id: str):
    db = _HERE / "output" / "audit.db"
    trail = get_audit_trail(contract_id, db_path=db)
    return {"contract_id": contract_id, "trail": trail}


# ── Human override ───────────────────────────────────────────────────────────
class OverrideBody(BaseModel):
    contract_id:   str
    clause_id:     str
    human_override: str   # accept | reject | edit
    override_by:   str = "user"
    override_note: str = ""

@app.post("/api/override")
def post_override(body: OverrideBody):
    if body.human_override not in ("accept", "reject", "edit"):
        raise HTTPException(400, "human_override must be accept|reject|edit")
    db = _HERE / "output" / "audit.db"
    log_override(
        body.contract_id, body.clause_id,
        body.human_override, body.override_by, body.override_note,
        db_path=db,
    )
    return {"status": "ok", "recorded": body.dict()}


# ── Serve dashboard static assets ────────────────────────────────────────────
@app.get("/app.js", include_in_schema=False)
def get_app_js():
    return FileResponse(str(_DASH / "app.js"))

if _DASH.exists():
    app.mount("/dashboard", StaticFiles(directory=str(_DASH)), name="dashboard")


if __name__ == "__main__":
    port = int(os.environ.get("DASHBOARD_PORT", 8765))
    print(f"\n⚖️  Compliance Sentinel Dashboard → http://localhost:{port}\n")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
