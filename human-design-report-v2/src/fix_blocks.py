import json
from typing import Dict, List

from openai_client import OpenAIClient
from schemas import ChartData


def fix_problematic_blocks(chart: ChartData, blocks: Dict[str, str], errors: List[str], report_language: str) -> Dict[str, str]:
    if not errors:
        return blocks

    client = OpenAIClient()
    joined_errors = "\n".join(f"- {e}" for e in errors)
    fixed = dict(blocks)

    for block_name, block_text in blocks.items():
        if any(token in " ".join(errors).lower() for token in ["gate", "planet", "type", "strategy", "authority", "profile", "definition"]):
            prompt = (
                f"Rewrite only this report block in {report_language}. Preserve all factual values from source JSON exactly. "
                "Do not invent values. Keep psychologically safe language.\n\n"
                f"SOURCE JSON:\n{json.dumps(chart.model_dump(), indent=2, ensure_ascii=False)}\n\n"
                f"BLOCK NAME: {block_name}\n"
                f"CURRENT BLOCK:\n{block_text}\n\n"
                f"VALIDATION ERRORS:\n{joined_errors}"
            )
            fixed[block_name] = client.complete(prompt)
    return fixed
