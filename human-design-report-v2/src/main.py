import json
import sys
from pathlib import Path

from build_pdf import export_pdf, render_html
from config import OUTPUT_DIR, REPORT_LANGUAGE
from extract_pdf import extract_text_from_pdf
from fix_blocks import fix_problematic_blocks
from generate_blocks import generate_all_blocks
from normalize_chart import normalize_chart_data
from validate_report import validate_report


def run_pipeline(pdf_path: Path) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_text_path = OUTPUT_DIR / "raw_text.txt"
    normalized_path = OUTPUT_DIR / "normalized_chart.json"
    html_path = OUTPUT_DIR / "report.html"
    pdf_out = OUTPUT_DIR / "report.pdf"

    raw_text = extract_text_from_pdf(pdf_path, raw_text_path)
    chart = normalize_chart_data(raw_text)
    normalized_path.write_text(json.dumps(chart.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")

    blocks = generate_all_blocks(chart, REPORT_LANGUAGE)
    validation = validate_report(chart, blocks)
    if not validation.valid:
        blocks = fix_problematic_blocks(chart, blocks, validation.errors, REPORT_LANGUAGE)

    context = {"chart": chart.model_dump(), "blocks": blocks, "language": REPORT_LANGUAGE}
    html = render_html(context, html_path)
    export_pdf(html, pdf_out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python src/main.py input/client_chart.pdf")
    run_pipeline(Path(sys.argv[1]))
