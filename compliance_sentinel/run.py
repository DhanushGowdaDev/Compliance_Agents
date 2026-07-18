"""
run.py — Compliance Sentinel Entry Point v2
Usage: python run.py <path/to/contract.pdf> [--output-dir DIR] [--open] [--sequential] [--delay N]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="compliance_sentinel",
        description="Compliance Sentinel — SaaS DPA Risk-Scoring Swarm (NIM-powered)",
    )
    parser.add_argument("pdf", metavar="CONTRACT.PDF", help="Path to the DPA PDF.")
    parser.add_argument("--output-dir", "-o", default="output", metavar="DIR")
    parser.add_argument("--contract-id", default="", metavar="ID",
                        help="Custom contract ID (default: derived from filename+timestamp).")
    parser.add_argument("--open", action="store_true",
                        help="Open HTML scorecard in browser after run.")
    parser.add_argument("--sequential", action="store_true",
                        help="Process clauses sequentially (free-tier rate-limit safe).")
    parser.add_argument("--delay", type=float, default=0.0, metavar="SECONDS",
                        help="Sleep N seconds between LLM calls.")

    args = parser.parse_args()
    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Load .env
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")

    if not os.environ.get("NIM_API_KEY"):
        print(
            "[ERROR] NIM_API_KEY not set.\n"
            "  Edit .env and set NIM_API_KEY=nvapi-<your-key>",
            file=sys.stderr,
        )
        sys.exit(1)

    # Derive contract_id
    contract_id = args.contract_id
    if not contract_id:
        stem = re.sub(r"[^a-zA-Z0-9_-]", "_", pdf_path.stem)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        contract_id = f"{stem}_{ts}"

    print(
        "\n"
        "╔══════════════════════════════════════════════════╗\n"
        "║     ⚖️  COMPLIANCE SENTINEL v2.0                ║\n"
        "║   SaaS DPA Risk Scoring · NIM Swarm             ║\n"
        "║   Jurisdiction: US (CCPA/CPRA) + EU (GDPR)      ║\n"
        "╚══════════════════════════════════════════════════╝"
    )
    print(f"  Contract ID : {contract_id}")
    print(f"  Output dir  : {args.output_dir}/{contract_id}/\n")

    _sentinel = Path(__file__).parent
    if str(_sentinel) not in sys.path:
        sys.path.insert(0, str(_sentinel))

    from swarm import run_swarm
    result = run_swarm(
        str(pdf_path.resolve()),
        output_dir=args.output_dir,
        contract_id=contract_id,
        sequential=args.sequential,
        delay_seconds=args.delay,
    )

    if args.open:
        import webbrowser
        webbrowser.open(f"file://{result['html_path']}")

    print(f"\nTo view dashboard: python server.py  (then open http://localhost:8765)")
    print(f"Contract ID for dashboard: {contract_id}")


if __name__ == "__main__":
    _dir = Path(__file__).parent
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))
    main()
