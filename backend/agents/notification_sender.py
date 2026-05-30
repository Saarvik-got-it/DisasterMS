from __future__ import annotations

import logging

from backend.graphs.state import DisasterState

logger = logging.getLogger(__name__)


def send_alert_node(state: DisasterState) -> DisasterState:
    run_id = state.get("run_id")
    alert = state.get("generated_alert") or ""
    action_plan = state.get("action_plan") or []
    department = state.get("routed_department") or "Unknown"

    logger.info("Sending alert for %s (run_id=%s)", department, run_id)
    logger.info("Generated alert: %s", alert)
    logger.info("Action plan: %s", action_plan)

    return {}
