from pathlib import Path
from tempfile import TemporaryDirectory

from build_pdf import render_html


def _mock_context():
    planets = [
        "Sun", "Earth", "Moon", "North Node", "South Node", "Mercury",
        "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"
    ]
    personality = {p: f"{i+1}.1" for i, p in enumerate(planets)}
    design = {p: f"{i+2}.2" for i, p in enumerate(planets)}
    emojis = {"Sun":"☀️","Earth":"🌍","Moon":"🌙","North Node":"🧭","South Node":"🪞","Mercury":"🗣️","Venus":"💚","Mars":"🔥","Jupiter":"📈","Saturn":"🪨","Uranus":"⚡","Neptune":"🌫️","Pluto":"🦂"}
    blocks = {
        "overview": "Type Generator\nStrategy Responding\nAuthority Sacral\nProfile 3/5\nDefinition Single\nIncarnation Cross Right Angle Cross\n- Theme one\n- Theme two",
        "type_strategy_authority": "Type: Generator\nStrategy: Responding\nAuthority: Sacral",
        "profile": "Profile 3/5\nStrengths and practical guidance",
        "planetary_activations": "\n".join([f"{emojis[p]} {p} — Role\nRole of {p}: message\n🧭 Synthesis\nPersonality: Gate {personality[p]}\nDesign: Gate {design[p]}\n🪞 Reflection: r\n🔑 Quantum Phrase: q" for p in planets]),
        "centers": "Center data was not available in the source PDF, so this section cannot be interpreted reliably from the current file.",
        "channels": "Channel data was not available or was not extracted from the source PDF, so this section should be treated as unavailable.",
        "tone_of_voice": "| Area | Note |\n|---|---|\n| 💼 Business | Clear offers |\n-\n•\n",
        "business": "1. First action\n2. Second action",
        "summary": "1. **Start simple**\n2. Keep rhythm\n---\nCalm closing note",
    }
    return {
        "chart": {
            "type": "Generator", "strategy": "Responding", "authority": "Sacral", "profile": "3/5",
            "definition": "Single", "incarnation_cross": "Right Angle Cross",
            "personality": personality, "design": design, "channels": [],
            "centers": {"Head": None, "Ajna": None},
        },
        "blocks": blocks,
        "language": "en",
        "client_name": "Artur",
        "generated_date": "2026-05-18",
    }


def test_template_contains_required_classes():
    template = Path("templates/report.html").read_text(encoding="utf-8")
    required = [
        "cover", "snapshot-grid", "snapshot-card", "activation-map", "activation-column", "activation-item",
        "planet-card", "planet-header", "subsection", "reflection-box", "quantum-box"
    ]
    for cls in required:
        assert cls in template


def test_rendered_planet_card_count_and_cleanup():
    context = _mock_context()
    with TemporaryDirectory() as td:
        html = render_html(context, Path(td) / "report.html")

    assert html.count("class='planet-card'") == 13
    assert "###" not in html
    assert "**" not in html
    assert "---" not in html
    assert "<li></li>" not in html


def test_overview_has_no_activation_duplication_terms():
    context = _mock_context()
    context["blocks"]["overview"] = "Type Generator\nStrategy Responding\nAuthority Sacral\nProfile 3/5\nDefinition Single\nIncarnation Cross Right Angle Cross\nTheme A\nTheme B"
    with TemporaryDirectory() as td:
        html = render_html(context, Path(td) / "report.html")
    banned = ["Планеты личности", "Планеты дизайна", "Personality Activations", "Design Activations"]
    overview_section = html.split("🔹 Overview", 1)[1].split("⚡ Type / Strategy / Authority", 1)[0]
    for word in banned:
        assert word not in overview_section


def test_centers_channels_safety_messages_present():
    context = _mock_context()
    with TemporaryDirectory() as td:
        html = render_html(context, Path(td) / "report.html")

    assert "cannot be interpreted reliably" in html
    assert "should be treated as unavailable" in html
    banned = ["центры не активированы", "all centers are undefined", "all centers are open", "каналы отсутствуют"]
    for word in banned:
        assert word not in html


def test_activation_map_has_theme_unavailable_fallback():
    context = _mock_context()
    with TemporaryDirectory() as td:
        html = render_html(context, Path(td) / "report.html")

    assert "Theme unavailable" in html
    assert "activation-theme" in html
