from pathlib import Path
from tempfile import TemporaryDirectory

from build_pdf import _build_activation_map, render_html
from main import normalize_language


def _mock_context():
    planets = ["Sun", "Earth", "Moon", "North Node", "South Node", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    personality = {p: f"{i+1}.1" for i, p in enumerate(planets)}
    design = {p: f"{i+2}.2" for i, p in enumerate(planets)}
    emojis = {"Sun":"☀️","Earth":"🌍","Moon":"🌙","North Node":"🧭","South Node":"🪞","Mercury":"🗣️","Venus":"💚","Mars":"🔥","Jupiter":"📈","Saturn":"🪨","Uranus":"⚡","Neptune":"🌫️","Pluto":"🦂"}
    blocks = {
        "overview": "Type Generator\nStrategy Responding\nAuthority Sacral\nProfile 3/5\nDefinition Single\nIncarnation Cross Right Angle Cross\n- Theme one\n- Theme two",
        "type_strategy_authority": "Type: Generator\nStrategy: Responding\nAuthority: Sacral",
        "profile": "Profile 3/5\nStrengths and practical guidance",
        "planetary_activations": "\n".join([f"{emojis[p]} {p} — Role\nRole of {p}: message\n🧭 Synthesis\nPersonality: Gate {personality[p]}\nDesign: Gate {design[p]}\n🪞 Reflection: r\n🔑 Quantum Phrase: q" for p in planets]),
        "centers": "Center data was not available in the source PDF, so this section cannot be interpreted reliably from the current file.",
        "channels": "There are no defined channels available in this report.",
        "tone_of_voice": "| Area | Note |\n|---|---|\n| 💼 Business | Clear offers |\n-\n•\n",
        "business": "1. First action\n2. Second action",
        "summary": "1. **Start simple**\n2. Keep rhythm\n---\nCalm closing note",
    }
    return {
        "chart": {"type": "Generator", "strategy": "Responding", "authority": "Sacral", "profile": "3/5", "definition": "Single", "incarnation_cross": "Right Angle Cross", "personality": personality, "design": design, "channels": [], "centers": {"Head": None, "Ajna": None}},
        "blocks": blocks,
        "language": "en",
        "client_name": "Artur",
        "generated_date": "2026-05-18",
    }


def test_language_aliases_and_ambiguous_uk():
    for value in ["ua", "ukr", "ukrainian", "українська", "украинский", "ukrainian language"]:
        assert normalize_language(value) == "ua"
    for value in ["ru", "rus", "russian", "русский"]:
        assert normalize_language(value) == "ru"
    for value in ["en", "eng", "english"]:
        assert normalize_language(value) == "en"

    try:
        normalize_language("uk")
        assert False, "uk must be ambiguous"
    except ValueError as exc:
        assert str(exc) == "ambiguous_uk"


def test_gate_theme_lookup_ignores_line_suffix():
    chart = {"personality": {"Sun": "46.5"}, "design": {"Sun": "52.1"}}
    rows = _build_activation_map(chart)
    assert rows[0]["personality"]["theme"] == "Embodiment / love of the body"
    assert rows[0]["design"]["theme"] == "Stillness / concentration"


def test_rendered_planet_card_count_and_cleanup():
    with TemporaryDirectory() as td:
        html = render_html(_mock_context(), Path(td) / "report.html")
    assert html.count("class='planet-card'") == 13
    assert "###" not in html and "**" not in html and "---" not in html
    assert "<li></li>" not in html


def test_channels_safety_wording_enforced():
    with TemporaryDirectory() as td:
        html = render_html(_mock_context(), Path(td) / "report.html")
    assert "should be treated as unavailable" in html
    banned = ["no defined channels", "channels are absent", "каналы отсутствуют"]
    for word in banned:
        assert word not in html.lower()


def test_activation_map_includes_theme_text():
    with TemporaryDirectory() as td:
        html = render_html(_mock_context(), Path(td) / "report.html")
    assert "Creative self-expression" in html
    assert "activation-theme" in html
