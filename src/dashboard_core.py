import joblib
import numpy as np
import pandas as pd
import shap
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "models" / "ensemble_no_oldbalances.pkl"
TEST_PATH = BASE_DIR / "data" / "processed" / "test.csv"
OUTPUT_DIR = BASE_DIR / "outputs"

def load_model():
    return joblib.load(MODEL_PATH)

def load_scored_transactions(limit=1000):
    model = load_model()
    test_df = pd.read_csv(TEST_PATH)
    if len(test_df) > limit:
        test_df = test_df.sample(limit, random_state=42).copy()

    features = list(model.feature_names_in_)
    X = test_df.reindex(columns=features, fill_value=0).fillna(0)
    scores = model.predict_proba(X)[:, 1]
    result = test_df.copy()
    result["risk_score"] = np.round(scores * 100, 2)
    result["risk_level"] = pd.cut(
        scores, bins=[-0.01, 0.30, 0.70, 1.0], labels=["Low", "Medium", "High"]
    ).astype(str)
    return result, X

def fpr_from_precision_recall(precision, recall, positives, negatives):
    true_positives = recall * positives
    false_positives = true_positives * (1 / precision - 1)
    return false_positives / negatives

def get_shap_explainer():
    model = load_model()
    if hasattr(model, "estimators_"):
        shap_model = model.estimators_[0]
    elif hasattr(model, "named_estimators_"):
        shap_model = next(iter(model.named_estimators_.values()))
    else:
        shap_model = model
    return shap.TreeExplainer(shap_model)

def get_shap_values_json(feature_row):
    explainer = get_shap_explainer()
    values = explainer.shap_values(feature_row)
    if isinstance(values, list):
        values = values[1]
    elif getattr(values, "ndim", 0) == 3:
        values = values[:, :, 1]

    feature_names = list(feature_row.columns)
    shap_vals = values[0]
    
    results = [{"label": str(name), "value": float(val)} for name, val in zip(feature_names, shap_vals)]
    results.sort(key=lambda x: abs(x["value"]), reverse=True)
    return results
