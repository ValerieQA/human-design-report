import json
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from config import BASE_DIR, TEMPLATES_DIR
from schemas import PLANETS

PLANET_EMOJIS = {"Sun":"☀️","Earth":"🌍","Moon":"🌙","North Node":"🧭","South Node":"🪞","Mercury":"🗣️","Venus":"💚","Mars":"🔥","Jupiter":"📈","Saturn":"🪨","Uranus":"⚡","Neptune":"🌫️","Pluto":"🦂","Chiron":"🩹"}

LABELS = {
    "en": {
        "title": "Human Design Report",
        "core": "Core Chart Snapshot",
        "activation_map": "Human Design Activation Map",
        "personality_acts": "Personality Activations",
        "design_acts": "Design Activations",
        "overview": "Overview / General Summary",
        "tsa": "Type / Strategy / Authority",
        "profile": "Profile",
        "planets": "Planetary Activations",
        "centers": "Centers",
        "channels": "Channels",
        "tone": "Tone of Voice",
        "business": "Business / Social Application",
        "summary": "Final Summary",
    },
    "ru": {
        "title": "Отчёт Human Design",
        "core": "Основные параметры карты",
        "activation_map": "Карта активаций",
        "personality_acts": "Активации Личности",
        "design_acts": "Активации Дизайна",
        "overview": "Обзор",
        "tsa": "Тип / Стратегия / Авторитет",
        "profile": "Профиль",
        "planets": "Планетарные активации",
        "centers": "Центры",
        "channels": "Каналы",
        "tone": "Тон голоса",
        "business": "Бизнес / Социальное применение",
        "summary": "Финальное резюме",
    },
    "ua": {
        "title": "Звіт Human Design",
        "core": "Основні параметри карти",
        "activation_map": "Карта активацій",
        "personality_acts": "Активації Особистості",
        "design_acts": "Активації Дизайну",
        "overview": "Огляд",
        "tsa": "Тип / Стратегія / Авторитет",
        "profile": "Профіль",
        "planets": "Планетарні активації",
        "centers": "Центри",
        "channels": "Канали",
        "tone": "Тон голосу",
        "business": "Бізнес / Соціальне застосування",
        "summary": "Фінальний підсумок",
    },
}


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
    html_parts, in_list = [], False
    for line in lines:
        if re.match(r"^[-•*]\s+", line):
            item = re.sub(r"^[-•*]\s+", "", line).strip()
            if item:
                if not in_list:
                    html_parts.append("<ul>")
                    in_list = True
                html_parts.append(f"<li>{item}</li>")
            continue
        if in_list:
            html_parts.append("</ul>")
            in_list = False
        html_parts.append(f"<p>{line}</p>")
    if in_list:
        html_parts.append("</ul>")
    html = "\n".join(html_parts)
    html = re.sub(r"<p>(🧭|🧠|🌑|⚠️|✨|🧬|💼|🤝)\s*([^<]+)</p>", r"<div class='subsection'><div class='subsection-title'>\1 \2</div></div>", html)
    html = re.sub(r"<p>(🪞\s*Reflection:?[^<]*)</p>", r"<div class='reflection-box'>\1</div>", html)
    html = re.sub(r"<p>(🔑\s*Quantum Phrase:?[^<]*)</p>", r"<div class='quantum-box'>\1</div>", html)
    html = re.sub(r"(<div class='subsection'><div class='subsection-title'>🧬[^<]*</div></div>)", r"<div class='gene-keys-box'>\1", html)
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
    if "###" in html or "**" in html or "---" in html:
        errors.append("Markdown artifacts detected")
    if "<li></li>" in html or re.search(r">\s*[•\-*]\s*<", html):
        errors.append("Empty bullet artifacts detected")

    expected = [p for p in PLANETS if chart.get("personality", {}).get(p) or chart.get("design", {}).get(p)]
    if (html.count('class="planet-card"') + html.count("class='planet-card'")) != len(expected):
        errors.append("Planet card count mismatch")

    overview_chunk = html.split("id=\"overview\"",1)[1].split("id=\"type-strategy-authority\"",1)[0] if "id=\"overview\"" in html else ""
    if re.search(r"\b\d{1,2}\.\d\b", overview_chunk):
        errors.append("Overview contains raw gate list")

    if errors:
        raise ValueError("Report structure validation failed:\n" + "\n".join(f"- {e}" for e in errors))


def render_html(context: dict, html_output_path: Path) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "xml"]))
    template = env.get_template("report.html")
    cleaned_blocks = {k: _block_to_html(v) for k, v in context.get("blocks", {}).items()}
    enhanced = dict(context)
    lang = context.get("language", "en")
    enhanced["ui"] = LABELS.get(lang, LABELS["en"])
    enhanced["blocks_html"] = cleaned_blocks
    enhanced["activation_map_rows"] = _build_activation_map(context.get("chart", {}))
    html = template.render(**enhanced)
    validate_report_structure(context.get("chart", {}), html)
    html_output_path.write_text(html, encoding="utf-8")
    return html


def export_pdf(html: str, pdf_output_path: Path) -> None:
    HTML(string=html).write_pdf(str(pdf_output_path))
