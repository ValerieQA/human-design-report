import json
import re
from typing import Dict, Optional

from schemas import ChartData, PLANETS
from openai_client import OpenAIClient


FIELD_PATTERNS = {
    "type": r"TYPE\s*\n\s*(.+)",
    "strategy": r"STRATEGY\s*\n\s*(.+)",
    "authority": r"AUTHORITY.*?\n\s*(.+)",
    "profile": r"PROFILE\s*\n\s*(.+)",
    "definition": r"DEFINITION\s*\n\s*(.+)",
    "incarnation_cross": r"(?:INCARNATION\s+CROSS|LIFE\s+THEME).*?\n\s*(.+)",
}


def _extract_scalar(text: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_design_personality_table(text: str) -> tuple[Dict[str, Optional[str]], Dict[str, Optional[str]]]:
    """
    Handles MyHumanDesign-style PDFs where the text looks like:
    Design Personality
    57.5 54.3
    51.5 53.3
    ...

    Planet names are often missing from the extracted text, so we map rows
    to PLANETS order.
    """
    design: Dict[str, Optional[str]] = {planet: None for planet in PLANETS}
    personality: Dict[str, Optional[str]] = {planet: None for planet in PLANETS}

    match = re.search(
        r"Design\s+Personality\s+(.*?)(?:©|TYPE|AUTHORITY|PROFILE|STRATEGY|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return design, personality

    block = match.group(1)
    pairs = re.findall(r"\b(\d{1,2}\.\d)\s+(\d{1,2}\.\d)\b", block)

    for index, (design_value, personality_value) in enumerate(pairs):
        if index >= len(PLANETS):
            break

        planet = PLANETS[index]
        design[planet] = design_value
        personality[planet] = personality_value

    return design, personality


def _extract_named_planet_block(text: str, section: str) -> Dict[str, Optional[str]]:
    """
    Fallback for PDFs where planets are explicitly named:
    Sun: 44.5
    Earth: 24.5
    """
    result: Dict[str, Optional[str]] = {planet: None for planet in PLANETS}

    block_match = re.search(
        rf"{section}\s*[:\-]?(.*?)(?:Design|Personality|Centers|Channels|TYPE|PROFILE|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    block = block_match.group(1) if block_match else text

    for planet in PLANETS:
        m = re.search(rf"{re.escape(planet)}\s*[:\-]\s*(\d{{1,2}}\.\d)", block, re.IGNORECASE)
        if m:
            result[planet] = m.group(1)

    return result


def _extract_channels(text: str):
    return sorted(set(re.findall(r"\b\d{1,2}-\d{1,2}\b", text)))


def _is_chart_incomplete(chart: ChartData) -> bool:
    has_core = bool(chart.type or chart.profile or chart.authority or chart.strategy)
    has_design = any(chart.design.values())
    has_personality = any(chart.personality.values())

    return not (has_core and has_design and has_personality)


def normalize_chart_data(raw_text: str) -> ChartData:
    chart_dict = {k: _extract_scalar(raw_text, p) for k, p in FIELD_PATTERNS.items()}

    design_from_table, personality_from_table = _extract_design_personality_table(raw_text)

    named_personality = _extract_named_planet_block(raw_text, "Personality")
    named_design = _extract_named_planet_block(raw_text, "Design")

    chart_dict["design"] = {
        planet: design_from_table.get(planet) or named_design.get(planet)
        for planet in PLANETS
    }

    chart_dict["personality"] = {
        planet: personality_from_table.get(planet) or named_personality.get(planet)
        for planet in PLANETS
    }

    chart_dict["channels"] = _extract_channels(raw_text)
    chart_dict["centers"] = {}

    parsed = ChartData(**chart_dict)

    if _is_chart_incomplete(parsed):
        parsed = fallback_openai_extraction(raw_text)

    return parsed


def _extract_json_object(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"OpenAI did not return valid JSON. Response was:\n{text}")

    return text[start:end + 1]


def fallback_openai_extraction(raw_text: str) -> ChartData:
    client = OpenAIClient()

    system_prompt = (
        "You extract Human Design chart data from raw PDF text. "
        "Return ONLY valid JSON. No markdown. No explanations. "
        "Use null for missing values. Do not invent missing data."
    )

    user_prompt = f"""
Extract Human Design chart data from this text.

Return JSON with exactly this structure:
{{
  "type": null,
  "strategy": null,
  "authority": null,
  "profile": null,
  "definition": null,
  "incarnation_cross": null,
  "personality": {{}},
  "design": {{}},
  "channels": [],
  "centers": {{}}
}}

For personality and design, use planet names as keys and Gate.Line as values.
Example:
"Sun": "44.5"

Raw text:
{raw_text}
"""

    json_str = client.complete(system_prompt + "\n\n" + user_prompt)
    json_str = _extract_json_object(json_str)

    return ChartData(**json.loads(json_str))