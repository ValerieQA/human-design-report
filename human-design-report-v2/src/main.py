import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from build_pdf import export_pdf, render_html
from config import OUTPUT_DIR, REPORT_LANGUAGE
from extract_pdf import extract_text_from_pdf
from fix_blocks import fix_problematic_blocks
from generate_blocks import generate_all_blocks
from normalize_chart import normalize_chart_data
from validate_report import validate_report


def sanitize_client_name(client_name: str) -> str:
    return "_".join(client_name.strip().split())


def get_inputs() -> tuple[Path, str, str]:
    parser = argparse.ArgumentParser(description="Human Design report generator")
    parser.add_argument("pdf_path", help="Path to source bodygraph PDF")
    parser.add_argument("--client-name", dest="client_name", help="Client name")
    parser.add_argument("--language", dest="language", help="Report language code, e.g. en/ru/uk")
    args = parser.parse_args()

    client_name = args.client_name or input("Enter client name: ").strip()
    language = args.language or input("Enter report language (en/ru/uk/etc.): ").strip()
    if not language:
        language = REPORT_LANGUAGE
    return Path(args.pdf_path), client_name, language


def run_pipeline(pdf_path: Path, client_name: str, report_language: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    clean_name = sanitize_client_name(client_name)
    raw_text_path = OUTPUT_DIR / "raw_text.txt"
    normalized_path = OUTPUT_DIR / "normalized_chart.json"
    html_path = OUTPUT_DIR / f"{clean_name}_HD_CL.html"
    pdf_out = OUTPUT_DIR / f"{clean_name}_HD_CL.pdf"

    raw_text = extract_text_from_pdf(pdf_path, raw_text_path)
    chart = normalize_chart_data(raw_text)
    normalized_path.write_text(json.dumps(chart.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")

    blocks = generate_all_blocks(chart, report_language)
    validation = validate_report(chart, blocks)
    if not validation.valid:
        blocks = fix_problematic_blocks(chart, blocks, validation.errors, report_language)

    context = {
        "chart": chart.model_dump(),
        "blocks": blocks,
        "language": report_language,
        "client_name": client_name,
        "generated_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    html = render_html(context, html_path)
    export_pdf(html, pdf_out)


if __name__ == "__main__":
    pdf_path, client_name, report_language = get_inputs()
    run_pipeline(pdf_path, client_name, report_language)
