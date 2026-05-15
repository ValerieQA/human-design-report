from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from config import TEMPLATES_DIR


def render_html(context: dict, html_output_path: Path) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html")
    html = template.render(**context)
    html_output_path.write_text(html, encoding="utf-8")
    return html


def export_pdf(html: str, pdf_output_path: Path) -> None:
    HTML(string=html).write_pdf(str(pdf_output_path))
