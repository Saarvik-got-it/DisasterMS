from __future__ import annotations

import logging
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from backend.models.feature_spec import FEATURE_COLUMNS, LABELS
from backend.models.synthetic_data import generate_synthetic_dataset

logger = logging.getLogger(__name__)


def train_classifier(
    dataset_path: Path,
    model_path: Path,
    plots_dir: Path,
) -> None:
    data = generate_synthetic_dataset(dataset_path)
    features = data[FEATURE_COLUMNS]
    labels = data["label"]

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    accuracy = accuracy_score(y_test, predictions)
    report = classification_report(y_test, predictions, labels=LABELS, zero_division=0)
    matrix = confusion_matrix(y_test, predictions, labels=LABELS)

    plots_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 5))
    ConfusionMatrixDisplay(confusion_matrix=matrix, display_labels=LABELS).plot(
        ax=ax,
        cmap="Blues",
        colorbar=False,
    )
    fig.tight_layout()
    fig.savefig(plots_dir / "disaster_confusion_matrix.png", bbox_inches="tight")
    plt.close(fig)

    (plots_dir / "disaster_classification_report.txt").write_text(
        f"Accuracy: {accuracy:.4f}\n\n{report}\n",
        encoding="utf-8",
    )

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    logger.info("Saved model to %s", model_path)


def main() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    dataset_path = backend_root / "storage" / "data" / "disaster_training.csv"
    model_path = Path(__file__).resolve().parent / "disaster_classifier.pkl"
    plots_dir = backend_root / "storage" / "plots"

    train_classifier(dataset_path, model_path, plots_dir)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
