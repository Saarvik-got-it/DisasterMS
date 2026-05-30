from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class DisasterState(TypedDict, total=False):
    run_id: str
    location: Dict[str, Any]
    weather_data: List[Dict[str, Any]]
    forecast: Dict[str, Any]
    disaster_prediction: Dict[str, Any]
    news_context: List[str]
    severity: str
    severity_reason: str
    routed_department: str
    generated_alert: str
    action_plan: List[str]
    feedback: str
    approval_status: str
    memory_rules: List[str]
