import json
from typing import Dict

from openai_client import OpenAIClient
from config import PROMPTS_DIR
from schemas import ChartData

SECTIONS = [
    "overview",
    "type_strategy_authority",
    "profile",
    "planetary_activations",
    "centers",
    "channels",
    "tone_of_voice",
    "business",
    "summary",
]


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def generate_block(section: str, chart: ChartData, report_language: str) -> str:
    client = OpenAIClient()
    template = _load_prompt(section)
    prompt = template.format(
        report_language=report_language,
        chart_json=json.dumps(chart.model_dump(), ensure_ascii=False, indent=2),
    )
    return client.complete(prompt)


def generate_all_blocks(chart: ChartData, report_language: str) -> Dict[str, str]:
    return {section: generate_block(section, chart, report_language) for section in SECTIONS}
