# Human Design Report MVP v2

Standalone local MVP to transform a Human Design chart PDF into a validated, multilingual interpretation report, with the PDF as source of truth.

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment setup
```bash
cp .env.example .env
```
Set `OPENAI_API_KEY` and optional `OPENAI_MODEL`.
Default report language is controlled by `REPORT_LANGUAGE` (default: `en`).

## Run
### Full CLI usage
```bash
python src/main.py input/client_chart.pdf --client-name "Artur" --language en
```

### Interactive fallback
If `--client-name` or `--language` are omitted, the app asks:
- `Enter client name:`
- `Enter report language (en/ru/uk/etc.):`

## Output files
- `output/raw_text.txt`
- `output/normalized_chart.json`
- `output/<Client_Name>_HD_CL.html`
- `output/<Client_Name>_HD_CL.pdf`

Client filename format is exact: `Client_Name_HD_CL.pdf`.
Spaces in client name are replaced with underscores.

## Pipeline
1. Extract all text from source PDF.
2. Save raw text.
3. Normalize chart into structured JSON via regex-first parser.
4. Validate structured JSON with Pydantic.
5. Generate report section-by-section.
6. Validate generated content against source facts.
7. Regenerate only problematic blocks.
8. Render styled HTML.
9. Export final PDF.

## Validation logic (mandatory)
Validator checks:
- all source Gate.Line values are present in report
- no hallucinated Gate.Line values
- type/strategy/authority/profile/definition are preserved
- all planets are included

GPT is an interpreter/writer only. The chart PDF remains source of truth.
