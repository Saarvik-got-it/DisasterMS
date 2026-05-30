from __future__ import annotations

import logging
from typing import Any, Dict

from backend.graphs.state import DisasterState
from backend.models.disaster_inference import predict_disaster

logger = logging.getLogger(__name__)


def disaster_prediction_node(state: DisasterState) -> DisasterState:
    forecast = state.get("forecast") or {}
    features = forecast.get("features") or {}
    run_id = state.get("run_id")
    if not features:
        raise ValueError("Forecast features missing for disaster prediction")

    prediction = predict_disaster(features)
    predicted_rainfall = float(features.get("predicted_rainfall", 0.0))
    flood_probability = float(prediction.get("Flood", 0.0))

    logger.info("Forecast: Predicted rainfall: %.2f", predicted_rainfall)
    logger.info("Disaster prediction: Flood probability: %.2f", flood_probability)
    logger.info(
        "Classifier state (run_id=%s, most_likely=%s)",
        run_id,
        prediction.get("most_likely"),
    )

    return {"disaster_prediction": prediction}
