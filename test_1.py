import os, re, json
from pathlib import Path
from datetime import datetime

from pdfminer.high_level import extract_text
import spacy
from pdfrw import PdfReader, PdfWriter, PdfName, PdfString

# ── CONFIG ──────────────────────────────────────────────────────────
# Always write inside your own Documents folder → no permission errors
HOME            = Path.home()
STORAGE_DIR     = HOME / "Documents" / "resume_data"
OUTPUT_PDF_DIR  = HOME / "Documents" / "generated_pdfs"
TEMPLATE_PDF    = Path("blank_template.pdf")      # keep next to script
NER_MODEL       = "en_core_web_sm"

# Create folders (parents=True lets it build the whole tree in one go)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PDF_DIR.mkdir(parents=True, exist_ok=True)

# Load NLP model once
nlp = spacy.load(NER_MODEL)

# ── CORE FUNCTIONS ──────────────────────────────────────────────────
def parse_resume(pdf_path: str | Path) -> dict:
    """Extract key fields from a résumé PDF."""
    text = extract_text(pdf_path)
    doc  = nlp(text)

    data = {
        "FullName": None,
        "Email":    None,
        "Phone":    None,
        "College":  None,
        "Domain":   None,
        "RawText":  text,
    }

    # --- Named-entity heuristics ---
    for ent in doc.ents:
        if ent.label_ == "PERSON" and not data["FullName"]:
            data["FullName"] = ent.text.strip()
        elif ent.label_ == "ORG" and not data["College"]:
            data["College"] = ent.text.strip()
        elif ent.label_ == "EMAIL" and not data["Email"]:
            data["Email"] = ent.text.strip()

    # --- Regex heuristics ---
    phone_match = re.search(r"\+?\d[\d\s\-]{9,}", text)
    if phone_match:
        data["Phone"] = phone_match.group().strip()

    # Very rough domain / skills guess
    skills = re.findall(
        r"\b(Java|Python|React|Flutter|Machine Learning|AI|Data Science|DevOps)\b",
        text, re.I,
    )
    if skills:
        data["Domain"] = ", ".join(dict.fromkeys([s.title() for s in skills]))

    return data


def save_parsed_data(data: dict):
    """Store JSON + plaintext log for audit/history."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base      = STORAGE_DIR / f"resume_{timestamp}"
    (base.with_suffix(".json")).write_text(json.dumps(data, indent=2), encoding="utf-8")
    (base.with_suffix(".txt")).write_text(
        "\n".join(f"{k}: {v}" for k, v in data.items()), encoding="utf-8"
    )
    return base


def fill_pdf(template: str | Path, output_path: str | Path, field_data: dict):
    """Fill AcroForm fields of `template` with `field_data` and write to `output_path`."""
    pdf = PdfReader(str(template))
    for page in pdf.pages:
        if not page.Annots:
            continue
        for annot in page.Annots:
            if annot.Subtype == PdfName.Widget and annot.T:
                key = annot.T.to_unicode()
                if key in field_data and field_data[key]:
                    annot.V  = PdfString.encode(field_data[key])
                    annot.Ff = 1  # lock field (remove this line if you want editable)

    PdfWriter().write(str(output_path), pdf)


def process_resume_and_fill_pdf(resume_path: str | Path):
    """High-level convenience wrapper."""
    resume_path = Path(resume_path)
    parsed      = parse_resume(resume_path)
    save_parsed_data(parsed)

    out_pdf = OUTPUT_PDF_DIR / f"offer_{resume_path.stem}.pdf"
    fill_pdf(TEMPLATE_PDF, out_pdf, parsed)
    print(f"✅ Finished. Generated PDF ⇒ {out_pdf.resolve()}")


# ── SAMPLE COMMAND-LINE TEST ────────────────────────────────────────
if __name__ == "__main__":
    sample_resume = "sample_resume.pdf"   # change to an actual file
    process_resume_and_fill_pdf(sample_resume)
import os, re, json
from pathlib import Path
from datetime import datetime

from pdfminer.high_level import extract_text
import spacy
from pdfrw import PdfReader, PdfWriter, PdfName, PdfString

# ── CONFIG ──────────────────────────────────────────────────────────
# Always write inside your own Documents folder → no permission errors
HOME            = Path.home()
STORAGE_DIR     = HOME / "Documents" / "resume_data"
OUTPUT_PDF_DIR  = HOME / "Documents" / "generated_pdfs"
TEMPLATE_PDF    = Path("blank_template.pdf")      # keep next to script
NER_MODEL       = "en_core_web_sm"

# Create folders (parents=True lets it build the whole tree in one go)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PDF_DIR.mkdir(parents=True, exist_ok=True)

# Load NLP model once
nlp = spacy.load(NER_MODEL)

# ── CORE FUNCTIONS ──────────────────────────────────────────────────
def parse_resume(pdf_path: str | Path) -> dict:
    """Extract key fields from a résumé PDF."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"🚫 Resume file not found: {pdf_path}")

    text = extract_text(pdf_path)
    doc  = nlp(text)

    data = {
        "FullName": None,
        "Email":    None,
        "Phone":    None,
        "College":  None,
        "Domain":   None,
        "RawText":  text,
    }

    # --- Named-entity heuristics ---
    for ent in doc.ents:
        if ent.label_ == "PERSON" and not data["FullName"]:
            data["FullName"] = ent.text.strip()
        elif ent.label_ == "ORG" and not data["College"]:
            data["College"] = ent.text.strip()
        elif ent.label_ == "EMAIL" and not data["Email"]:
            data["Email"] = ent.text.strip()

    # --- Regex heuristics ---
    phone_match = re.search(r"\+?\d[\d\s\-]{9,}", text)
    if phone_match:
        data["Phone"] = phone_match.group().strip()

    # Very rough domain / skills guess
    skills = re.findall(
        r"\b(Java|Python|React|Flutter|Machine Learning|AI|Data Science|DevOps)\b",
        text, re.I,
    )
    if skills:
        data["Domain"] = ", ".join(dict.fromkeys([s.title() for s in skills]))

    return data


def save_parsed_data(data: dict):
    """Store JSON + plaintext log for audit/history."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base      = STORAGE_DIR / f"resume_{timestamp}"
    (base.with_suffix(".json")).write_text(json.dumps(data, indent=2), encoding="utf-8")
    (base.with_suffix(".txt")).write_text(
        "\n".join(f"{k}: {v}" for k, v in data.items()), encoding="utf-8"
    )
    return base


def fill_pdf(template: str | Path, output_path: str | Path, field_data: dict):
    """Fill AcroForm fields of `template` with `field_data` and write to `output_path`."""
    pdf = PdfReader(str(template))
    for page in pdf.pages:
        if not page.Annots:
            continue
        for annot in page.Annots:
            if annot.Subtype == PdfName.Widget and annot.T:
                key = annot.T.to_unicode()
                if key in field_data and field_data[key]:
                    annot.V  = PdfString.encode(field_data[key])
                    annot.Ff = 1  # lock field (remove this line if you want editable)

    PdfWriter().write(str(output_path), pdf)


def process_resume_and_fill_pdf(resume_path: str | Path):
    """High-level convenience wrapper."""
    resume_path = Path(resume_path)
    parsed      = parse_resume(resume_path)
    save_parsed_data(parsed)

    out_pdf = OUTPUT_PDF_DIR / f"offer_{resume_path.stem}.pdf"
    fill_pdf(TEMPLATE_PDF, out_pdf, parsed)
    print(f"✅ Finished. Generated PDF ⇒ {out_pdf.resolve()}")


# ── SAMPLE COMMAND-LINE TEST ────────────────────────────────────────
if __name__ == "__main__":
    sample_resume = "sample_resume.pdf"   # change to your actual file path
    process_resume_and_fill_pdf(sample_resume)
