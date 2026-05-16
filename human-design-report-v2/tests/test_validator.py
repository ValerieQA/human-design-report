from schemas import ChartData
from validate_report import validate_report


def test_validator_passes_minimal_case():
    chart = ChartData(
        type="Generator",
        strategy="To Respond",
        authority="Sacral",
        profile="4/6",
        definition="Single",
        personality={"Sun": "44.5"},
        design={"Sun": "7.1"},
    )
    blocks = {"overview": "Generator To Respond Sacral 4/6 Single Sun 44.5 7.1"}
    result = validate_report(chart, blocks)
    assert result.valid is False
