"""
pdf_extractor.py — Orchestrator Tool
Extracts raw text from a contract PDF using pdfplumber (preferred) or PyPDF2 fallback.
"""
from __future__ import annotations

import os
from pathlib import Path


def extract_text(pdf_path: str) -> str:
    """
    Extract all text from a PDF file.

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        Concatenated text from all pages, pages separated by a form-feed character.

    Raises:
        FileNotFoundError: If the PDF path does not exist.
        RuntimeError: If both pdfplumber and PyPDF2 fail to parse the file.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8")

    # Try pdfplumber first (better layout preservation)
    try:
        import pdfplumber  # type: ignore

        pages: list[str] = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        if pages:
            return "\f".join(pages)
    except ImportError:
        pass  # fall through to PyPDF2
    except Exception as exc:
        raise RuntimeError(f"pdfplumber failed: {exc}") from exc

    # Fallback: PyPDF2
    try:
        import PyPDF2  # type: ignore

        pages = []
        with open(str(path), "rb") as fh:
            reader = PyPDF2.PdfReader(fh)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        if pages:
            return "\f".join(pages)
        raise RuntimeError("PyPDF2 extracted no text — PDF may be image-based or encrypted.")
    except ImportError as exc:
        raise RuntimeError(
            "Neither pdfplumber nor PyPDF2 is installed. "
            "Run: pip install pdfplumber"
        ) from exc
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"PyPDF2 failed: {exc}") from exc


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <path/to/contract.pdf>")
        sys.exit(1)
    extracted = extract_text(sys.argv[1])
    print(extracted[:2000])
    print(f"\n[Total characters extracted: {len(extracted)}]")
