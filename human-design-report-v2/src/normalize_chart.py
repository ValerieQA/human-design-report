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
    "incarnation_cross": ["Incarnation Cross", "Life Theme", "Not Self Theme"],
}


PLANET_SPLIT_MARKERS = (
    r"(?:\n\s*(?:Personality|Design|Centers|Channels|Definition|Profile|Type|Strategy|Authority)\b|$)"
)


CROSS_START_PATTERNS = [r"Right\s+Angle\s+Cross", r"Left\s+Angle\s+Cross", r"Juxtaposition\s+Cross"]


def _clean_value(value: str) -> Optional[str]:
    value = value.strip(" :-\t\r\n")
    value = re.sub(r"\s+", " ", value)
    return value if value else None


def _clean_incarnation_cross(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    for pattern in CROSS_START_PATTERNS:
        match = re.search(pattern, value, re.IGNORECASE)
        if match:
            return _clean_value(value[match.start():])
    return _clean_value(value)


def _extract_field_line(text: str, labels: list[str]) -> Optional[str]:
    for label in labels:
        pattern = rf"(?im)^\s*{re.escape(label)}\s*[:\-]\s*([^\n\r]+)"
        match = re.search(pattern, text)
        if match:
            value = _clean_value(match.group(1))
            if value:
                return value
    return None


def _extract_mhd_core_fields(text: str) -> dict[str, Optional[str]]:
    result: dict[str, Optional[str]] = {
        "type": None,
        "strategy": None,
        "authority": None,
        "profile": None,
        "definition": None,
        "incarnation_cross": None,
    }

    lines = [_clean_value(line) for line in text.splitlines()]
    lines = [line for line in lines if line]

    for index, line in enumerate(lines):
        upper = line.upper()

        if "TYPE" in upper and "AUTHORITY" in upper:
            if index + 1 < len(lines):
                combined = lines[index + 1]
                if " - " in combined:
                    type_part, authority_part = combined.split(" - ", 1)
                    result["type"] = _clean_value(type_part)
                    result["authority"] = _clean_value(authority_part)
                else:
                    result["type"] = combined

        if upper == "PROFILE":
            next_values = [
                item for item in lines[index + 1:index + 5]
                if item.upper() not in {"STRATEGY", "AUTHORITY", "TYPE", "PROFILE"}
            ]
            for value in next_values:
                if re.match(r"^\d/\d\b", value):
                    result["profile"] = value
                    break

        if upper == "STRATEGY":
            next_values = [
                item for item in lines[index + 1:index + 5]
                if item.upper() not in {"PROFILE", "AUTHORITY", "TYPE", "STRATEGY"}
            ]
            for value in next_values:
                if not re.match(r"^\d/\d\b", value):
                    result["strategy"] = value
                    break

        if "LIFE THEME" in upper or "INCARNATION CROSS" in upper:
            if index + 1 < len(lines):
                result["incarnation_cross"] = lines[index + 1]

        if upper == "DEFINITION":
            if index + 1 < len(lines):
                result["definition"] = lines[index + 1]

    result["incarnation_cross"] = _clean_incarnation_cross(result.get("incarnation_cross"))
    return result


def _extract_design_personality_table(text: str) -> tuple[Dict[str, Optional[str]], Dict[str, Optional[str]]]:
    design: Dict[str, Optional[str]] = {planet: None for planet in PLANETS}
    personality: Dict[str, Optional[str]] = {planet: None for planet in PLANETS}

    match = re.search(
        r"(?is)\bDesign\s+Personality\b(.*?)(?:©|TYPE|AUTHORITY|PROFILE|STRATEGY|NOT SELF THEME|$)",
        text,
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
    result: Dict[str, Optional[str]] = {planet: None for planet in PLANETS}

    block_match = re.search(
        rf"(?is){section}\s*[:\-]?\s*(.*?){PLANET_SPLIT_MARKERS}",
        text,
    )
    block = block_match.group(1) if block_match else ""

    for planet in PLANETS:
        match = re.search(rf"(?i)\b{re.escape(planet)}\b\s*[:\-]\s*(\d{{1,2}}\.\d)", block)
        if match:
            result[planet] = match.group(1)

    return result


def _extract_channels(text: str) -> list[str]:
    return sorted(set(re.findall(r"\b\d{1,2}-\d{1,2}\b", text)))


def _extract_centers(text: str) -> Dict[str, Optional[str]]:
    known = ["Head", "Ajna", "Throat", "G", "Ego", "Sacral", "Spleen", "Solar Plexus", "Root"]
    centers: Dict[str, Optional[str]] = {}

    for name in known:
        match = re.search(rf"(?im)^\s*{re.escape(name)}\s*[:\-]\s*(Defined|Undefined|Open)\b", text)
        centers[name] = match.group(1) if match else None

    return centers


def _merge_dicts(primary: dict, fallback: dict) -> dict:
    merged = dict(primary)
    for key, value in fallback.items():
        if not merged.get(key) and value:
            merged[key] = value
    return merged


def _is_chart_incomplete(chart: ChartData) -> bool:
    has_core = bool(chart.type and chart.strategy and chart.authority and chart.profile)
    has_design = any(chart.design.values())
    has_personality = any(chart.personality.values())
    return not (has_core and has_design and has_personality)


def normalize_chart_data(raw_text: str) -> ChartData:
    regex_fields = {k: _extract_field_line(raw_text, labels) for k, labels in FIELD_ALIASES.items()}
    mhd_fields = _extract_mhd_core_fields(raw_text)
    chart_dict = _merge_dicts(regex_fields, mhd_fields)

    chart_dict["incarnation_cross"] = _clean_incarnation_cross(chart_dict.get("incarnation_cross"))

    design_from_table, personality_from_table = _extract_design_personality_table(raw_text)
    named_design = _extract_named_planet_block(raw_text, "Design")
    named_personality = _extract_named_planet_block(raw_text, "Personality")

    chart_dict["design"] = {planet: design_from_table.get(planet) or named_design.get(planet) for planet in PLANETS}
    chart_dict["personality"] = {
        planet: personality_from_table.get(planet) or named_personality.get(planet) for planet in PLANETS
    }

    chart_dict["channels"] = _extract_channels(raw_text)
    chart_dict["centers"] = _extract_centers(raw_text)

    parsed = ChartData(**chart_dict)
    if _is_chart_incomplete(parsed):
        parsed = fallback_openai_extraction(raw_text)
        parsed.incarnation_cross = _clean_incarnation_cross(parsed.incarnation_cross)
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
    prompt = f"""
Extract Human Design chart fields from text.

Return ONLY valid JSON.
No markdown.
No explanations.

JSON structure:
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

Rules:
- Use null for unknown values.
- Do not invent missing data.
- Do not swap profile with strategy or authority.
- Personality and design must be dictionaries of planet -> Gate.Line.
- Example: "Sun": "44.5"

SOURCE TEXT:
{raw_text}
"""
    json_str = client.complete(prompt)
    json_str = _extract_json_object(json_str)
    return ChartData(**json.loads(json_str))
