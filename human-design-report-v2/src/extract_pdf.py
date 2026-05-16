from pathlib import Path
import pdfplumber


def extract_text_from_pdf(pdf_path: Path, raw_text_path: Path) -> str:
    chunks = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            chunks.append(text)
    full_text = "\n\n".join(chunks)
    raw_text_path.parent.mkdir(parents=True, exist_ok=True)
    raw_text_path.write_text(full_text, encoding="utf-8")
    return full_text
