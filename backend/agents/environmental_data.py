from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional
import logging
import math
import os
import time

import httpx
import pandas as pd

from backend.graphs.state import DisasterState

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
logger = logging.getLogger(__name__)


def _summarize_series(series: pd.Series) -> Dict[str, float]:
    cleaned = pd.to_numeric(series, errors="coerce").dropna()
    if cleaned.empty:
        return {"count": 0, "min": 0.0, "max": 0.0, "mean": 0.0}
    return {
        "count": float(len(cleaned)),
        "min": float(cleaned.min()),
        "max": float(cleaned.max()),
        "mean": float(cleaned.mean()),
    }


def build_synthetic_weather(hours: int = 72) -> pd.DataFrame:
    now = pd.Timestamp.utcnow().tz_localize("UTC")
    times = pd.date_range(end=now, periods=hours, freq="H")

    temperature = []
    humidity = []
    rainfall = []
    wind_speed = []
    pressure = []

    for idx in range(hours):
        phase = (idx / 24.0) * math.tau
        temperature.append(24 + 3 * math.sin(phase))
        humidity.append(60 + 10 * math.cos(phase))
        rainfall.append(max(0.0, 0.6 * math.sin(phase + 1.0)))
        wind_speed.append(3 + 1.2 * math.sin(phase + 0.5))
        pressure.append(1012 + 2 * math.cos(phase + 0.2))

    return pd.DataFrame(
        {
            "time": times,
            "temperature": temperature,
            "humidity": humidity,
            "rainfall": rainfall,
            "wind_speed": wind_speed,
            "pressure": pressure,
        }
    )


def fetch_environmental_data(
    location: Mapping[str, Any],
    past_days: int = 7,
    forecast_days: int = 2,
    retries: int = 3,
) -> pd.DataFrame:
    if "latitude" not in location or "longitude" not in location:
        raise ValueError("Location must include latitude and longitude")

    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,pressure_msl",
        "past_days": past_days,
        "forecast_days": forecast_days,
        "timezone": "UTC",
    }

    last_error: Optional[Exception] = None
    with httpx.Client(timeout=15) as client:
        for attempt in range(1, retries + 1):
            try:
                response = client.get(OPEN_METEO_URL, params=params)
                response.raise_for_status()
                payload = response.json()
                last_error = None
                break
            except httpx.HTTPError as exc:
                last_error = exc
                status_code = getattr(exc.response, "status_code", "n/a")
                logger.warning(
                    "Open-Meteo request failed (attempt %s/%s, status=%s)",
                    attempt,
                    retries,
                    status_code,
                )
                time.sleep(min(2 * attempt, 5))

    if last_error:
        raise last_error

    hourly = payload.get("hourly", {})
    data = {
        "time": hourly.get("time", []),
        "temperature": hourly.get("temperature_2m", []),
        "humidity": hourly.get("relative_humidity_2m", []),
        "rainfall": hourly.get("precipitation", []),
        "wind_speed": hourly.get("wind_speed_10m", []),
        "pressure": hourly.get("pressure_msl", []),
    }

    frame = pd.DataFrame(data)
    frame["time"] = pd.to_datetime(frame["time"], utc=True)
    frame["rainfall"] = pd.to_numeric(frame["rainfall"], errors="coerce")
    negative_count = int((frame["rainfall"] < 0).sum())
    if negative_count:
        logger.warning("Open-Meteo returned %s negative rainfall values; clamping", negative_count)
        frame["rainfall"] = frame["rainfall"].clip(lower=0)
    return frame


def store_historical_csv(frame: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        existing = pd.read_csv(output_path, parse_dates=["time"])
        combined = pd.concat([existing, frame], ignore_index=True)
        combined.drop_duplicates(subset=["time"], inplace=True)
        combined.sort_values("time", inplace=True)
        combined.to_csv(output_path, index=False)
    else:
        frame.sort_values("time").to_csv(output_path, index=False)

    return output_path


def ingest_environmental_data(state: DisasterState) -> DisasterState:
    location = state.get("location")
    if not location:
        raise ValueError("State missing location")

    run_id = state.get("run_id")
    location_label = location.get("name") or f"{location.get('latitude')},{location.get('longitude')}"
    logger.info("Weather ingest start (run_id=%s, location=%s)", run_id, location_label)

    history_path = Path("backend/storage/data/environmental_history.csv")
    source = "live"
    try:
        frame = fetch_environmental_data(location)
        store_historical_csv(frame, history_path)
    except httpx.HTTPError as exc:
        logger.warning(
            "Open-Meteo unavailable (run_id=%s, location=%s). Falling back to cached data. Error: %s",
            run_id,
            location_label,
            exc,
        )
        if history_path.exists():
            source = "cache"
            frame = pd.read_csv(history_path, parse_dates=["time"])
            logger.info(
                "Using cached weather data (run_id=%s, location=%s)",
                run_id,
                location_label,
            )
        else:
            allow_synthetic = os.getenv("ALLOW_SYNTHETIC_FALLBACK", "true").lower() in {
                "1",
                "true",
                "yes",
            }
            if not allow_synthetic:
                raise
            logger.warning(
                "Using synthetic weather fallback data (run_id=%s, location=%s)",
                run_id,
                location_label,
            )
            source = "synthetic"
            frame = build_synthetic_weather()

    # Keep a rolling window of recent observations for forecasting.
    rainfall_stats = _summarize_series(frame.get("rainfall", pd.Series(dtype=float)))
    if rainfall_stats["count"] and rainfall_stats["max"] == 0.0:
        logger.warning("Rainfall is all zero in history (run_id=%s, source=%s)", run_id, source)
    time_start = frame["time"].min() if "time" in frame else None
    time_end = frame["time"].max() if "time" in frame else None
    logger.info(
        "Weather summary (run_id=%s, source=%s, rows=%s, time_start=%s, time_end=%s, rainfall_mean=%.2f)",
        run_id,
        source,
        len(frame),
        time_start,
        time_end,
        rainfall_stats["mean"],
    )
    records: List[Dict[str, Any]] = frame.tail(72).to_dict(orient="records")
    if records:
        logger.info(
            "Weather state (run_id=%s, records=%s, last_time=%s)",
            run_id,
            len(records),
            records[-1].get("time"),
        )
    return {
        "location": location,
        "weather_data": records,
    }
