from __future__ import annotations

import logging
from typing import List

from backend.graphs.state import DisasterState
from backend.memory.memory_store import store_rule

logger = logging.getLogger(__name__)


def memory_update_node(state: DisasterState) -> DisasterState:
    # Prefer derived insights produced by the reflection node
    derived = state.get("derived_rule")
    feedback = state.get("feedback")
    memory_rules = list(state.get("memory_rules") or [])
    department = state.get("routed_department") or "Unknown"
    run_id = state.get("run_id")

    rule_to_store = None
    if derived:
        rule_to_store = derived
    elif feedback:
        # fallback - wrap raw feedback into concise form
        rule_to_store = f"Incorporate feedback: {feedback}"

    if rule_to_store:
        memory_rules.append(rule_to_store)
        store_rule(department, rule_to_store, run_id=run_id)
        logger.info("Memory updated with derived insight")

    # Preserve routing and run context when returning so the workflow can re-route correctly
    return {"memory_rules": memory_rules, "routed_department": department, "run_id": run_id}
