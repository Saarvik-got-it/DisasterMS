from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

RUNS_PATH = Path(__file__).resolve().parents[1] / "storage" / "data" / "runs_log.json"


def _load_runs(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError:
        logger.warning("Runs log is invalid JSON: %s", path)
        return []

    if isinstance(data, list):
        return data
    logger.warning("Runs log has unexpected format: %s", path)
    return []


def load_run_history(path: Path = RUNS_PATH) -> List[Dict[str, Any]]:
    return _load_runs(path)


def append_run_log(entry: Dict[str, Any], path: Path = RUNS_PATH) -> Dict[str, Any]:
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(), **entry}
    runs = _load_runs(path)
    runs.append(payload)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(runs, handle, indent=2)

    logger.info("Run logged: %s", payload)
    return payload
