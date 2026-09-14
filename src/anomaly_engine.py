"""Level-3 unsupervised anomaly detection against a population baseline."""

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "isolation_forest.pkl"
FEATURE_ORDER = [
    "amount",
    "oldbalanceDest",
    "newbalanceDest",
    "step",
    "transaction_velocity",
    "amount_deviation",
    "balance_discrepancy",
]


def _synthetic_normal(n: int = 4000) -> np.ndarray:
    rng = np.random.default_rng(42)
    amount = rng.lognormal(mean=4.2, sigma=0.8, size=n)
    dest_old = rng.lognormal(mean=7.5, sigma=1.1, size=n)
    dest_new = dest_old + amount * rng.uniform(0.2, 1.0, size=n)
    step = rng.integers(1, 400, size=n).astype(float)
    velocity = rng.poisson(lam=2.0, size=n).astype(float) + 1.0
    deviation = np.abs(amount - np.median(amount))
    discrepancy = rng.normal(loc=0.0, scale=15.0, size=n)
    return np.column_stack([amount, dest_old, dest_new, step, velocity, deviation, discrepancy])


def fit_and_save(X: np.ndarray | None = None) -> IsolationForest:
    matrix = X if X is not None else _synthetic_normal()
    model = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
    model.fit(matrix)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURE_ORDER}, MODEL_PATH)
    return model


def _load() -> IsolationForest:
    if MODEL_PATH.exists():
        payload = joblib.load(MODEL_PATH)
        return payload["model"] if isinstance(payload, dict) else payload
    return fit_and_save()


_MODEL = _load()


def score_anomaly(tx: dict) -> dict:
    row = np.array([[float(tx.get(col) or 0.0) for col in FEATURE_ORDER]])
    prediction = int(_MODEL.predict(row)[0])  # -1 anomaly, 1 normal
    raw = float(_MODEL.decision_function(row)[0])
    # Map decision_function (higher = more normal) to a 0-99 anomaly score.
    anomaly_score = int(round(max(0.0, min(99.0, (0.15 - raw) * 250))))
    is_anomaly = prediction == -1 or anomaly_score >= 70
    return {
        "level": 3,
        "is_anomaly": bool(is_anomaly),
        "anomaly_score": anomaly_score,
        "decision_function": round(raw, 6),
        "label": "customer_profile_deviation" if is_anomaly else "within_profile",
    }
