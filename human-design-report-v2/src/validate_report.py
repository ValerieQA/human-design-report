import re
from typing import Dict, Set

from schemas import ChartData, ValidationResult, PLANETS


def _collect_gate_lines(chart: ChartData) -> Set[str]:
    values = set()
    for side in [chart.personality, chart.design]:
        for v in side.values():
            if v:
                values.add(v)
    return values


def validate_report(chart: ChartData, blocks: Dict[str, str]) -> ValidationResult:
    text = "\n".join(blocks.values())
    errors = []
    source_gate_lines = _collect_gate_lines(chart)
    mentioned = set(re.findall(r"\b\d{1,2}\.\d\b", text))

    missing = sorted(source_gate_lines - mentioned)
    extra = sorted(mentioned - source_gate_lines)
    if missing:
        errors.append(f"Missing Gate.Line values: {missing}")
    if extra:
        errors.append(f"Hallucinated Gate.Line values: {extra}")

    for key in ["type", "strategy", "authority", "profile", "definition"]:
        val = getattr(chart, key)
        if val and val.lower() not in text.lower():
            errors.append(f"{key} mismatch or absent: {val}")

    for planet in PLANETS:
        if planet.lower() not in text.lower():
            errors.append(f"Planet not included: {planet}")

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=[])
