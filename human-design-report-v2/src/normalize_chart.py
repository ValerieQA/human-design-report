import json
import re
from typing import Dict, Optional

from schemas import ChartData, PLANETS
from openai_client import OpenAIClient


FIELD_PATTERNS = {
    "type": r"Type\s*[:\-]\s*(.+)",
    "strategy": r"Strategy\s*[:\-]\s*(.+)",
    "authority": r"Authority\s*[:\-]\s*(.+)",
    "profile": r"Profile\s*[:\-]\s*(.+)",
    "definition": r"Definition\s*[:\-]\s*(.+)",
    "incarnation_cross": r"Incarnation\s+Cross\s*[:\-]\s*(.+)",
}


def _extract_scalar(text: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_planet_block(text: str, section: str) -> Dict[str, Optional[str]]:
    result: Dict[str, Optional[str]] = {planet: None for planet in PLANETS}
    block_match = re.search(rf"{section}\s*[:\-]?(.*?)(?:Design|Centers|Channels|$)", text, re.IGNORECASE | re.DOTALL)
    block = block_match.group(1) if block_match else ""
    for planet in PLANETS:
        m = re.search(rf"{re.escape(planet)}\s*[:\-]\s*(\d+\.\d+)", block, re.IGNORECASE)
        if m:
            result[planet] = m.group(1)
    return result


def _extract_channels(text: str):
    return sorted(set(re.findall(r"\b\d{1,2}-\d{1,2}\b", text)))


def normalize_chart_data(raw_text: str) -> ChartData:
    chart_dict = {k: _extract_scalar(raw_text, p) for k, p in FIELD_PATTERNS.items()}
    chart_dict["personality"] = _extract_planet_block(raw_text, "Personality")
    chart_dict["design"] = _extract_planet_block(raw_text, "Design")
    chart_dict["channels"] = _extract_channels(raw_text)
    chart_dict["centers"] = {}

    parsed = ChartData(**chart_dict)
    if not parsed.type or not parsed.profile:
        parsed = fallback_openai_extraction(raw_text)
    return parsed


def fallback_openai_extraction(raw_text: str) -> ChartData:
    client = OpenAIClient()
    prompt = (
        "Extract Human Design chart fields from text. Return STRICT JSON only with keys: "
        "type, strategy, authority, profile, definition, incarnation_cross, personality, design, channels, centers. "
        "Use null for unknown values.\n\n"
        f"SOURCE TEXT:\n{raw_text}"
    )
    json_str = client.complete(prompt)
    return ChartData(**json.loads(json_str))
