"""
Resume → PDF-offer-letter generator
-----------------------------------

Dependencies
------------
pip install pdfminer.six spacy pdfrw
python -m spacy download en_core_web_sm
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

from pdfminer.high_level import extract_text              # text extraction :contentReference[oaicite:0]{index=0}
import spacy                                              # NLP :contentReference[oaicite:1]{index=1}
from pdfrw import PdfReader, PdfWriter, PdfName, PdfString  # form filling :contentReference[oaicite:2]{index=2}


# ── CONFIG ──────────────────────────────────────────────────────
HOME            = Path.home()
STORAGE_DIR     = HOME / "Documents" / "resume_data"
OUTPUT_PDF_DIR  = HOME / "Documents" / "generated_pdfs"
TEMPLATE_PDF    = Path(__file__).with_name("blank_template.pdf")  # next to script
NER_MODEL       = "en_core_web_sm"

# Create folders if they don’t exist (mkdir -p) :contentReference[oaicite:3]{index=3}
for d in (STORAGE_DIR, OUTPUT_PDF_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Load NLP model once; abort early if it’s missing
try:
    nlp = spacy.load(NER_MODEL)
except OSError:
    raise SystemExit(
        f"spaCy model “{NER_MODEL}” not found.  Install it with:\n"
        f"    python -m spacy download {NER_MODEL}"
    )

# ── CORE FUNCTIONS ─────────────────────────────────────────────
PHONE_RE = re.compile(r"\+?\d[\d\s\-]{9,14}")  # 7–15 digits per ITU-E.164 :contentReference[oaicite:4]{index=4}
SKILL_RE = re.compile(
    r"\b(Java|Python|React|Flutter|Machine Learning|AI|Data Science|DevOps)\b",
    re.I,
)

def parse_resume(pdf_path: str | Path) -> dict:
    """Return a dict of extracted résumé data."""
    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"🚫 Resume file not found: {pdf_path}")

    text = extract_text(str(pdf_path))                     # pdfminer high-level API :contentReference[oaicite:5]{index=5}
    doc  = nlp(text)

    data = {
        "FullName": None,
        "Email":    None,
        "Phone":    None,
        "College":  None,
        "Domain":   None,
        "RawText":  text,  # saved only to JSON log
    }

    # Named-entity heuristics
    for ent in doc.ents:
        if ent.label_ == "PERSON" and not data["FullName"]:
            data["FullName"] = ent.text.strip()
        elif ent.label_ == "ORG" and not data["College"]:
            data["College"] = ent.text.strip()
        elif ent.label_ == "EMAIL" and not data["Email"]:
            data["Email"] = ent.text.strip()

    # Regex heuristics
    if m := PHONE_RE.search(text):
        data["Phone"] = m.group().strip()

    if skills := SKILL_RE.findall(text):
        # Remove duplicates, title-case, join with commas
        data["Domain"] = ", ".join(dict.fromkeys(s.title() for s in skills))

    return data


def save_parsed_data(data: dict) -> Path:
    """Persist JSON + plaintext audit log.  Return base path."""
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = STORAGE_DIR / f"resume_{ts}"
    base.with_suffix(".json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    base.with_suffix(".txt" ).write_text(
        "\n".join(f"{k}: {v}" for k, v in data.items()),
        encoding="utf-8",
    )
    return base


def fill_pdf(template: str | Path, output_path: str | Path, fields: dict):
    """
    Copy `template` to `output_path`, writing `fields` into AcroForm widgets.

    Field names in the PDF **must exactly match** the keys of `fields`
    (e.g., “FullName”, “Email”, …).  You can inspect field names with
        >>> from pdfrw import PdfReader
        >>> PdfReader("blank_template.pdf").Root.AcroForm
    """
    pdf = PdfReader(str(template))
    for page in pdf.pages or []:                            # None-safe
        for annot in (page.Annots or []):
            if annot.Subtype != PdfName.Widget or not annot.T:
                continue
            key = annot.T.to_unicode()
            if value := fields.get(key):
                annot.V  = PdfString.encode(value)
                annot.Ff = 1      # set read-only flag (“flatten”) :contentReference[oaicite:6]{index=6}

    PdfWriter().write(str(output_path), pdf)                # writes new PDF :contentReference[oaicite:7]{index=7}


def process_resume_and_fill_pdf(resume_path: str | Path):
    """Main entry point."""
    data = parse_resume(resume_path)
    save_parsed_data(data)

    out_pdf = OUTPUT_PDF_DIR / f"offer_{Path(resume_path).stem}.pdf"
    fill_pdf(TEMPLATE_PDF, out_pdf, data)
    print(f"✅ Finished. Generated PDF → {out_pdf.resolve()}")


# ── CLI USAGE ────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Generate offer letter from résumé")
    ap.add_argument("resume", help="Path to résumé PDF")
    args = ap.parse_args()

    process_resume_and_fill_pdf(args.resume)
