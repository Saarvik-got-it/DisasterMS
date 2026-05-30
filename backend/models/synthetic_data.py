from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from backend.models.feature_spec import FEATURE_COLUMNS


def generate_synthetic_dataset(
    output_path: Path,
    sample_size: int = 2000,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    rainfall = rng.gamma(shape=2.0, scale=4.0, size=sample_size)
    humidity = rng.uniform(25, 100, size=sample_size)
    wind_speed = rng.uniform(0, 30, size=sample_size)
    temperature_trend = rng.normal(loc=0.0, scale=3.0, size=sample_size)
    pressure = rng.normal(loc=1010, scale=8.0, size=sample_size)

    labels = []
    for idx in range(sample_size):
        if rainfall[idx] > 18 and humidity[idx] > 75:
            label = "Flood"
        elif temperature_trend[idx] > 4 and humidity[idx] < 45 and rainfall[idx] < 3:
            label = "Heatwave"
        elif wind_speed[idx] > 18 and pressure[idx] < 995:
            label = "Storm"
        else:
            label = "Normal"
        labels.append(label)

    data = pd.DataFrame(
        {
            "rainfall": rainfall,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "temperature_trend": temperature_trend,
            "pressure": pressure,
            "label": labels,
        }
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output_path, index=False)
    return data[FEATURE_COLUMNS + ["label"]]
