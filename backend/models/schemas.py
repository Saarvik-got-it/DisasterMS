from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Location(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    name: Optional[str] = None


class WeatherData(BaseModel):
    time: datetime
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: float
    pressure: float


class ForecastPoint(BaseModel):
    time: datetime
    rainfall: float
    rainfall_lower: Optional[float] = None
    rainfall_upper: Optional[float] = None


class ForecastResult(BaseModel):
    horizon_hours: int
    points: List[ForecastPoint]
    plot_path: str


class RunRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    location_name: Optional[str] = None


class RunResponse(BaseModel):
    state: Dict[str, Any]


class SeverityAssessment(BaseModel):
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    reason: str


class ApprovalRequest(BaseModel):
    run_id: str
    feedback: Optional[str] = None


class ApprovalResponse(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    run_id: str
    feedback: Optional[str] = None


class MemoryRule(BaseModel):
    timestamp: datetime
    department: str
    rule: str
    run_id: Optional[str] = None


class MemoryRulesResponse(BaseModel):
    rules: List[MemoryRule]


class RunLogEntry(BaseModel):
    timestamp: datetime
    run_id: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None
    severity: Optional[str] = None
    routed_department: Optional[str] = None
    approval_status: Optional[str] = None
    most_likely: Optional[str] = None


class RunHistoryResponse(BaseModel):
    runs: List[RunLogEntry]


class PendingApproval(BaseModel):
    run_id: Optional[str] = None
    routed_department: Optional[str] = None
    severity: Optional[str] = None
    generated_alert: Optional[str] = None
    action_plan: List[str] = []


class PendingApprovalResponse(BaseModel):
    pending: List[PendingApproval]
