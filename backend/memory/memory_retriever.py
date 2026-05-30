from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from backend.memory.memory_store import RULES_PATH

logger = logging.getLogger(__name__)


def _load_rules(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError:
        logger.warning("Rules file is invalid JSON: %s", path)
        return []

    if isinstance(data, list):
        return data
    logger.warning("Rules file has unexpected format: %s", path)
    return []


def retrieve_rules(department: str, limit: int = 5, path: Path = RULES_PATH) -> List[str]:
    rules = _load_rules(path)
    department = department.strip()

    filtered = [item for item in rules if item.get("department") == department]
    rule_texts = [item.get("rule") for item in filtered if item.get("rule")]
    if limit > 0:
        rule_texts = rule_texts[-limit:]

    logger.info("Retrieved memories: %s", rule_texts)
    return rule_texts


def retrieve_recent_insights(limit: int = 5, path: Path = RULES_PATH) -> List[str]:
    rules = _load_rules(path)
    if not rules:
        return []
    # Return last `limit` rule texts across departments
    rule_texts = [item.get("rule") for item in rules if item.get("rule")]
    return rule_texts[-limit:]
