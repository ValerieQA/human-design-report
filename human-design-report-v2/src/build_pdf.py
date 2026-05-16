import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from config import TEMPLATES_DIR


PLANET_HEADER_PATTERN = re.compile(r"^(☀️|🌍|🌙|🧭|🪞|🗣️|💚|🔥|📈|🪨|⚡|🌫️|🦂|🩹)\s+")


def _clean_line(line: str) -> str:
    line = re.sub(r"^\s*#{1,6}\s*", "", line)
    line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
    line = re.sub(r"^\s*[-*]\s*$", "", line)
    return line.strip()


def _looks_like_md_table_line(line: str) -> bool:
    return line.count("|") >= 2


def _block_to_html(text: str) -> str:
    value = text or ""
    value = re.sub(r"^\s*---+\s*$", "", value, flags=re.MULTILINE)
    lines = [_clean_line(line) for line in value.splitlines()]
    lines = [line for line in lines if line and line not in {"•", "-", "*"}]

    html_parts = []
    in_list = False
    i = 0
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
                header = rows[0]
                html_parts.append("<thead><tr>" + "".join(f"<th>{h}</th>" for h in header) + "</tr></thead>")
                html_parts.append("<tbody>")
                for row in rows[1:]:
                    html_parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
                html_parts.append("</tbody></table>")
            continue

        if re.match(r"^[-•*]\s+", line):
            item = re.sub(r"^[-•*]\s+", "", line).strip()
            if item:
                if not in_list:
                    html_parts.append("<ul>")
                    in_list = True
                html_parts.append(f"<li>{item}</li>")
            i += 1
            continue

        if in_list:
            html_parts.append("</ul>")
            in_list = False

        if PLANET_HEADER_PATTERN.match(line):
            html_parts.append(f"<h3 class='planet-header'>{line}</h3>")
        elif re.match(r"^(Role of|Personality|Design|Synthesis:|Shadow:|Gift:|Gene Keys:|Business:|Social|Reflection:|Quantum phrase:|🧭|🧠|🌑|⚠️|✨|🧬|💼|🤝|🪞|🔑)", line, re.IGNORECASE):
            html_parts.append(f"<p class='subsection-title'>{line}</p>")
        else:
            html_parts.append(f"<p>{line}</p>")
        i += 1

    if in_list:
        html_parts.append("</ul>")

    return "\n".join(html_parts)


def _planetary_cards(html: str) -> str:
    chunks = re.split(r"(?=<h3 class='planet-header'>)", html)
    cards = []
    for chunk in chunks:
        clean = chunk.strip()
        if clean:
            cards.append(f"<div class='planet-card'>{clean}</div>")
    return "\n".join(cards) if cards else html




def render_html(context: dict, html_output_path: Path) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "xml"]))
    template = env.get_template("report.html")

    cleaned_blocks = {k: _block_to_html(v) for k, v in context.get("blocks", {}).items()}
    if "planetary_activations" in cleaned_blocks:
        cleaned_blocks["planetary_activations"] = _planetary_cards(cleaned_blocks["planetary_activations"])

    enhanced_context = dict(context)
    enhanced_context["blocks_html"] = cleaned_blocks
    html = template.render(**enhanced_context)
    html_output_path.write_text(html, encoding="utf-8")
    return html


def export_pdf(html: str, pdf_output_path: Path) -> None:
    HTML(string=html).write_pdf(str(pdf_output_path))
