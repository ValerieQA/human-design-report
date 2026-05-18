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


LANGUAGE_ALIASES = {
    "en": "en",
    "eng": "en",
    "english": "en",
    "ru": "ru",
    "rus": "ru",
    "russian": "ru",
    "русский": "ru",
    "ua": "ua",
    "ukr": "ua",
    "ukrainian": "ua",
    "українська": "ua",
    "украинский": "ua",
    "ukrainian language": "ua",
}


def sanitize_client_name(client_name: str) -> str:
    return "_".join(client_name.strip().split())


def _normalize_default_language() -> str:
    base = (REPORT_LANGUAGE or "en").strip().lower()
    return LANGUAGE_ALIASES.get(base, "en")


def normalize_language(language: str) -> str:
    key = (language or "").strip().lower()
    if not key:
        return _normalize_default_language()
    if key == "uk":
        raise ValueError("ambiguous_uk")
    return LANGUAGE_ALIASES.get(key, key)


def _resolve_ambiguous_uk() -> str:
    followup = input(
        "Did you mean Ukrainian language or United Kingdom context? Please enter: ua for Ukrainian or en for English. "
    ).strip().lower()
    return "ua" if followup == "ua" else "en"


def cleanup_output_dir() -> None:
    for pattern in ("*.pdf", "*.html", "*.json", "*.txt", "*.textClipping"):
        for file_path in OUTPUT_DIR.glob(pattern):
            if file_path.name != ".gitkeep":
                file_path.unlink(missing_ok=True)


def get_inputs() -> tuple[Path, str, str]:
    parser = argparse.ArgumentParser(description="Human Design report generator")
    parser.add_argument("pdf_path", help="Path to source bodygraph PDF")
    parser.add_argument("--client-name", dest="client_name", help="Client name")
    parser.add_argument("--language", dest="language", help="Report language code, e.g. en/ru/ua")
    args = parser.parse_args()

    client_name = args.client_name or input("Enter client name: ").strip()
    language_input = args.language or input("Enter report language (en/ru/ua/etc.): ").strip()
    try:
        language = normalize_language(language_input)
    except ValueError as exc:
        if str(exc) == "ambiguous_uk":
            language = _resolve_ambiguous_uk()
        else:
            raise
    return Path(args.pdf_path), client_name, language


def run_pipeline(pdf_path: Path, client_name: str, report_language: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cleanup_output_dir()
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
