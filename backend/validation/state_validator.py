from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Mapping

from backend.agents.news_monitor import filter_relevant_headlines
from backend.services.alert_builder import build_alert_message
from backend.services.risk_mapping import ALLOWED_SEVERITIES, select_department, select_severity

logger = logging.getLogger(__name__)


def _clamp_non_negative(value: float) -> float:
    return max(0.0, float(value))


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _alert_needs_regen(alert: str, hazard: str, severity: str) -> bool:
    lower = (alert or "").lower()
    if not lower:
        return True
    if hazard and hazard.lower() not in lower:
        return True
    if severity and severity.lower() not in lower:
        return True
    if "confidence" not in lower:
        return True
    return False


def validate_and_repair_state(state: Dict[str, Any]) -> Dict[str, Any]:
    updated = copy.deepcopy(state)

    forecast = updated.get("forecast") or {}
    points = forecast.get("points") or []
    clamped_points: List[Dict[str, Any]] = []
    rainfall_changed = False
    for point in points:
        rainfall = _clamp_non_negative(_safe_float(point.get("rainfall")))
        lower = _clamp_non_negative(_safe_float(point.get("rainfall_lower")))
        upper = _clamp_non_negative(_safe_float(point.get("rainfall_upper")))
        if rainfall != point.get("rainfall") or lower != point.get("rainfall_lower"):
            rainfall_changed = True
        clamped_points.append(
            {
                "time": point.get("time"),
                "rainfall": rainfall,
                "rainfall_lower": lower,
                "rainfall_upper": upper,
            }
        )

    if rainfall_changed:
        logger.warning("Validation: clamped negative rainfall values in forecast points")
        forecast["points"] = clamped_points

    features = forecast.get("features") or {}
    predicted = features.get("predicted_rainfall")
    if predicted is not None:
        predicted_value = _clamp_non_negative(_safe_float(predicted))
        if predicted_value != predicted:
            logger.warning("Validation: clamped predicted rainfall from %s to %.2f", predicted, predicted_value)
        features["predicted_rainfall"] = predicted_value
        forecast["features"] = features

    prediction = updated.get("disaster_prediction") or {}
    current_severity = (updated.get("severity") or "").upper()
    # Only correct severity when it's missing or invalid. Do NOT overwrite valid LLM outputs.
    if current_severity not in ALLOWED_SEVERITIES:
        logger.warning(
            "Validation: severity missing or invalid (%s). Setting default to LOW.", current_severity or "(missing)"
        )
        updated["severity"] = "LOW"

    # Do not force routed_department from classifier prediction. Use existing routed_department if present.
    desired_department = select_department(prediction)
    current_department = updated.get("routed_department")

    location = updated.get("location") or {}
    headlines = updated.get("news_context") or []
    if headlines:
        filtered = filter_relevant_headlines(
            [{"title": headline} for headline in headlines],
            location,
            limit=min(len(headlines), 5),
        )
        if filtered != headlines:
            logger.warning(
                "Validation: filtered news headlines (before=%s, after=%s)",
                len(headlines),
                len(filtered),
            )
            updated["news_context"] = filtered

    # Determine effective department: prefer router result, otherwise fallback to classifier mapping
    effective_department = current_department if current_department is not None else desired_department
    if effective_department == "None":
        if updated.get("generated_alert") or updated.get("action_plan"):
            logger.warning("Validation: clearing alert output for Normal prediction")
        updated["generated_alert"] = ""
        updated["action_plan"] = []
        return updated

    hazard = prediction.get("most_likely", "Hazard")
    severity = updated.get("severity")
    try:
        confidence = float(prediction.get(hazard)) if hazard in prediction else None
    except (TypeError, ValueError):
        confidence = None

    alert = updated.get("generated_alert") or ""
    action_plan = updated.get("action_plan") or []
    # Use the routed department if present otherwise fall back to classifier-derived department
    department_for_alert = current_department if current_department is not None else desired_department

    if _alert_needs_regen(alert, hazard, severity):
        logger.warning("Validation: regenerating alert message for consistency")
        updated["generated_alert"] = build_alert_message(
            department=department_for_alert,
            location_label=location.get("name") or "unknown location",
            risk_type=hazard,
            severity=severity,
            confidence=confidence,
            action_plan=action_plan,
        )

    return updated
