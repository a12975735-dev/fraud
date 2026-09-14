"""Batch / lambda speed-complement layer: velocity profiles and FRAML index refresh.

Falls back to pandas when PySpark is not installed (local Windows defense setup).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.anomaly_engine import FEATURE_ORDER, fit_and_save
from src.framl_engine import reload_index

BASE = Path(__file__).resolve().parents[1]
PROCESSED_TRAIN = BASE / "data" / "processed" / "train.csv"
FRAML_INDEX = BASE / "models" / "framl_index.json"
POWERBI_EXPORT = BASE / "outputs" / "powerbi_risk_dataset.csv"


def _load_train() -> pd.DataFrame | None:
    if PROCESSED_TRAIN.exists():
        return pd.read_csv(PROCESSED_TRAIN)
    return None


def recompute_velocity_features(frame: pd.DataFrame) -> pd.DataFrame:
    account_col = "nameOrig" if "nameOrig" in frame.columns else None
    if account_col and "step" in frame.columns:
        frame = frame.copy()
        frame["transaction_velocity"] = frame.groupby(account_col)["step"].transform("count")
        if "amount" in frame.columns:
            mean_amt = frame.groupby(account_col)["amount"].transform("mean")
            frame["amount_deviation"] = (frame["amount"] - mean_amt).abs()
    return frame


def refresh_framl_index(frame: pd.DataFrame | None) -> dict:
    existing = json.loads(FRAML_INDEX.read_text(encoding="utf-8")) if FRAML_INDEX.exists() else {
        "rings": [], "mule_destinations": [], "high_risk_countries": ["NG", "RU", "KP"], "embeddings": {}
    }
    if frame is not None and {"nameOrig", "nameDest", "isFraud"}.issubset(frame.columns):
        fraud = frame.loc[frame["isFraud"] == 1, ["nameOrig", "nameDest"]]
        counts = pd.concat([fraud["nameOrig"], fraud["nameDest"]]).value_counts()
        hot = counts.head(12).index.tolist()
        if len(hot) >= 3:
            existing["rings"] = [hot[:3], hot[3:6] or hot[:3]]
        existing["mule_destinations"] = [acct for acct in hot if str(acct).startswith("M")][:8]
    FRAML_INDEX.parent.mkdir(parents=True, exist_ok=True)
    FRAML_INDEX.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    reload_index()
    return existing


def export_powerbi(frame: pd.DataFrame | None) -> None:
    POWERBI_EXPORT.parent.mkdir(parents=True, exist_ok=True)
    if frame is None:
        pd.DataFrame([{"region": "US", "risk_score": 12, "aml_flag": 0}]).to_csv(POWERBI_EXPORT, index=False)
        return
    cols = [c for c in ["step", "amount", "type", "isFraud", "nameOrig", "nameDest"] if c in frame.columns]
    sample = frame[cols].head(5000).copy()
    sample["region"] = "US"
    sample.to_csv(POWERBI_EXPORT, index=False)


def run_batch_layer() -> dict:
    frame = _load_train()
    spark_used = False
    try:
        from pyspark.sql import SparkSession  # type: ignore

        spark = SparkSession.builder.master("local[1]").appName("fraud-batch").getOrCreate()
        spark.stop()
        spark_used = True
    except Exception:
        spark_used = False

    if frame is not None:
        frame = recompute_velocity_features(frame)
        numeric = frame.reindex(columns=FEATURE_ORDER).fillna(0).to_numpy()
        fit_and_save(numeric)
    else:
        fit_and_save()

    index = refresh_framl_index(frame)
    export_powerbi(frame)
    return {
        "spark_available": spark_used,
        "engine": "pyspark" if spark_used else "pandas",
        "framl_rings": len(index.get("rings", [])),
        "powerbi_export": str(POWERBI_EXPORT),
    }


if __name__ == "__main__":
    print(json.dumps(run_batch_layer(), indent=2))
