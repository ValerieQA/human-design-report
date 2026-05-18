from pathlib import Path
from tempfile import TemporaryDirectory

from build_pdf import LABELS, render_html, validate_report_structure
from schemas import PLANETS


def _chart(include_chiron=False):
    planets = [p for p in PLANETS if p != "Chiron"]
    personality = {p: f"{i+1}.1" for i, p in enumerate(planets)}
    design = {p: f"{i+2}.2" for i, p in enumerate(planets)}
    if include_chiron:
        personality["Chiron"] = "62.1"
        design["Chiron"] = None
    return {"type":"Generator","strategy":"Responding","authority":"Sacral","profile":"5/1","definition":"Single","incarnation_cross":"Right Angle Cross","personality": personality, "design": design, "channels": [], "centers": {"Head": None, "Ajna": None}}


def _cards(chart):
    cards = []
    for p in PLANETS:
        if chart["personality"].get(p) or chart["design"].get(p):
            cards.append({"planet": p, "emoji": "🪐", "role":"role", "personality_gate": chart["personality"].get(p), "design_gate": chart["design"].get(p), "content": f"{p} content"})
    return cards


def _context(chart, language="en"):
    return {
        "chart": chart,
        "planet_cards": _cards(chart),
        "blocks": {
            "overview": "Type Generator\nStrategy Responding\nAuthority Sacral\nProfile 5/1\nDefinition Single\nIncarnation Cross Right Angle Cross\n- Theme one\n- Theme two",
            "type_strategy_authority": "Type: Generator\nStrategy: Responding\nAuthority: Sacral",
            "profile": "Line 5 meaning\nLine 1 meaning\nStrengths\nChallenges\nPractical guidance",
            "centers": "Center data was not available in the source PDF, so this section cannot be interpreted reliably from the current file.",
            "channels": "Channel data was not available or was not extracted from the source PDF, so this section should be treated as unavailable.",
            "tone_of_voice": "Ген Кі\nОсобистісний Вхід 46.5\nТінь: приклад\nДар: приклад\nСіддхі: приклад",
            "business": "Business guidance without center assumptions",
            "summary": "Type, Strategy, Authority, Profile, Incarnation Cross, and practical next steps",
        },
        "language": language,
        "client_name": "A",
        "generated_date": "2026-05-18",
    }


def test_section_order_and_uniqueness():
    with TemporaryDirectory() as td:
        html = render_html(_context(_chart(False), "en"), Path(td) / "r.html")
    order = [
        f"<h2>{LABELS['en']['core']}</h2>", f"<h2>{LABELS['en']['activation_map']}</h2>", f"<h2>{LABELS['en']['overview']}</h2>",
        f"<h2>{LABELS['en']['tsa']}</h2>", f"<h2>{LABELS['en']['profile']}</h2>", f"<h2>{LABELS['en']['planets']}</h2>",
        f"<h2>{LABELS['en']['centers']}</h2>", f"<h2>{LABELS['en']['channels']}</h2>", f"<h2>{LABELS['en']['tone']}</h2>",
        f"<h2>{LABELS['en']['business']}</h2>", f"<h2>{LABELS['en']['summary']}</h2>",
    ]
    positions = [html.find(x) for x in order]
    assert all(p != -1 for p in positions)
    assert positions == sorted(positions)
    assert html.count(LABELS['en']['planets']) == 1


def test_planet_cards_count_and_values():
    chart = _chart(False)
    with TemporaryDirectory() as td:
        html = render_html(_context(chart), Path(td) / "r.html")
    assert html.count('class="planet-card"') == 13
    for p in ["Sun","Earth","Moon","North Node","South Node","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto"]:
        assert p in html
        assert chart["personality"][p] in html
        assert chart["design"][p] in html


def test_chiron_rules():
    with TemporaryDirectory() as td:
        html1 = render_html(_context(_chart(False)), Path(td) / "a.html")
    assert "Chiron" not in html1

    with TemporaryDirectory() as td:
        html2 = render_html(_context(_chart(True)), Path(td) / "b.html")
    assert "Chiron" in html2


def test_validation_fails_on_missing_planet_card():
    chart = _chart(False)
    ctx = _context(chart)
    ctx["planet_cards"] = ctx["planet_cards"][:-1]
    with TemporaryDirectory() as td:
        try:
            render_html(ctx, Path(td) / "r.html")
            assert False
        except ValueError as exc:
            assert "Report structure validation failed" in str(exc)


def test_no_duplicate_planet_lists_and_no_unsafe_claims():
    chart = _chart(False)
    with TemporaryDirectory() as td:
        html = render_html(_context(chart), Path(td) / "r.html")
    overview_chunk = html.split('id="overview"',1)[1].split('id="type-strategy-authority"',1)[0]
    profile_chunk = html.split('id="profile"',1)[1].split('id="planetary-activations"',1)[0]
    banned_dup = ["Планеты личности", "Планеты дизайна", "Personality Activations", "Design Activations"]
    for b in banned_dup:
        assert b not in overview_chunk
        assert b not in profile_chunk
    for b in ["centers are absent", "there are no defined channels"]:
        assert b.lower() not in html.lower()
    assert "snapshot-card" in html
    assert "activation-card" in html
    assert "Ген Кі" not in html and "Вхід" not in html and "Воротар" not in html
    assert "Gene Keys" in html and "Shadow —" in html and "Gift —" in html and "Siddhi —" in html


def test_validation_function_direct_failure():
    chart = _chart(False)
    bad_html = "<h2>Planetary Activations</h2><div class='planet-card'>Sun 1.1 2.2</div><h2>Final Summary</h2>"
    try:
        validate_report_structure(chart, bad_html)
        assert False
    except ValueError:
        assert True


def test_localized_labels_render():
    with TemporaryDirectory() as td:
        ru_html = render_html(_context(_chart(False), "ru"), Path(td) / "ru.html")
        ua_html = render_html(_context(_chart(False), "ua"), Path(td) / "ua.html")
    assert LABELS["ru"]["core"] in ru_html and LABELS["ru"]["summary"] in ru_html
    assert LABELS["ua"]["core"] in ua_html and LABELS["ua"]["summary"] in ua_html
