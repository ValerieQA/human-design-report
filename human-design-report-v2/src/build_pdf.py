import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from config import TEMPLATES_DIR


PLANET_HEADER_PATTERN = re.compile(r"^(☀️|🌍|🌙|🧭|🪞|🗣️|💚|🔥|📈|🪨|⚡|🌫️|🦂|🩹)\s+")


def _block_to_html(text: str) -> str:
    value = text or ""
    value = re.sub(r"^\s*---+\s*$", "", value, flags=re.MULTILINE)
    value = re.sub(r"^\s*###\s*(.+)$", r"<h3 class='subheading'>\1</h3>", value, flags=re.MULTILINE)
    value = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", value)
    lines = [line.rstrip() for line in value.splitlines() if line.strip()]

    html_parts = []
    in_list = False
    for raw_line in lines:
        line = raw_line.strip()
        if re.match(r"^[-•]\s+", line):
            item = re.sub(r"^[-•]\s+", "", line).strip()
            if not item:
                continue
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{item}</li>")
            continue

        if in_list:
            html_parts.append("</ul>")
            in_list = False

        if PLANET_HEADER_PATTERN.match(line):
            html_parts.append(f"<h3 class='subheading'>{line}</h3>")
        elif line.lower().startswith("reflection:"):
            html_parts.append(f"<p class='reflection'>{line}</p>")
        else:
            html_parts.append(f"<p>{line}</p>")

    if in_list:
        html_parts.append("</ul>")

    return "\n".join(html_parts)


def _planetary_cards(html: str) -> str:
    chunks = re.split(r"(?=<h3 class='subheading'>)", html)
    cards = []
    for chunk in chunks:
        clean = chunk.strip()
        if not clean:
            continue
        cards.append(f"<div class='planet-card'>{clean}</div>")
    return "\n".join(cards) if cards else html


def render_html(context: dict, html_output_path: Path) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
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
