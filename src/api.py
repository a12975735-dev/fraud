"""
Day 3 - Real-time scoring API
Serves the reduced-feature ensemble model via FastAPI.
"""

import time
from functools import lru_cache
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from src.audit_logger import log_decision
from src.biometrics_engine import score_biometrics as mlp_score_biometrics
from src.step_up_auth import verify_challenge
from src.unified_scorer import build_unified_view

try:
    import shap
except ImportError:
    shap = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "ensemble_no_oldbalances.pkl"
BIOMETRICS_MODEL_PATH = PROJECT_ROOT / "models" / "biometrics_classifier.pkl"

app = FastAPI(title="Fraud Detection Scoring API")

# Allow the local-file keystroke demo to call this localhost API. The page
# submits aggregate timings only; it never sends the typed phrase itself.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

model = joblib.load(MODEL_PATH)

if hasattr(model, "feature_names_in_"):
    FEATURE_COLS = list(model.feature_names_in_)
else:
    FEATURE_COLS = ["amount", "oldbalanceDest", "newbalanceDest", "step",
                     "transaction_velocity", "amount_deviation", "balance_discrepancy"]

if hasattr(model, "estimators_"):
    shap_model = model.estimators_[0]
elif hasattr(model, "named_estimators_"):
    shap_model = list(model.named_estimators_.values())[0]
else:
    shap_model = model

explainer = shap.TreeExplainer(shap_model) if shap is not None else None


class Transaction(BaseModel):
    model_config = ConfigDict(extra="allow")
    amount: float
    oldbalanceDest: Optional[float] = 0.0
    newbalanceDest: Optional[float] = 0.0
    step: Optional[int] = 0
    transaction_velocity: Optional[float] = 0.0
    amount_deviation: Optional[float] = 0.0
    balance_discrepancy: Optional[float] = 0.0
    type: Optional[str] = "TRANSFER"
    biometricRiskScore: Optional[float] = Field(default=None, ge=0, le=100)
    nameOrig: Optional[str] = None
    nameDest: Optional[str] = None
    sourceIp: Optional[str] = None
    region: Optional[str] = None
    deviceId: Optional[str] = None
    biometricConsent: Optional[bool] = True


class KeystrokeSample(BaseModel):
    mean_dwell_time: float = Field(ge=0, description="Mean key hold duration in milliseconds.")
    mean_flight_time: float = Field(ge=0, description="Mean gap between keys in milliseconds.")


class KeystrokeFeatures(BaseModel):
    avg_dwell_time: float = Field(ge=0, description="Average key hold duration in milliseconds.")
    avg_flight_time: float = Field(ge=0, description="Average gap between key presses in milliseconds.")


class MouseFeatures(BaseModel):
    mda: float = Field(description="Movement Direction Average in degrees.")
    msd: float = Field(description="Movement Speed to Distance ratio.")
    total_distance: float = Field(ge=0, description="Total cursor distance traveled in pixels.")
    avg_speed: float = Field(ge=0, description="Average cursor speed in pixels/ms.")


class BiometricsPayload(BaseModel):
    keystroke_features: KeystrokeFeatures
    mouse_features: MouseFeatures
    consent: Optional[bool] = True


class StepUpRequest(BaseModel):
    nameDest: Optional[str] = "M0000"
    amount: float = 0
    answers: dict



@lru_cache
def load_biometrics_classifier():
    """Load the saved scaler-plus-classifier pipeline only once per API process."""
    if not BIOMETRICS_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Biometrics model not found at {BIOMETRICS_MODEL_PATH}. Run src/biometrics_demo.py first."
        )
    return joblib.load(BIOMETRICS_MODEL_PATH)


def build_feature_row(tx: Transaction) -> pd.DataFrame:
    data = tx.model_dump()
    row = {}
    for col in FEATURE_COLS:
        row[col] = data.get(col, 0)
    return pd.DataFrame([row])


@app.get("/")
def root():
    return {"status": "ok", "message": "Fraud Detection Scoring API is running."}


@app.post("/score_transaction")
def score_transaction(tx: Transaction):
    start = time.perf_counter()

    X = build_feature_row(tx)

    proba = model.predict_proba(X)[0][1]
    ml_risk_score = int(round(proba * 99))
    biometric_risk_score = tx.biometricRiskScore
    # A high behavioral anomaly is independently actionable, so never let it lower
    # the transaction model's score. Missing telemetry leaves ML scoring unchanged.
    if explainer is None:
        top_reasons = []
    else:
        shap_vals = explainer.shap_values(X)
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[1]
        contributions = list(zip(FEATURE_COLS, shap_vals[0]))
        contributions.sort(key=lambda x: abs(x[1]), reverse=True)
        top_reasons = [
            {"feature": feat, "impact": round(float(val), 4)}
            for feat, val in contributions[:3]
        ]

    unified = build_unified_view(tx.model_dump(), ml_risk_score, top_reasons, model, X, FEATURE_COLS)
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    unified["latency_ms"] = latency_ms
    unified["ml_risk_score"] = ml_risk_score
    unified["biometric_risk_score"] = biometric_risk_score

    log_decision(
        model_name="ensemble_no_oldbalances.pkl",
        input_features=tx.model_dump(),
        risk_score=unified["risk_score"],
        risk_level=unified["risk_level"],
        top_reason_codes=unified["top_reason_codes"],
    )
    return unified


@app.post("/score_keystrokes")
def score_keystrokes(sample: KeystrokeSample):
    """Classify aggregate live keystroke timings against the demo's synthetic baseline."""
    try:
        classifier = load_biometrics_classifier()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    features = np.array([[sample.mean_dwell_time, sample.mean_flight_time]])
    predicted_class = int(classifier.predict(features)[0])
    class_index = list(classifier.classes_).index(predicted_class)
    confidence = float(classifier.predict_proba(features)[0][class_index])
    pattern = "genuine" if predicted_class == 1 else "impostor"
    return {
        "pattern": pattern,
        "confidence": round(confidence, 4),
        "mean_dwell_time": sample.mean_dwell_time,
        "mean_flight_time": sample.mean_flight_time,
        "note": "Demo classification against a synthetic baseline; not an identity-verification decision.",
    }


@app.post("/api/v1/biometrics/score")
def score_biometrics(payload: BiometricsPayload):
    """Score continuous behavioral biometrics with the MLP engine."""
    if payload.consent is False:
        return {
            "status": "skipped",
            "biometric_score": None,
            "risk_level": None,
            "reason": "GDPR Article 9 consent was not granted; biometrics not processed.",
        }
    result = mlp_score_biometrics(payload.model_dump())
    result["payload"] = payload.model_dump()
    return result


@app.post("/api/v1/auth/step-up")
def step_up(request: StepUpRequest):
    return verify_challenge({"nameDest": request.nameDest, "amount": request.amount}, request.answers)


@app.get("/api/v1/federated/status")
def federated_status():
    """Describe the federated-averaging demonstration (no raw data leaves partitions)."""
    return {
        "status": "ok",
        "mode": "simulated_federated_averaging",
        "script": "src/federated_learning.py",
        "note": "Only model parameters are combined across in-memory partitions.",
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
