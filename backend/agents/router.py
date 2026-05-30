from __future__ import annotations

import logging

from backend.graphs.state import DisasterState
from backend.services.risk_mapping import select_department

logger = logging.getLogger(__name__)

DEPARTMENT_ROUTE_KEYS = {
    "Public Works": "public_works",
    "Civil Defense": "civil_defense",
    "Emergency Response": "emergency_response",
    "None": "none",
}


def routing_node(state: DisasterState) -> DisasterState:
    run_id = state.get("run_id")
    prediction = state.get("disaster_prediction") or {}
    # Route based on severity (LLM authoritative)
    severity = (state.get("severity") or "").upper()
    mapping = {
        "LOW": "None",
        "MEDIUM": "Public Works",
        "HIGH": "Civil Defense",
        "CRITICAL": "Emergency Response",
    }
    department = mapping.get(severity, "Public Works")

    logger.info("Routing decision: severity=%s -> department=%s", severity, department)
    logger.info(
        "Router state (run_id=%s, most_likely=%s, severity=%s)",
        run_id,
        prediction.get("most_likely"),
        severity,
    )

    routing_reason = f"Severity {severity} routed to {department}."
    return {"routed_department": department, "routing_reason": routing_reason}


def route_from_department(state: DisasterState) -> str:
    department = state.get("routed_department") or "Public Works"
    return DEPARTMENT_ROUTE_KEYS.get(department, "public_works")
