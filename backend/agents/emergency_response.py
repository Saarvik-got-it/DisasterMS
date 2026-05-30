from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping

from backend.graphs.state import DisasterState
from backend.services.alert_builder import build_alert_message
from backend.memory.memory_retriever import retrieve_rules

logger = logging.getLogger(__name__)


def _location_label(location: Mapping[str, Any]) -> str:
    name = location.get("name")
    if name:
        return str(name)
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    if latitude is None or longitude is None:
        return "unknown location"
    return f"{latitude:.4f},{longitude:.4f}"


def _headline_summary(news_context: List[str], limit: int = 2) -> str:
    if not news_context:
        return "No relevant headlines."
    return "; ".join(news_context[:limit])


def emergency_response_node(state: DisasterState) -> DisasterState:
    location = state.get("location") or {}
    severity = (state.get("severity") or "LOW").upper()
    run_id = state.get("run_id")
    news_context = state.get("news_context") or []
    forecast = state.get("forecast") or {}
    features = forecast.get("features") or {}
    prediction = state.get("disaster_prediction") or {}
    feedback = state.get("feedback")

    rules = retrieve_rules("Emergency Response")

    hazard = prediction.get("most_likely", "Hazard")
    try:
        confidence = float(prediction.get(hazard)) if hazard in prediction else None
    except (TypeError, ValueError):
        confidence = None
    location_label = _location_label(location)

    action_plan = [
        "Activate emergency operations center and incident command.",
        "Issue evacuation advisories for high-risk zones and open shelters.",
        "Deploy medical and rescue teams; stage ambulances and supplies.",
        "Coordinate emergency communications and public alerts.",
        "Work with civil defense and public works on road closures and access control.",
    ]

    if rules:
        logger.info("Applied rules: %s", rules)
        for rule in rules:
            action_plan.append(f"Apply rule: {rule}")

    if feedback:
        action_plan.append(f"Incorporate feedback: {feedback}")

    alert_message = build_alert_message(
        department="Emergency Response",
        location_label=location_label,
        risk_type=hazard,
        severity=severity,
        confidence=confidence,
        action_plan=action_plan,
    )

    logger.info("Generated alert: %s", alert_message)
    logger.info("Action plan: %s", action_plan)
    logger.info(
        "Department state (run_id=%s, department=Emergency Response, severity=%s)",
        run_id,
        severity,
    )

    return {
        "generated_alert": alert_message,
        "action_plan": action_plan,
    }
