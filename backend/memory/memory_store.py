from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

RULES_PATH = Path(__file__).resolve().parent / "rules.json"


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


def load_rules(path: Path = RULES_PATH) -> List[Dict[str, Any]]:
    return _load_rules(path)


def store_rule(
    department: str,
    rule: str,
    run_id: Optional[str] = None,
    path: Path = RULES_PATH,
) -> Dict[str, Any]:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "department": department,
        "rule": rule,
        "run_id": run_id,
    }

    rules = _load_rules(path)
    rules.append(entry)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(rules, handle, indent=2)

    logger.info("Stored memory: %s", entry)
    return entry
