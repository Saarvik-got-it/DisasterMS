from __future__ import annotations

import logging

from backend.graphs.state import DisasterState

logger = logging.getLogger(__name__)


def reflection_node(state: DisasterState) -> DisasterState:
    feedback = (state.get("feedback") or "").strip()
    department = state.get("routed_department") or "Unknown"
    run_id = state.get("run_id")

    logger.info("Reflection requested for %s (run_id=%s)", department, run_id)
    logger.info("Feedback: %s", feedback or "(none)")

    # Simple deterministic insight extraction heuristics.
    # If feedback contains an instruction like 'include X' or 'add X', normalize it to
    # a derived_rule: 'Always include X.' Otherwise, store a concise incorporation rule.
    derived_rule = None
    lower = feedback.lower()
    import re

    m = re.search(r"(?:include|add|always include|please include)\s+(.+?)(?:\.|$)", lower)
    if m:
        candidate = m.group(1).strip()
        # Capitalize first letter and ensure trailing period
        candidate = candidate.rstrip(". ")
        derived_rule = f"Always include {candidate}."
    else:
        if feedback:
            # fallback concise form
            derived_rule = feedback[0].upper() + feedback[1:]
            if not derived_rule.endswith("."):
                derived_rule = derived_rule + "."
        else:
            derived_rule = "No actionable insight provided."

    logger.info("Derived rule: %s", derived_rule)

    return {"derived_rule": derived_rule}
