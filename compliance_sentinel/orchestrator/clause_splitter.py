"""
clause_splitter.py — Orchestrator Tool
Splits extracted contract text into discrete numbered clauses.

Recognises common contract heading patterns:
  - "1."  "2."  "10."
  - "1.1"  "2.3.4"
  - "Section 1"  "Section 2.1"  "SECTION 3"
  - "Article 1"  "ARTICLE IV"
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Clause:
    id: str          # e.g. "1", "2.1", "Section 3"
    heading: str     # raw heading line
    text: str        # full clause text (heading + body)


# ---------------------------------------------------------------------------
# Heading patterns — ordered from most-specific to least-specific
# ---------------------------------------------------------------------------
_HEADING_PATTERNS: list[re.Pattern[str]] = [
    # "Section 3.2.1" / "SECTION 3" / "Article IV" (roman numerals or digits)
    re.compile(
        r"^(?P<kw>Section|SECTION|Article|ARTICLE)\s+"
        r"(?P<id>[IVXLCDM]+|\d+(?:\.\d+)*)"
        r"(?:[ \t]+(?P<title>[^\n]+))?",
        re.MULTILINE,
    ),
    # Standard decimal-numbered heading: "1." or "2.1" or "3.1.2"
    re.compile(
        r"^(?P<id>\d+(?:\.\d+)*)\.[ \t]+(?P<title>[^\n]+)",
        re.MULTILINE,
    ),
]


def split_clauses(text: str) -> list[dict]:
    """
    Split raw contract text into a list of clause dicts:
      [{"id": str, "heading": str, "text": str}, ...]

    If no numbered headings are found, falls back to splitting on
    double-newlines and labelling clauses "para_1", "para_2", …

    Args:
        text: Raw contract text (may contain form-feed characters from pdfplumber).

    Returns:
        List of clause dicts with keys "id", "heading", "text".
    """
    # Normalise form-feeds and excessive blank lines
    text = text.replace("\f", "\n\n")
    text = re.sub(r"\n{3,}", "\n\n", text)

    matches: list[tuple[int, str, str]] = []  # (start_pos, id, heading_text)

    for pattern in _HEADING_PATTERNS:
        for m in pattern.finditer(text):
            id_part = m.group("id")
            title_part = (m.group("title") or "").strip()
            heading_text = m.group(0).strip()
            matches.append((m.start(), id_part, heading_text))

    # Deduplicate and sort by position
    matches.sort(key=lambda x: x[0])
    # Remove overlapping matches (keep the first at each position)
    deduped: list[tuple[int, str, str]] = []
    last_end = -1
    for pos, cid, heading in matches:
        if pos >= last_end:
            deduped.append((pos, cid, heading))
            last_end = pos + len(heading)

    if not deduped:
        # Fallback: paragraph splitting
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        return [
            {"id": f"para_{i+1}", "heading": "", "text": p}
            for i, p in enumerate(paras)
        ]

    clauses: list[dict] = []
    for idx, (pos, cid, heading) in enumerate(deduped):
        start = pos
        end = deduped[idx + 1][0] if idx + 1 < len(deduped) else len(text)
        body = text[start:end].strip()
        clauses.append({"id": cid, "heading": heading, "text": body})

    return clauses


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        # Read stdin
        raw = sys.stdin.read()
    else:
        raw = open(sys.argv[1]).read()

    result = split_clauses(raw)
    print(json.dumps(result, indent=2))
    print(f"\n[{len(result)} clauses identified]")
