from __future__ import annotations

import logging
import os
import threading
from typing import Any, Dict, List, Optional, Union

from backend.graphs.state import DisasterState

logger = logging.getLogger(__name__)

_decision_lock = threading.Lock()
_decision_events: Dict[str, threading.Event] = {}
_decision_store: Dict[str, Dict[str, Any]] = {}
_pending_lock = threading.Lock()
_pending_store: Dict[str, Dict[str, Any]] = {}


def set_decision(run_id: str, status: str, feedback: Optional[str] = None) -> None:
    normalized = status.strip().upper()
    if normalized not in {"APPROVED", "REJECTED"}:
        raise ValueError("Approval status must be APPROVED or REJECTED")

    with _decision_lock:
        _decision_store[run_id] = {"status": normalized, "feedback": feedback}
        event = _decision_events.get(run_id)
        if event is None:
            event = threading.Event()
            _decision_events[run_id] = event
        event.set()


def await_human_decision(run_id: str, default_timeout: int = 900) -> Dict[str, Any]:
    mode = os.getenv("APPROVAL_MODE", "api").lower()
    if mode == "terminal":
        decision = input("Approve alert? (approve/reject): ").strip().lower()
        status = "APPROVED" if decision.startswith("a") else "REJECTED"
        feedback = input("Feedback (optional): ").strip()
        with _pending_lock:
            _pending_store.pop(run_id, None)
        return {"approval_status": status, "feedback": feedback or None}

    timeout = int(os.getenv("APPROVAL_TIMEOUT_SECONDS", str(default_timeout)))
    with _decision_lock:
        event = _decision_events.get(run_id)
        if event is None:
            event = threading.Event()
            _decision_events[run_id] = event

    received = event.wait(timeout=timeout)
    if not received:
        raise TimeoutError("Approval decision timed out")

    with _decision_lock:
        decision = _decision_store.pop(run_id, {})
        status = decision.get("status") or "REJECTED"
        feedback = decision.get("feedback")
        event = _decision_events.pop(run_id, None)
        if event:
            event.clear()

    with _pending_lock:
        _pending_store.pop(run_id, None)

    return {"approval_status": status, "feedback": feedback}


def set_pending(payload: Dict[str, Any]) -> None:
    run_id = payload.get("run_id")
    if not run_id:
        raise ValueError("run_id is required to set pending approval")
    with _pending_lock:
        _pending_store[run_id] = payload


def get_pending(run_id: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    with _pending_lock:
        if run_id:
            return dict(_pending_store.get(run_id, {}))
        return list(_pending_store.values())


def approval_route(state: DisasterState) -> str:
    status = (state.get("approval_status") or "").upper()
    return "approved" if status == "APPROVED" else "rejected"


def human_gatekeeper_node(state: DisasterState) -> DisasterState:
    run_id = state.get("run_id") or ""
    if not run_id:
        raise ValueError("run_id is required for approval flow")
    department = state.get("routed_department") or "Unknown"
    severity = state.get("severity") or ""
    alert = state.get("generated_alert") or ""
    action_plan = state.get("action_plan") or []

    set_pending(
        {
            "run_id": run_id,
            "routed_department": department,
            "severity": severity,
            "generated_alert": alert,
            "action_plan": action_plan,
        }
    )

    logger.info(
        "Gatekeeper review for %s (severity: %s, run_id=%s)",
        department,
        severity,
        run_id,
    )
    decision = await_human_decision(run_id)

    logger.info("Approval status: %s", decision.get("approval_status"))
    if decision.get("feedback"):
        logger.info("Feedback: %s", decision.get("feedback"))

    # Merge the approval decision into the full state so downstream nodes retain context
    merged = dict(state)
    merged.update(decision)
    return merged
