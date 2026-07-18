"""
audit_logger.py — Orchestrator Tool
Appends every agent rating, redline, benchmark verdict, and human override
to a local SQLite audit log. Exposes get_audit_trail(contract_id) → JSON.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_DB = Path(__file__).parent.parent.parent / "output" / "audit.db"


def _conn(db_path: str | Path = _DEFAULT_DB) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT    NOT NULL,
            contract_id     TEXT    NOT NULL,
            clause_id       TEXT    NOT NULL,
            agent_name      TEXT    NOT NULL,
            action          TEXT    NOT NULL,  -- 'rating'|'redline'|'benchmark'|'compromise'|'override'
            rating          TEXT,
            rule_id         TEXT,
            reason          TEXT,
            extra_json      TEXT,              -- JSON blob for redline/benchmark/compromise payloads
            human_override  TEXT,              -- 'accept'|'reject'|'edit'|NULL
            override_by     TEXT,
            override_note   TEXT
        )
    """)
    con.commit()
    return con


def log_rating(
    contract_id: str,
    clause_id: str,
    agent_name: str,
    rating: str,
    rule_id: str,
    reason: str,
    db_path: str | Path = _DEFAULT_DB,
) -> None:
    with _conn(db_path) as con:
        con.execute(
            """INSERT INTO audit_log
               (timestamp, contract_id, clause_id, agent_name, action, rating, rule_id, reason)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                contract_id, clause_id, agent_name,
                "rating", rating, rule_id, reason,
            ),
        )


def log_redline(
    contract_id: str,
    clause_id: str,
    redline_data: dict,
    db_path: str | Path = _DEFAULT_DB,
) -> None:
    with _conn(db_path) as con:
        con.execute(
            """INSERT INTO audit_log
               (timestamp, contract_id, clause_id, agent_name, action, rule_id, extra_json)
               VALUES (?,?,?,?,?,?,?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                contract_id, clause_id, "redline_generator",
                "redline",
                redline_data.get("rule_id_addressed", ""),
                json.dumps(redline_data),
            ),
        )


def log_benchmark(
    contract_id: str,
    clause_id: str,
    benchmark_data: dict,
    db_path: str | Path = _DEFAULT_DB,
) -> None:
    with _conn(db_path) as con:
        con.execute(
            """INSERT INTO audit_log
               (timestamp, contract_id, clause_id, agent_name, action, extra_json)
               VALUES (?,?,?,?,?,?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                contract_id, clause_id, "clause_benchmarker",
                "benchmark",
                json.dumps(benchmark_data),
            ),
        )


def log_compromise(
    contract_id: str,
    clause_id: str,
    compromise_data: list,
    db_path: str | Path = _DEFAULT_DB,
) -> None:
    with _conn(db_path) as con:
        con.execute(
            """INSERT INTO audit_log
               (timestamp, contract_id, clause_id, agent_name, action, extra_json)
               VALUES (?,?,?,?,?,?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                contract_id, clause_id, "mediator_agent",
                "compromise",
                json.dumps(compromise_data),
            ),
        )


def log_override(
    contract_id: str,
    clause_id: str,
    human_override: str,
    override_by: str,
    override_note: str = "",
    db_path: str | Path = _DEFAULT_DB,
) -> None:
    """Record a human accept/reject/edit action from the dashboard."""
    with _conn(db_path) as con:
        con.execute(
            """INSERT INTO audit_log
               (timestamp, contract_id, clause_id, agent_name, action,
                human_override, override_by, override_note)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                contract_id, clause_id, "human",
                "override", human_override, override_by, override_note,
            ),
        )


def get_audit_trail(
    contract_id: str,
    db_path: str | Path = _DEFAULT_DB,
) -> list[dict[str, Any]]:
    """Return full audit history for a contract as a list of dicts."""
    try:
        with _conn(db_path) as con:
            rows = con.execute(
                "SELECT * FROM audit_log WHERE contract_id=? ORDER BY id ASC",
                (contract_id,),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
