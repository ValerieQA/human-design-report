import json
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from config import BASE_DIR, TEMPLATES_DIR


PLANET_NAMES = "Sun|Earth|Moon|North Node|South Node|Mercury|Venus|Mars|Jupiter|Saturn|Uranus|Neptune|Pluto|Chiron"
PLANET_HEADER_PATTERN = re.compile(rf"^(?:\S+\s+)?(?:{PLANET_NAMES})\b")
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


def _looks_like_md_table_line(line: str) -> bool:
    return line.count("|") >= 2


def _wrap_special_boxes(text: str) -> str:
    text = re.sub(r"<p class='subsection subsection-title'>(🪞\s*Reflection:?[^<]*)</p>", r"<div class='reflection-box'><p class='subsection subsection-title'>\1</p></div>", text)
    text = re.sub(r"<p class='subsection subsection-title'>(🔑\s*Quantum Phrase:?[^<]*)</p>", r"<div class='quantum-box'><p class='subsection subsection-title'>\1</p></div>", text)
    text = re.sub(r"(<p class='subsection subsection-title'>(?:🧬\s*Gene Keys:?|Gene Keys:)[^<]*</p>)", r"<div class='gene-keys-box'>\1", text)
    text = re.sub(r"(<p>\s*(?:Shadow|Gift|Siddhi)\s*:.*?</p>)", r"\1", text)
    text = text.replace("</div><p class='subsection subsection-title'>", "</div><p class='subsection subsection-title'>")
    return text


def _block_to_html(text: str) -> str:
    value = re.sub(r"^\s*---+\s*$", "", text or "", flags=re.MULTILINE)
    lines = [_clean_line(line) for line in value.splitlines()]
    lines = [line for line in lines if line and line not in {"•", "-", "*"}]
    html_parts, in_list, i = [], False, 0
    while i < len(lines):
        line = lines[i]
        if _looks_like_md_table_line(line):
            rows = []
            while i < len(lines) and _looks_like_md_table_line(lines[i]):
                row = [c.strip() for c in lines[i].strip("|").split("|")]
                if not all(set(c) <= {"-", ":", " "} for c in row):
                    rows.append(row)
                i += 1
            if rows:
                html_parts.append("<table class='clean-table'>")
                html_parts.append("<thead><tr>" + "".join(f"<th>{h}</th>" for h in rows[0]) + "</tr></thead><tbody>")
                for row in rows[1:]:
                    html_parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
                html_parts.append("</tbody></table>")
            continue
        if re.match(r"^[-•*]\s+", line):
            item = re.sub(r"^[-•*]\s+", "", line).strip()
            if item:
                if not in_list:
                    html_parts.append("<ul>"); in_list = True
                html_parts.append(f"<li>{item}</li>")
            i += 1; continue
        if in_list:
            html_parts.append("</ul>"); in_list = False
        if PLANET_HEADER_PATTERN.match(line):
            html_parts.append(f"<h3 class='planet-header planet-title'>{line}</h3>")
        elif re.match(r"^(Role of|Personality|Design|Synthesis:|Shadow:|Gift:|Gene Keys:|Business:|Social|Reflection:|Quantum phrase:|🧭|🧠|🌑|⚠️|✨|🧬|💼|🤝|🪞|🔑)", line, re.IGNORECASE):
            klass = "subsection subsection-title"
            if line.lower().startswith("role of"):
                klass += " planet-role"
            html_parts.append(f"<p class='{klass}'>{line}</p>")
        else:
            html_parts.append(f"<p>{line}</p>")
        i += 1
    if in_list:
        html_parts.append("</ul>")
    return _wrap_special_boxes("\n".join(html_parts))


def _planetary_cards(html: str) -> str:
    chunks = re.split(r"(?=<h3 class='planet-header)", html)
    return "\n".join([f"<div class='planet-card'>{c.strip()}</div>" for c in chunks if c.strip()])


def _build_activation_map(chart: dict) -> list[dict]:
    themes = _load_gate_themes(); personality = chart.get("personality", {}); design = chart.get("design", {})
    planets = list(dict.fromkeys(list(personality.keys()) + list(design.keys())))
    rows = []
    for planet in planets:
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


def _safe_channels_text(language: str) -> str:
    if language == "ru":
        return "Данные по каналам отсутствуют или не были извлечены из исходного PDF, поэтому этот раздел следует считать недоступным."
    if language == "ua":
        return "Дані про канали відсутні або не були витягнуті з вихідного PDF, тому цей розділ слід вважати недоступним."
    return "Channel data was not available or was not extracted from the source PDF, so this section should be treated as unavailable."


def render_html(context: dict, html_output_path: Path) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "xml"]))
    template = env.get_template("report.html")
    cleaned_blocks = {k: _block_to_html(v) for k, v in context.get("blocks", {}).items()}
    if "planetary_activations" in cleaned_blocks:
        cleaned_blocks["planetary_activations"] = _planetary_cards(cleaned_blocks["planetary_activations"])
    chart = context.get("chart", {})
    if not chart.get("channels"):
        cleaned_blocks["channels"] = f"<p>{_safe_channels_text(context.get('language', 'en'))}</p>"
    enhanced_context = dict(context)
    enhanced_context["blocks_html"] = cleaned_blocks
    enhanced_context["activation_map_rows"] = _build_activation_map(chart)
    html = template.render(**enhanced_context)
    html_output_path.write_text(html, encoding="utf-8")
    return html


def export_pdf(html: str, pdf_output_path: Path) -> None:
    HTML(string=html).write_pdf(str(pdf_output_path))
