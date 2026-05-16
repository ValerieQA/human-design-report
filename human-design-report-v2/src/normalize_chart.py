import json
import re
from typing import Dict, Optional

from schemas import ChartData, PLANETS
from openai_client import OpenAIClient


FIELD_ALIASES = {
    "type": ["Type"],
    "strategy": ["Strategy"],
    "authority": ["Authority", "Inner Authority"],
    "profile": ["Profile"],
    "definition": ["Definition"],
    "incarnation_cross": ["Incarnation Cross", "Life Theme"],
}


PLANET_SPLIT_MARKERS = r"(?:\n\s*(?:Personality|Design|Centers|Channels|Definition|Profile|Type|Strategy|Authority)\b|$)"


def _extract_field_line(text: str, labels: list[str]) -> Optional[str]:
    for label in labels:
        pattern = rf"(?im)^\s*{re.escape(label)}\s*[:\-]\s*([^\n\r]+)"
        m = re.search(pattern, text)
        if m:
            value = m.group(1).strip(" :-\t")
            if value:
                return value
    return None


def _extract_planet_block(text: str, section: str) -> Dict[str, Optional[str]]:
    result: Dict[str, Optional[str]] = {planet: None for planet in PLANETS}
    block_match = re.search(rf"(?is){section}\s*[:\-]?\s*(.*?){PLANET_SPLIT_MARKERS}", text)
    block = block_match.group(1) if block_match else ""
    for planet in PLANETS:
        m = re.search(rf"(?i)\b{re.escape(planet)}\b\s*[:\-]\s*(\d{{1,2}}\.\d)", block)
        if m:
            result[planet] = m.group(1)
    return result


def _extract_channels(text: str) -> list[str]:
    return sorted(set(re.findall(r"\b\d{1,2}-\d{1,2}\b", text)))


def _extract_centers(text: str) -> Dict[str, Optional[str]]:
    known = ["Head", "Ajna", "Throat", "G", "Ego", "Sacral", "Spleen", "Solar Plexus", "Root"]
    centers: Dict[str, Optional[str]] = {}
    for name in known:
        m = re.search(rf"(?im)^\s*{re.escape(name)}\s*[:\-]\s*(Defined|Undefined|Open)\b", text)
        centers[name] = m.group(1) if m else None
    return centers


def normalize_chart_data(raw_text: str) -> ChartData:
    chart_dict = {k: _extract_field_line(raw_text, labels) for k, labels in FIELD_ALIASES.items()}
    chart_dict["personality"] = _extract_planet_block(raw_text, "Personality")
    chart_dict["design"] = _extract_planet_block(raw_text, "Design")
    chart_dict["channels"] = _extract_channels(raw_text)
    chart_dict["centers"] = _extract_centers(raw_text)

    parsed = ChartData(**chart_dict)
    if not parsed.type or not parsed.strategy or not parsed.authority or not parsed.profile:
        parsed = fallback_openai_extraction(raw_text)
    return parsed


def fallback_openai_extraction(raw_text: str) -> ChartData:
    client = OpenAIClient()
    prompt = (
        "Extract Human Design chart fields from text. Return STRICT JSON only with keys: "
        "type, strategy, authority, profile, definition, incarnation_cross, personality, design, channels, centers. "
        "Use null for unknown values. Do not swap profile with strategy or authority.\n\n"
        f"SOURCE TEXT:\n{raw_text}"
    )
    json_str = client.complete(prompt)
    return ChartData(**json.loads(json_str))
