import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from config import TEMPLATES_DIR


def _block_to_html(text: str) -> str:
    value = text or ""
    value = re.sub(r"^\s*---+\s*$", "", value, flags=re.MULTILINE)
    value = re.sub(r"^\s*###\s*(.+)$", r"<h3 class='subheading'>\1</h3>", value, flags=re.MULTILINE)
    value = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", value)
    lines = [line.rstrip() for line in value.splitlines() if line.strip()]

    html_parts = []
    in_list = False
    for line in lines:
        if re.match(r"^[-•]\s+", line):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            item = re.sub(r"^[-•]\s+", "", line)
            html_parts.append(f"<li>{item}</li>")
        else:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f"<p>{line}</p>")
    if in_list:
        html_parts.append("</ul>")
    return "\n".join(html_parts)


def render_html(context: dict, html_output_path: Path) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html")

    cleaned_blocks = {k: _block_to_html(v) for k, v in context.get("blocks", {}).items()}
    enhanced_context = dict(context)
    enhanced_context["blocks_html"] = cleaned_blocks

    html = template.render(**enhanced_context)
    html_output_path.write_text(html, encoding="utf-8")
    return html


def export_pdf(html: str, pdf_output_path: Path) -> None:
    HTML(string=html).write_pdf(str(pdf_output_path))
