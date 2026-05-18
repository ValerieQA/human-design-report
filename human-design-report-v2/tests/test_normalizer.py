from normalize_chart import normalize_chart_data


def test_normalizer_extracts_fields():
    text = (
        "Type: Generator\nStrategy: To Respond\nAuthority: Sacral\nProfile: 4/6\nDefinition: Single\n"
        "Personality:\nSun: 44.5\nDesign:\nSun: 7.1"
    )
    chart = normalize_chart_data(text)
    assert chart.type == "Generator"
    assert chart.authority == "Sacral"
    assert chart.personality.get("Sun") == "44.5"
