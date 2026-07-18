"""
generate_sample_contract.py
Creates a sample_contract.pdf with intentional compliance risks for testing.
Run: python generate_sample_contract.py
Requires: pip install reportlab
"""
from pathlib import Path


SAMPLE_CONTRACT_TEXT = """\
SOFTWARE SERVICES AGREEMENT

This Software Services Agreement ("Agreement") is entered into as of January 1, 2025,
between Acme Corp, a Delaware corporation ("Client"), and TechVendor Inc., a California
corporation ("Vendor").

1. SERVICES

1.1 Vendor will provide SaaS platform access and professional services as described in
any Statement of Work attached hereto. Vendor makes no warranty as to uptime, availability,
or response time for the services provided.

2. PAYMENT TERMS

2.1 Client shall pay Vendor within a reasonable time after receipt of each invoice.
Payment shall be made in whatever currency Vendor designates. No interest or late fees
apply to overdue balances.

3. PRICE CHANGES

3.1 Vendor reserves the right to change pricing at any time, in its sole and absolute
discretion, upon notice to Client. Client's continued use of the services constitutes
acceptance of the new pricing.

4. TERM AND TERMINATION

4.1 This Agreement commences on the Effective Date and continues until terminated by
either party upon thirty (30) days written notice. There is no cure period for breach.
Upon termination, all fees owed to Vendor become immediately due and payable.

5. INDEMNIFICATION

5.1 Client shall indemnify, defend, and hold harmless Vendor and its affiliates, officers,
directors, employees, and agents from and against any and all claims, liabilities, damages,
losses, costs, and expenses (including reasonable attorneys' fees) arising out of or
related to Client's use of the services. There is no cap on Client's indemnification
obligations under this section.

6. LIMITATION OF LIABILITY

6.1 IN NO EVENT SHALL VENDOR BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
OR CONSEQUENTIAL DAMAGES. VENDOR'S TOTAL LIABILITY SHALL NOT EXCEED THE FEES PAID IN THE
PRIOR THREE (3) MONTHS. THIS LIMITATION APPLIES TO VENDOR ONLY AND NOT TO CLIENT.

7. DATA PROCESSING AND PRIVACY

7.1 Vendor may process personal data on behalf of Client. Vendor agrees to implement
commercially reasonable security measures to protect personal data. In the event of a
security breach, Vendor will notify Client within a commercially reasonable time.

7.2 Vendor may transfer personal data internationally as required for service delivery.
No reference is made to Standard Contractual Clauses or adequacy decisions.

7.3 Personal data will be retained by Vendor for as long as required by applicable law.

7.4 Vendor may engage subprocessors at its discretion without prior notice to Client.

8. AUTO-RENEWAL

8.1 Unless either party provides written notice of non-renewal, this Agreement will
automatically renew for successive one-year terms. The notice period for opting out of
auto-renewal is not specified.

9. GOVERNING LAW

9.1 This Agreement shall be governed by the laws of the State of Delaware.

10. FORCE MAJEURE

10.1 Neither party shall be liable for failure to perform due to causes beyond its
reasonable control including but not limited to acts of God, government actions, labor
disputes, or any other event Vendor deems appropriate.

11. ASSIGNMENT

11.1 Either party may assign this Agreement or any rights hereunder to any third party
without the consent of the other party.

12. LIQUIDATED DAMAGES

12.1 In the event of any breach by Client, Client shall pay Vendor a liquidated damages
amount equal to three times the annual contract value regardless of actual damages
suffered by Vendor.

13. CCPA/DATA PRIVACY COMPLIANCE

13.1 Vendor acknowledges processing personal information on behalf of Client. No
certification is provided that Vendor will not sell or share personal information.
Vendor is not explicitly designated as a "Service Provider" under the CCPA.

14. ENTIRE AGREEMENT

14.1 This Agreement constitutes the entire agreement between the parties and supersedes
all prior agreements and understandings relating to its subject matter.
"""


def create_pdf(output_path: str = "sample_contract.pdf") -> str:
    """Create a sample contract PDF using reportlab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_LEFT

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=1 * inch,
            leftMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=16,
            spaceAfter=20,
        )
        heading_style = ParagraphStyle(
            "Heading",
            parent=styles["Heading2"],
            fontSize=12,
            spaceAfter=6,
            spaceBefore=12,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=8,
            leading=14,
        )

        story = []
        for line in SAMPLE_CONTRACT_TEXT.strip().split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue

            # Detect section headings
            import re
            if re.match(r"^\d+\.", line) and line.upper() == line or (
                re.match(r"^\d+\.\s+[A-Z]", line) and not re.match(r"^\d+\.\d+", line)
            ):
                story.append(Paragraph(line, heading_style))
            elif re.match(r"^\d+\.\d+", line):
                story.append(Paragraph(line, body_style))
            elif line == line.upper() and len(line) > 10:
                story.append(Paragraph(f"<b>{line}</b>", body_style))
            else:
                story.append(Paragraph(line, body_style))

        doc.build(story)
        print(f"[OK] Sample contract PDF created: {output_path}")
        return output_path

    except ImportError:
        # Fallback: write a plain text file
        txt_path = output_path.replace(".pdf", ".txt")
        Path(txt_path).write_text(SAMPLE_CONTRACT_TEXT, encoding="utf-8")
        print(f"[WARN] reportlab not installed — wrote plain text: {txt_path}")
        print("       To create PDF: pip install reportlab && python generate_sample_contract.py")
        return txt_path


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)
    create_pdf("sample_contract.pdf")
