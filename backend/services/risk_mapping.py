from __future__ import annotations

from typing import Mapping, Tuple

ALLOWED_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

DEPARTMENT_BY_HAZARD = {
    "Normal": "None",
    "Flood": "Public Works",
    "Heatwave": "Civil Defense",
    "Storm": "Emergency Response",
}


def _confidence_for_hazard(prediction: Mapping[str, float]) -> Tuple[str, float]:
    hazard = str(prediction.get("most_likely") or "")
    if not hazard:
        return "", 0.0
    try:
        confidence = float(prediction.get(hazard, 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    return hazard, confidence


def select_department(prediction: Mapping[str, float]) -> str:
    hazard, _ = _confidence_for_hazard(prediction)
    if not hazard:
        return "None"
    return DEPARTMENT_BY_HAZARD.get(hazard, "Public Works")


def select_severity(prediction: Mapping[str, float]) -> str:
    hazard, confidence = _confidence_for_hazard(prediction)
    if not hazard or hazard == "Normal":
        return "LOW"
    if hazard == "Flood":
        return "HIGH" if confidence >= 0.7 else "MEDIUM"
    if hazard == "Heatwave":
        return "HIGH" if confidence >= 0.7 else "MEDIUM"
    if hazard == "Storm":
        return "CRITICAL"
    return "MEDIUM"
