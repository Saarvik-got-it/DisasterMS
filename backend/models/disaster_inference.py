from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Mapping
import logging
import os
import threading

import joblib
import pandas as pd

from backend.models.feature_spec import FEATURE_COLUMNS
from backend.models.train_classifier import train_classifier

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "disaster_classifier.pkl"
_train_lock = threading.Lock()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_disaster_model(model_path: Path = DEFAULT_MODEL_PATH):
    if not model_path.exists():
        auto_train = os.getenv("AUTO_TRAIN_MODEL", "true").lower() in {"1", "true", "yes"}
        if not auto_train:
            raise FileNotFoundError(f"Model not found at {model_path}")

        with _train_lock:
            if not model_path.exists():
                logger.warning("Model missing at %s. Training a new classifier.", model_path)
                backend_root = Path(__file__).resolve().parents[1]
                dataset_path = backend_root / "storage" / "data" / "disaster_training.csv"
                plots_dir = backend_root / "storage" / "plots"
                train_classifier(dataset_path, model_path, plots_dir)
    model = joblib.load(model_path)
    try:
        classes = list(model.classes_)
    except AttributeError:
        classes = []
    logger.info("Classifier model loaded (path=%s, classes=%s)", model_path, classes)
    return model


def predict_disaster(
    features: Mapping[str, float],
    model_path: Path = DEFAULT_MODEL_PATH,
) -> Dict[str, float]:
    payload = {
        "rainfall": features.get("predicted_rainfall", features.get("rainfall")),
        "humidity": features.get("humidity"),
        "wind_speed": features.get("wind_speed"),
        "temperature_trend": features.get("temperature_trend"),
        "pressure": features.get("pressure"),
    }

    missing = [key for key, value in payload.items() if value is None]
    if missing:
        raise ValueError(f"Missing feature values: {', '.join(missing)}")

    logger.info("Classifier features: %s", payload)
    frame = pd.DataFrame([payload], columns=FEATURE_COLUMNS)
    model = load_disaster_model(model_path)
    probabilities = model.predict_proba(frame)[0]

    result = {label: float(prob) for label, prob in zip(model.classes_, probabilities)}
    result["most_likely"] = max(result, key=result.get)
    logger.info("Classifier probabilities: %s", result)
    return result
