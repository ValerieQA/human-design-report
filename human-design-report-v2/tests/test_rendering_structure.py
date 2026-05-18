from pathlib import Path
from tempfile import TemporaryDirectory

from build_pdf import render_html, validate_planetary_rendering
from schemas import PLANETS


def _chart(include_chiron=False):
    planets = [p for p in PLANETS if p != "Chiron"]
    personality = {p: f"{i+1}.1" for i,p in enumerate(planets)}
    design = {p: f"{i+2}.2" for i,p in enumerate(planets)}
    if include_chiron:
        personality["Chiron"] = "62.1"
        design["Chiron"] = None
    return {"personality": personality, "design": design, "channels": [], "centers": {"Head": None}}


def _cards(chart):
    cards=[]
    for p in PLANETS:
        if chart["personality"].get(p) or chart["design"].get(p):
            cards.append({"planet":p,"emoji":"🪐","personality_gate":chart["personality"].get(p),"design_gate":chart["design"].get(p),"content":f"{p} content"})
    return cards


def _context(chart):
    return {
        "chart": chart,
        "planet_cards": _cards(chart),
        "blocks": {"overview":"ok","type_strategy_authority":"ok","profile":"ok","centers":"ok","channels":"no defined channels","tone_of_voice":"ok","business":"ok","summary":"ok"},
        "language":"en","client_name":"A","generated_date":"2026-05-18"
    }


def test_render_13_planet_cards_and_activations_present():
    chart=_chart(False)
    with TemporaryDirectory() as td:
        html=render_html(_context(chart), Path(td)/"r.html")
    assert html.count('class="planet-card"')==13
    for p in ["Sun","Earth","Moon","North Node","South Node","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto"]:
        assert p in html
        assert chart["personality"][p] in html
        assert chart["design"][p] in html


def test_missing_planet_card_validation_fails():
    chart=_chart(False)
    ctx=_context(chart)
    ctx["planet_cards"]=ctx["planet_cards"][:-1]
    with TemporaryDirectory() as td:
        try:
            render_html(ctx, Path(td)/"r.html")
            assert False
        except ValueError as exc:
            assert "Planetary rendering validation failed" in str(exc)


def test_chiron_skipped_when_null_and_included_when_present():
    c1=_chart(False)
    with TemporaryDirectory() as td:
        html1=render_html(_context(c1), Path(td)/"a.html")
    assert "Chiron" not in html1

    c2=_chart(True)
    with TemporaryDirectory() as td:
        html2=render_html(_context(c2), Path(td)/"b.html")
    assert "Chiron" in html2


def test_validation_function_direct():
    chart=_chart(False)
    html='<div class="planet-card">Sun 1.1 2.2</div>'
    try:
        validate_planetary_rendering(chart, html)
        assert False
    except ValueError:
        assert True
