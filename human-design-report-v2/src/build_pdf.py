import json
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from config import BASE_DIR, TEMPLATES_DIR
from schemas import PLANETS

PLANET_EMOJIS = {"Sun":"☀️","Earth":"🌍","Moon":"🌙","North Node":"🧭","South Node":"🪞","Mercury":"🗣️","Venus":"💚","Mars":"🔥","Jupiter":"📈","Saturn":"🪨","Uranus":"⚡","Neptune":"🌫️","Pluto":"🦂","Chiron":"🩹"}


def _load_gate_themes() -> dict[str, str]:
    gates_path = BASE_DIR / "knowledge" / "gates.json"
    if not gates_path.exists():
        return {}
    data = json.loads(gates_path.read_text(encoding="utf-8"))
    return {str(k): (v.get("theme") if isinstance(v, dict) else None) for k, v in data.items()}


def _clean_line(line: str) -> str:
    line = re.sub(r"^\s*#{1,6}\s*", "", line)
    line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
    line = re.sub(r"^\s*[-*]\s*$", "", line)
    return line.strip()


def _block_to_html(text: str) -> str:
    value = re.sub(r"^\s*---+\s*$", "", text or "", flags=re.MULTILINE)
    lines = [_clean_line(line) for line in value.splitlines()]
    lines = [line for line in lines if line and line not in {"•", "-", "*"}]
    html_parts = []
    for line in lines:
        if re.match(r"^[-•*]\s+", line):
            item = re.sub(r"^[-•*]\s+", "", line).strip()
            if item:
                html_parts.append(f"<li>{item}</li>")
        else:
            html_parts.append(f"<p>{line}</p>")
    html = "\n".join(html_parts)
    html = re.sub(r"(<li>.*?</li>)", r"<ul>\1</ul>", html)
    return html


def _build_activation_map(chart: dict) -> list[dict]:
    themes = _load_gate_themes(); personality = chart.get("personality", {}); design = chart.get("design", {})
    rows = []
    for planet in PLANETS:
        pval, dval = personality.get(planet), design.get(planet)
        if not pval and not dval:
            continue
        def mk(val):
            if not val: return {"gate_line":"N/A", "theme":"Theme unavailable"}
            gate = re.match(r"^(\d{1,2})", val)
            key = gate.group(1) if gate else ""
            return {"gate_line":val, "theme": themes.get(key) or "Theme unavailable"}
        rows.append({"planet":planet, "emoji":PLANET_EMOJIS.get(planet,"🪐"), "personality":mk(pval), "design":mk(dval)})
    return rows


def validate_report_structure(chart: dict, html: str) -> None:
    errors = []
    required_headers = [
        "Core Chart Snapshot", "Activation Map", "Overview / General Summary", "Type / Strategy / Authority",
        "Profile", "Planetary Activations", "Centers", "Channels", "Tone of Voice", "Business / Social Application", "Final Summary"
    ]
    for h in required_headers:
        if h not in html:
            errors.append(f"Missing section: {h}")

    if html.count("Planetary Activations") != 1:
        errors.append("Planetary Activations must appear exactly once")
    if html.count("Final Summary") != 1:
        errors.append("Final Summary must appear exactly once")

    def pos(x): return html.find(x)
    if pos("Planetary Activations") > pos("Centers") or pos("Planetary Activations") > pos("Final Summary"):
        errors.append("Planetary Activations order is invalid")

    expected = [p for p in PLANETS if chart.get("personality", {}).get(p) or chart.get("design", {}).get(p)]
    actual_cards = html.count('class="planet-card"') + html.count("class='planet-card'")
    if actual_cards != len(expected):
        errors.append(f"Planet card count mismatch: expected {len(expected)} got {actual_cards}")

    for p in expected:
        if p not in html:
            errors.append(f"Missing planet card label: {p}")
        pval = chart.get("personality", {}).get(p)
        dval = chart.get("design", {}).get(p)
        if pval and pval not in html:
            errors.append(f"Missing personality activation: {p} {pval}")
        if dval and dval not in html:
            errors.append(f"Missing design activation: {p} {dval}")

    overview_chunk = html.split("Overview / General Summary",1)[1].split("Type / Strategy / Authority",1)[0] if "Overview / General Summary" in html and "Type / Strategy / Authority" in html else ""
    profile_chunk = html.split("<h2>Profile</h2>",1)[1].split("Planetary Activations",1)[0] if "<h2>Profile</h2>" in html and "Planetary Activations" in html else ""
    for banned in ["Планеты личности", "Планеты дизайна", "Personality Activations", "Design Activations"]:
        if banned in overview_chunk: errors.append(f"Overview contains duplicated planet list marker: {banned}")
        if banned in profile_chunk: errors.append(f"Profile contains duplicated planet list marker: {banned}")

    centers_all_null = all(v is None for v in chart.get("centers", {}).values()) if chart.get("centers") else True
    if centers_all_null:
        for banned in ["centers are absent", "centers are open", "centers are undefined", "центры отсутствуют", "центры открыты"]:
            if banned.lower() in html.lower():
                errors.append(f"Unsafe centers claim found: {banned}")
        for banned in ["because you have no defined centers", "because your centers are absent"]:
            if banned.lower() in html.lower():
                errors.append(f"Unsafe business/summary centers claim: {banned}")

    if not chart.get("channels"):
        for banned in ["there are no defined channels", "channels are absent", "каналы отсутствуют"]:
            if banned.lower() in html.lower():
                errors.append(f"Unsafe channels claim found: {banned}")

    if errors:
        raise ValueError("Report structure validation failed:\n" + "\n".join(f"- {e}" for e in errors))


def render_html(context: dict, html_output_path: Path) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "xml"]))
    template = env.get_template("report.html")
    cleaned_blocks = {k: _block_to_html(v) for k, v in context.get("blocks", {}).items()}
    enhanced = dict(context)
    enhanced["blocks_html"] = cleaned_blocks
    enhanced["activation_map_rows"] = _build_activation_map(context.get("chart", {}))
    html = template.render(**enhanced)
    validate_report_structure(context.get("chart", {}), html)
    html_output_path.write_text(html, encoding="utf-8")
    return html


def export_pdf(html: str, pdf_output_path: Path) -> None:
    HTML(string=html).write_pdf(str(pdf_output_path))
