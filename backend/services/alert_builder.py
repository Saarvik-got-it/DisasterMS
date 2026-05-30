from __future__ import annotations

from typing import Iterable, List


def build_alert_message(
    *,
    department: str,
    location_label: str,
    risk_type: str,
    severity: str,
    confidence: float | None,
    action_plan: Iterable[str],
) -> str:
    confidence_text = "n/a"
    if confidence is not None:
        confidence_text = f"{confidence * 100:.0f}%"

    lines: List[str] = [
        f"{department} Advisory",
        f"Location: {location_label}",
        f"Risk Type: {risk_type}",
        f"Severity: {severity.title()}",
        f"Confidence: {confidence_text}",
        "",
        "Recommended Actions:",
    ]

    for action in action_plan:
        lines.append(f"- {action}")

    return "\n".join(lines)
