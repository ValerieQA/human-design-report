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


def validate_planetary_rendering(chart: dict, html: str) -> None:
    expected = [p for p in PLANETS if chart.get("personality", {}).get(p) or chart.get("design", {}).get(p)]
    actual_cards = html.count("class=\"planet-card\"") + html.count("class='planet-card'")
    missing_planets = [p for p in expected if p not in html]
    missing_activations = []
    for p in expected:
        for val in [chart.get("personality", {}).get(p), chart.get("design", {}).get(p)]:
            if val and val not in html:
                missing_activations.append(f"{p} {val}")
    if actual_cards < len(expected) or missing_planets or missing_activations:
        raise ValueError(
            "Planetary rendering validation failed:\n"
            f"Missing planet cards: {', '.join(missing_planets) if missing_planets else 'None'}\n"
            f"Missing activations: {', '.join(missing_activations) if missing_activations else 'None'}\n"
            f"Expected cards: {len(expected)}, Rendered cards: {actual_cards}"
        )


def render_html(context: dict, html_output_path: Path) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "xml"]))
    template = env.get_template("report.html")
    cleaned_blocks = {k: _block_to_html(v) for k, v in context.get("blocks", {}).items()}
    enhanced = dict(context)
    enhanced["blocks_html"] = cleaned_blocks
    enhanced["activation_map_rows"] = _build_activation_map(context.get("chart", {}))
    html = template.render(**enhanced)
    validate_planetary_rendering(context.get("chart", {}), html)
    html_output_path.write_text(html, encoding="utf-8")
    return html


def export_pdf(html: str, pdf_output_path: Path) -> None:
    HTML(string=html).write_pdf(str(pdf_output_path))
