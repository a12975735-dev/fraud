"""MLP behavioral-biometrics engine with EER reporting.

Uses CMU-style keystroke columns and ReMouse-style mouse columns when those
CSV files are present under data/. Otherwise trains on labelled synthetic
sessions that match the live capture schema (dwell, flight, MDA, MSD, distance, speed).
"""

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import roc_curve
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "models" / "biometrics_mlp.pkl"
METRICS_PATH = BASE_DIR / "models" / "biometrics_metrics.json"
CMU_PATH = BASE_DIR / "data" / "cmu_keystroke.csv"
REMOUSE_PATH = BASE_DIR / "data" / "remouse.csv"
FEATURE_NAMES = [
    "avg_dwell_time",
    "avg_flight_time",
    "mda",
    "msd",
    "total_distance",
    "avg_speed",
]


def equal_error_rate(y_true, scores) -> tuple[float, float]:
    fpr, tpr, thresholds = roc_curve(y_true, scores)
    fnr = 1 - tpr
    index = int(np.argmin(np.abs(fpr - fnr)))
    return float((fpr[index] + fnr[index]) / 2), float(thresholds[index])


def _synthetic_dataset(n_per_class: int = 1200):
    rng = np.random.default_rng(42)
    genuine = np.column_stack([
        rng.normal(92, 8, n_per_class),
        rng.normal(118, 12, n_per_class),
        rng.normal(40, 18, n_per_class),
        rng.normal(0.12, 0.04, n_per_class).clip(0, 1),
        rng.normal(1800, 400, n_per_class).clip(50),
        rng.normal(280, 60, n_per_class).clip(10),
    ])
    impostor = np.column_stack([
        rng.normal(105, 25, n_per_class),
        rng.normal(135, 30, n_per_class),
        rng.normal(55, 25, n_per_class),
        rng.normal(0.20, 0.08, n_per_class).clip(0, 1),
        rng.normal(2200, 600, n_per_class).clip(50),
        rng.normal(350, 100, n_per_class).clip(10),
    ])
    X = np.vstack([genuine, impostor])
    y = np.concatenate([np.ones(n_per_class, dtype=int), np.zeros(n_per_class, dtype=int)])
    return X, y, "synthetic_cmu_remouse_schema"


def load_training_matrix():
    if CMU_PATH.exists() and REMOUSE_PATH.exists():
        keystroke = np.genfromtxt(CMU_PATH, delimiter=",", skip_header=1)
        mouse = np.genfromtxt(REMOUSE_PATH, delimiter=",", skip_header=1)
        n = min(len(keystroke), len(mouse))
        X = np.column_stack([keystroke[:n, :2], mouse[:n, :4]])
        y = keystroke[:n, -1].astype(int)
        return X, y, "cmu_keystroke.csv+remouse.csv"
    return _synthetic_dataset()


def train_and_save() -> dict:
    X, y, source = load_training_matrix()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("mlp", MLPClassifier(
            hidden_layer_sizes=(32, 16),
            activation="relu",
            max_iter=400,
            random_state=42,
        )),
    ])
    pipeline.fit(X_train, y_train)
    proba = pipeline.predict_proba(X_test)[:, 1]
    eer, threshold = equal_error_rate(y_test, proba)
    accuracy = float((pipeline.predict(X_test) == y_test).mean())
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "features": FEATURE_NAMES, "threshold": threshold}, MODEL_PATH)
    metrics = {
        "source": source,
        "eer": round(eer, 4),
        "threshold": round(threshold, 4),
        "accuracy": round(accuracy, 4),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "classifier": "MLPClassifier(32,16)",
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def _load_bundle() -> dict:
    if not MODEL_PATH.exists():
        train_and_save()
    return joblib.load(MODEL_PATH)


_BUNDLE = _load_bundle()


def score_biometrics(payload: dict) -> dict:
    keystroke = payload.get("keystroke_features") or payload
    mouse = payload.get("mouse_features") or payload
    row = np.array([[
        float(keystroke.get("avg_dwell_time") or 0.0),
        float(keystroke.get("avg_flight_time") or 0.0),
        float(mouse.get("mda") or 0.0),
        float(mouse.get("msd") or 0.0),
        float(mouse.get("total_distance") or 0.0),
        float(mouse.get("avg_speed") or 0.0),
    ]])
    pipeline = _BUNDLE["pipeline"]
    genuine_proba = float(pipeline.predict_proba(row)[0][1])
    impostor_risk = int(round((1.0 - genuine_proba) * 99))
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8")) if METRICS_PATH.exists() else {}
    risk_level = "low" if impostor_risk < 30 else ("medium" if impostor_risk < 70 else "high")
    step_up = impostor_risk >= 70
    return {
        "status": "success",
        "biometric_score": impostor_risk,
        "genuine_probability": round(genuine_proba, 4),
        "risk_level": risk_level,
        "eer": metrics.get("eer"),
        "classifier": metrics.get("classifier", "MLPClassifier"),
        "source": metrics.get("source"),
        "step_up_required": step_up,
        "challenge_type": "knowledge_based" if step_up else None,
    }


if __name__ == "__main__":
    print(json.dumps(train_and_save(), indent=2))
