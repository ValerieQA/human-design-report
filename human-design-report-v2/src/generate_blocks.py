import json
from typing import Dict, List

from openai_client import OpenAIClient
from config import PROMPTS_DIR, BASE_DIR
from schemas import ChartData, PLANETS

SECTIONS = [
    "overview",
    "type_strategy_authority",
    "profile",
    "centers",
    "channels",
    "tone_of_voice",
    "business",
    "summary",
]

PLANET_EMOJIS = {"Sun":"☀️","Earth":"🌍","Moon":"🌙","North Node":"🧭","South Node":"🪞","Mercury":"🗣️","Venus":"💚","Mars":"🔥","Jupiter":"📈","Saturn":"🪨","Uranus":"⚡","Neptune":"🌫️","Pluto":"🦂","Chiron":"🩹"}


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _load_gate_themes() -> dict[str, str]:
    data = json.loads((BASE_DIR / "knowledge" / "gates.json").read_text(encoding="utf-8"))
    return {str(k): v.get("theme", "Theme unavailable") for k, v in data.items() if isinstance(v, dict)}


def _gate_theme(gate_line: str | None, themes: dict[str, str]) -> str:
    if not gate_line:
        return "Theme unavailable"
    gate = gate_line.split(".")[0]
    return themes.get(gate, "Theme unavailable")


def generate_block(section: str, chart: ChartData, report_language: str) -> str:
    client = OpenAIClient()
    template = _load_prompt(section)
    prompt = template.format(
        report_language=report_language,
        chart_json=json.dumps(chart.model_dump(), ensure_ascii=False, indent=2),
    )
    return client.complete(prompt)


def _generate_planet_card(planet: str, chart: ChartData, report_language: str, themes: dict[str, str]) -> dict:
    personality_gate = chart.personality.get(planet)
    design_gate = chart.design.get(planet)
    role_map = json.loads((BASE_DIR / "knowledge" / "planets.json").read_text(encoding="utf-8"))
    role = role_map.get(planet, {}).get("role", "Theme unavailable")

    prompt = _load_prompt("planetary_activations").format(
        report_language=report_language,
        chart_json=json.dumps(chart.model_dump(), ensure_ascii=False, indent=2),
    )
    prompt += (
        "\n\nGenerate interpretation for ONE planet only."
        f"\nPlanet: {planet}"
        f"\nPlanet Role: {role}"
        f"\nPersonality Gate.Line: {personality_gate}"
        f"\nDesign Gate.Line: {design_gate}"
        f"\nPersonality Gate Theme: {_gate_theme(personality_gate, themes)}"
        f"\nDesign Gate Theme: {_gate_theme(design_gate, themes)}"
        f"\nChart Type: {chart.type}\nStrategy: {chart.strategy}\nAuthority: {chart.authority}\nProfile: {chart.profile}\nIncarnation Cross: {chart.incarnation_cross}"
    )

    client = OpenAIClient()
    try:
        content = client.complete(prompt)
    except Exception:
        try:
            content = client.complete(prompt)
        except Exception:
            content = (
                f"{PLANET_EMOJIS.get(planet,'🪐')} {planet}\n"
                f"Personality: Gate {personality_gate or 'N/A'} ({_gate_theme(personality_gate, themes)})\n"
                f"Design: Gate {design_gate or 'N/A'} ({_gate_theme(design_gate, themes)})\n"
                "Detailed interpretation could not be generated for this planet."
            )

    return {
        "planet": planet,
        "emoji": PLANET_EMOJIS.get(planet, "🪐"),
        "role": role,
        "personality_gate": personality_gate,
        "design_gate": design_gate,
        "content": content,
    }


def generate_planet_cards(chart: ChartData, report_language: str) -> List[dict]:
    themes = _load_gate_themes()
    cards: List[dict] = []
    for planet in PLANETS:
        if chart.personality.get(planet) or chart.design.get(planet):
            cards.append(_generate_planet_card(planet, chart, report_language, themes))
    return cards


def generate_all_blocks(chart: ChartData, report_language: str) -> Dict[str, str]:
    return {section: generate_block(section, chart, report_language) for section in SECTIONS}
