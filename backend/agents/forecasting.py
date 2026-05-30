from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from prophet import Prophet

from backend.graphs.state import DisasterState

logger = logging.getLogger(__name__)


def _clamp_non_negative(value: float) -> float:
    return max(0.0, float(value))


def prepare_prophet_frame(records: List[Mapping[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    if frame.empty:
        raise ValueError("No weather data available for forecasting")

    frame["ds"] = pd.to_datetime(frame["time"], utc=True).dt.tz_convert(None)
    frame["y"] = pd.to_numeric(frame["rainfall"], errors="coerce")
    cleaned = frame[["ds", "y"]].dropna()
    negative_count = int((cleaned["y"] < 0).sum())
    if negative_count:
        logger.warning("Found %s negative rainfall inputs; clamping to 0", negative_count)
        cleaned.loc[:, "y"] = cleaned["y"].clip(lower=0)
    if cleaned.empty:
        raise ValueError("Rainfall series is empty after cleaning")
    return cleaned


def summarize_recent_conditions(records: List[Mapping[str, Any]]) -> Dict[str, float]:
    frame = pd.DataFrame(records)
    if frame.empty:
        raise ValueError("No weather data available for feature summary")

    recent = frame.tail(24)

    def mean_series(series: pd.Series, name: str) -> float:
        cleaned = pd.to_numeric(series, errors="coerce").dropna()
        if cleaned.empty:
            raise ValueError(f"{name} series is empty after cleaning")
        return float(cleaned.mean())

    temp_values = pd.to_numeric(recent["temperature"], errors="coerce").dropna()
    if temp_values.empty:
        raise ValueError("Temperature series is empty after cleaning")

    temperature_trend = (
        float(temp_values.iloc[-1] - temp_values.iloc[0]) if len(temp_values) > 1 else 0.0
    )

    return {
        "temperature_trend": temperature_trend,
        "humidity": mean_series(recent["humidity"], "Humidity"),
        "wind_speed": mean_series(recent["wind_speed"], "Wind speed"),
        "pressure": mean_series(recent["pressure"], "Pressure"),
    }


def run_rainfall_forecast(
    frame: pd.DataFrame,
    horizon_hours: int = 48,
) -> Tuple[pd.DataFrame, Prophet]:
    model = Prophet()
    model.fit(frame)
    future = model.make_future_dataframe(periods=horizon_hours, freq="h", include_history=False)
    forecast = model.predict(future)
    return forecast, model


def save_forecast_plot(model: Prophet, forecast: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig = model.plot(forecast)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def forecast_rainfall(state: DisasterState) -> DisasterState:
    records = state.get("weather_data") or []
    run_id = state.get("run_id")
    logger.info("Forecast input (run_id=%s, records=%s)", run_id, len(records))
    frame = prepare_prophet_frame(records)
    if len(frame) < 48:
        logger.warning("Forecast history is short (run_id=%s, points=%s)", run_id, len(frame))
    forecast, model = run_rainfall_forecast(frame)
    feature_snapshot = summarize_recent_conditions(records)

    plot_path = save_forecast_plot(
        model,
        forecast,
        Path("backend/storage/plots/rainfall_forecast.png"),
    )

    points: List[Dict[str, Any]] = []
    rainfall_values: List[float] = []
    negative_forecast = int((forecast["yhat"] < 0).sum())
    if negative_forecast:
        logger.warning("Forecast produced %s negative rainfall values; clamping", negative_forecast)
    for _, row in forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].iterrows():
        rainfall = _clamp_non_negative(row["yhat"])
        rainfall_lower = _clamp_non_negative(row["yhat_lower"])
        rainfall_upper = _clamp_non_negative(row["yhat_upper"])
        rainfall_values.append(rainfall)
        points.append(
            {
                "time": row["ds"].isoformat(),
                "rainfall": rainfall,
                "rainfall_lower": rainfall_lower,
                "rainfall_upper": rainfall_upper,
            }
        )

    predicted_rainfall = float(sum(rainfall_values) / len(rainfall_values)) if rainfall_values else 0.0
    predicted_rainfall = _clamp_non_negative(predicted_rainfall)
    feature_snapshot["predicted_rainfall"] = predicted_rainfall

    logger.info(
        "Forecast summary (run_id=%s, predicted_rainfall=%.2f, forecast_min=%.2f, forecast_max=%.2f)",
        run_id,
        predicted_rainfall,
        float(forecast["yhat"].min()),
        float(forecast["yhat"].max()),
    )
    logger.info(
        "Forecast state (run_id=%s, points=%s)",
        run_id,
        len(points),
    )

    return {
        "forecast": {
            "horizon_hours": 48,
            "points": points,
            "plot_path": str(plot_path),
            "features": feature_snapshot,
        }
    }
