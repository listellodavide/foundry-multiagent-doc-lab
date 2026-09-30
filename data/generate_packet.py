"""Generates the onboarding packet and policy for the October 2026 workshop.

Run once from the repo root:  python data/generate_packet.py

All companies, people, numbers and bank details are fictional. The IBAN is a demo string,
not a valid account. Planted issues (see data/golden/decision_record.json):
  R1 breach notice 96 h (DPA)          R2 pen test older than 12 months
  R4 insurance expires 29 days after onboarding   R7 invoice total does not add up
Decoys that test careful reading: a 72-hour data-subject deadline in the DPA, an internal
vulnerability scan dated 2026-09-30, and a EUR 500,000 professional indemnity line.
"""

import sys
from pathlib import Path

import pymupdf as fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shared.config import PACKET_DIR, POLICY_PDF  # noqa: E402
from shared.policy import policy_text  # noqa: E402

LEFT, TOP, RIGHT, BOTTOM = 56, 110, 556, 770


def write_pages(doc: fitz.Document, header: str, pages: list[str], fontsize: float = 10) -> None:
    for n, body in enumerate(pages, start=1):
        page = doc.new_page()  # Letter, 612 x 792 pt
        page.insert_text((LEFT, 60), header, fontsize=14, fontname="hebo")
        page.insert_text((LEFT, 80), f"Page {n} of {len(pages)}", fontsize=8, color=(0.4, 0.4, 0.4))
        page.draw_line((LEFT, 90), (RIGHT, 90), color=(0.6, 0.6, 0.6), width=0.6)
        spare = page.insert_textbox(fitz.Rect(LEFT, TOP, RIGHT, BOTTOM), body, fontsize=fontsize, fontname="helv")
        if spare < 0:
            raise ValueError(f"{header} page {n} overflows by {-spare:.0f} pt: split the text")


def make_pdf(path: Path, header: str, pages: list[str]) -> None:
    doc = fitz.open()
    write_pages(doc, header, pages)
    doc.set_metadata({"title": header, "author": "PDF Agents Lab generator"})
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    doc.close()


def make_scanned_pdf(path: Path, header: str, body: str) -> None:
    """Render text to an image and save a PDF whose only page is that image (no text layer)."""
    tmp = fitz.open()
    write_pages(tmp, header, [body], fontsize=11)
    pix = tmp[0].get_pixmap(dpi=110, colorspace=fitz.csGRAY)
    tmp.close()
    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(page.rect, stream=pix.tobytes("png"))
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    doc.close()


MSA_P1 = """MASTER SERVICES AGREEMENT No. CC-MSA-2026-031

Between CONTOSO CREATIVE SRL, Bucharest, Romania ("Customer") and CARPATHIA LOCALIZATION SRL, Cluj-Napoca, Romania ("Vendor").

1. DEFINITIONS
"Services" means the translation and localisation services in clause 2. "Fees" means the amounts payable under Schedule A. "Effective Date" means 2 November 2026.

2. SERVICES
Vendor shall translate and localise product user-interface strings, help content and release notes into twelve (12) languages, using Customer's terminology database and translation memory.

3. TERM AND RENEWAL
This Agreement starts on the Effective Date and runs for twenty-four (24) months. It renews automatically for successive periods of twelve (12) months unless either party gives written notice of non-renewal at least sixty (60) days before the end of the current term.

4. FEES AND INVOICING
Vendor shall invoice monthly in arrears at the per-word rates in Schedule A. One-off setup work is invoiced on completion.

5. PAYMENT
Customer shall pay each correct and undisputed invoice within forty-five (45) days of receipt.

6. CONFIDENTIALITY
Each party shall keep the other party's confidential information secret and use it only to perform this Agreement, during the term and for five (5) years after it ends.
"""

MSA_P2 = """7. DATA PROTECTION
Vendor processes personal data on behalf of Customer only as set out in the Data Processing Addendum (DPA) attached as document 02, which forms part of this Agreement.

8. LIABILITY
Except for fraud, wilful misconduct and breaches of clause 6, each party's aggregate liability arising out of or in connection with this Agreement shall not exceed the total Fees paid or payable in the twelve (12) months preceding the event giving rise to the claim.

9. TERMINATION
Either party may terminate for material breach not remedied within thirty (30) days of written notice.

10. GOVERNING LAW
This Agreement is governed by Romanian law. The courts of Bucharest have exclusive jurisdiction.

SIGNATURES

For CONTOSO CREATIVE SRL
Name: Andrei Popescu
Title: Head of Procurement
Date: 20 October 2026

For CARPATHIA LOCALIZATION SRL
Name: Ioana Marinescu
Title: Managing Director
Date: 20 October 2026
"""

DPA = """DATA PROCESSING ADDENDUM to Master Services Agreement CC-MSA-2026-031

1. ROLES. Contoso Creative SRL is the Controller. Carpathia Localization SRL is the Processor.

2. SUBJECT MATTER. Processing of names and e-mail addresses of Customer employees and contractors who appear in source files, review comments and translation memory, for the duration of the Agreement.

3. SUBPROCESSORS. Processor uses TransCloud GmbH (Germany) to host machine-translation engines. Processor shall inform Controller at least thirty (30) days before adding or replacing a subprocessor.

4. LOCATION. Personal data is stored and processed only within the European Economic Area.

5. DATA SUBJECT REQUESTS. Processor shall forward to Controller, within seventy-two (72) hours, any request it receives from a data subject, and shall assist Controller in answering it.

6. SECURITY. Processor maintains the technical and organisational measures described in its security questionnaire (document 03), including encryption at rest and in transit and multi-factor authentication for all staff.

7. PERSONAL DATA BREACH. Processor shall notify Controller without undue delay and in any event within ninety-six (96) hours after becoming aware of a personal data breach, providing the information reasonably available at that time.

8. AUDIT. Controller may audit Processor once per year on thirty (30) days' notice, or rely on Processor's SOC 2 Type II report.

9. RETURN AND DELETION. At the end of the Agreement Processor shall return or delete all personal data within sixty (60) days.
"""

QUESTIONNAIRE = """VENDOR SECURITY QUESTIONNAIRE - completed by Carpathia Localization SRL, 14 October 2026

Q1. Do you hold a current SOC 2 Type II report?
Yes. Our latest SOC 2 Type II report covers the period 1 June 2025 to 31 May 2026 and was issued on 15 July 2026 by an independent audit firm.

Q2. When was your latest external penetration test?
Our last external penetration test was completed on 20 June 2025 by SecureWay SRL. The next one is scheduled for the first quarter of 2027. We also run an internal vulnerability scan every month; the most recent scan was on 30 September 2026.

Q3. Is multi-factor authentication enforced?
Yes, for all staff, on e-mail, VPN and every production system.

Q4. How is data encrypted?
AES-256 at rest; TLS 1.2 or higher in transit.

Q5. Where is customer data hosted?
Microsoft Azure, West Europe and North Europe regions.

Q6. Do you have an incident response plan?
Yes. It is tested with a tabletop exercise every year; the last exercise was in March 2026.

Q7. Are employees screened?
Yes, background checks before hiring, and security awareness training every year.

Q8. Do you use subprocessors?
Yes: TransCloud GmbH, Germany (machine-translation hosting).

Q9. Business continuity?
Daily encrypted backups with 30-day retention; recovery tested twice a year.
"""

INSURANCE = """CERTIFICATE OF INSURANCE

Insurer: Danubius Asigurari SA (fictional), Bucharest
Insured: CARPATHIA LOCALIZATION SRL, Cluj-Napoca
Certificate number: CY-2025-88417
Issued: 2 December 2025

COVERAGE SUMMARY
- Cyber liability: limit EUR 2,000,000 per claim and in the aggregate.
- Professional indemnity: limit EUR 500,000 per claim.
- General liability: limit EUR 1,000,000 per occurrence.

POLICY PERIOD
From 2 December 2025 to 1 December 2026, both dates inclusive.

This certificate is issued as a matter of information only and confers no rights upon the certificate holder. Renewal is subject to underwriting review.
"""

INVOICE = """INVOICE INV-2026-0142

Seller: CARPATHIA LOCALIZATION SRL, Cluj-Napoca, Romania
Buyer: CONTOSO CREATIVE SRL, Bucharest, Romania
Invoice date: 22 October 2026
Reference: MSA CC-MSA-2026-031, one-off setup work

LINE ITEMS
1. Terminology database setup (12 languages)        1 x EUR 2,500.00   =  EUR 2,500.00
2. Translation memory migration                      1 x EUR 1,500.00   =  EUR 1,500.00

Subtotal:   EUR 4,000.00
VAT:        EUR   760.00
TOTAL DUE:  EUR 4,800.00

Payment terms: 45 days from receipt, as per clause 5 of the MSA.
Bank details: see company profile.
"""

PROFILE = """COMPANY PROFILE

Legal name: CARPATHIA LOCALIZATION SRL
Trade register number: J40/12345/2019
Fiscal code: RO40123456
Registered office: Strada Exemplu 10, Cluj-Napoca, Romania

Authorised signatory: Ioana Marinescu, Managing Director
Second contact: Mihai Georgescu, Operations Lead

Bank: Banca Demo SA
IBAN: RO49 DEMO 0000 1234 5678 9012 (demo value, not a real account)

Contact for onboarding: onboarding@carpathia.example
Stamp and signature on file.
"""

POLICY_HEADER = """CONTOSO CREATIVE - VENDOR ONBOARDING POLICY (version 3, 2026)

Every new vendor that processes personal data or receives customer material must pass the rules below before its first purchase order. Procurement records one decision per vendor: approve, conditional or reject.

RULES
"""


def main() -> None:
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    make_pdf(PACKET_DIR / "01_msa.pdf", "Master Services Agreement", [MSA_P1, MSA_P2])
    make_pdf(PACKET_DIR / "02_dpa.pdf", "Data Processing Addendum", [DPA])
    make_pdf(PACKET_DIR / "03_security_questionnaire.pdf", "Vendor Security Questionnaire", [QUESTIONNAIRE])
    make_pdf(PACKET_DIR / "04_insurance_certificate.pdf", "Certificate of Insurance", [INSURANCE])
    make_pdf(PACKET_DIR / "05_invoice.pdf", "Invoice", [INVOICE])
    make_scanned_pdf(PACKET_DIR / "06_company_profile_scan.pdf", "Company Profile", PROFILE)
    make_pdf(POLICY_PDF, "Vendor Onboarding Policy", [POLICY_HEADER + policy_text().replace("\n", "\n\n")])
    for pdf in sorted(PACKET_DIR.glob("*.pdf")) + [POLICY_PDF]:
        print(f"  wrote {pdf.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
