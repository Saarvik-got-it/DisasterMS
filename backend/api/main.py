from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional in prod
    load_dotenv = None

from backend.agents.human_gatekeeper import get_pending, set_decision
from backend.graphs.workflow import build_graph
from backend.memory.rules import DEFAULT_MEMORY_RULES
from backend.memory.memory_store import load_rules
from backend.models.schemas import (
    ApprovalRequest,
    ApprovalResponse,
    MemoryRulesResponse,
    PendingApprovalResponse,
    RunHistoryResponse,
    RunRequest,
    RunResponse,
)
from backend.services.run_history import append_run_log, load_run_history
from backend.validation.state_validator import validate_and_repair_state

author = "DisasterMS"

app = FastAPI(title="Autonomous Disaster Management System", version="0.1.0")
logger = logging.getLogger(author)

if load_dotenv is not None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=env_path, override=False)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_graph = build_graph()


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
def run_workflow(payload: RunRequest) -> RunResponse:
    run_id = str(uuid.uuid4())
    initial_state = {
        "run_id": run_id,
        "location": {
            "latitude": payload.lat,
            "longitude": payload.lon,
            "name": payload.location_name,
        },
        "memory_rules": DEFAULT_MEMORY_RULES,
    }
    try:
        result = _graph.invoke(initial_state)
    except Exception as exc:
        logger.exception("Workflow failed")
        raise HTTPException(status_code=500, detail="Workflow failed") from exc
    result = validate_and_repair_state(result)
    append_run_log(
        {
            "run_id": run_id,
            "location_name": payload.location_name,
            "latitude": payload.lat,
            "longitude": payload.lon,
            "severity": result.get("severity"),
            "routed_department": result.get("routed_department"),
            "approval_status": result.get("approval_status"),
            "most_likely": (result.get("disaster_prediction") or {}).get("most_likely"),
        }
    )
    return RunResponse(state=result)


@app.post("/approve", response_model=ApprovalResponse)
def approve_alert(payload: ApprovalRequest) -> ApprovalResponse:
    set_decision(payload.run_id, "APPROVED", payload.feedback)
    return ApprovalResponse(status="APPROVED", run_id=payload.run_id, feedback=payload.feedback)


@app.post("/reject", response_model=ApprovalResponse)
def reject_alert(payload: ApprovalRequest) -> ApprovalResponse:
    set_decision(payload.run_id, "REJECTED", payload.feedback)
    return ApprovalResponse(status="REJECTED", run_id=payload.run_id, feedback=payload.feedback)


@app.get("/memory", response_model=MemoryRulesResponse)
def get_memory_rules() -> MemoryRulesResponse:
    return MemoryRulesResponse(rules=load_rules())


@app.get("/runs", response_model=RunHistoryResponse)
def get_run_history() -> RunHistoryResponse:
    return RunHistoryResponse(runs=load_run_history())


@app.get("/pending", response_model=PendingApprovalResponse)
def get_pending_approval() -> PendingApprovalResponse:
    pending = get_pending()
    return PendingApprovalResponse(pending=pending)
