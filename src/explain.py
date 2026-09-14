"""
Day 3 - SHAP Explainability
Loads the reduced-feature ensemble (ensemble_no_oldbalances.pkl) and
generates global + local SHAP explanations.
"""

import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shap

MODEL_PATH = "models/ensemble_no_oldbalances.pkl"
TEST_PATH = "data/processed/test.csv"
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_model_and_data():
    print(f"Loading model from {MODEL_PATH} ...")
    model = joblib.load(MODEL_PATH)

    print(f"Loading test data from {TEST_PATH} ...")
    test_df = pd.read_csv(TEST_PATH)

    if hasattr(model, "feature_names_in_"):
        feature_cols = list(model.feature_names_in_)
    else:
        drop_cols = ["isFraud", "isFlaggedFraud", "nameOrig", "nameDest",
                     "oldbalanceOrg", "newbalanceOrig"]
        feature_cols = [c for c in test_df.columns if c not in drop_cols]

    label_col = "isFraud" if "isFraud" in test_df.columns else None

    X_test = test_df[feature_cols].copy()
    y_test = test_df[label_col].copy() if label_col else None

    print(f"Using {len(feature_cols)} features: {feature_cols}")
    return model, X_test, y_test, feature_cols


def get_tree_model_for_shap(model):
    if hasattr(model, "estimators_"):
        print("Ensemble wrapper detected — using first underlying tree model for SHAP.")
        return model.estimators_[0]
    if hasattr(model, "named_estimators_"):
        first_key = list(model.named_estimators_.keys())[0]
        print(f"Using '{first_key}' sub-model for SHAP explanations.")
        return model.named_estimators_[first_key]
    return model


def main():
    model, X_test, y_test, feature_cols = load_model_and_data()
    shap_model = get_tree_model_for_shap(model)

    sample_size = min(2000, len(X_test))
    X_sample = X_test.sample(sample_size, random_state=42)

    print("Building SHAP TreeExplainer ...")
    explainer = shap.TreeExplainer(shap_model)
    shap_values = explainer.shap_values(X_sample)

    if isinstance(shap_values, list):
        shap_values_to_plot = shap_values[1]
    else:
        shap_values_to_plot = shap_values

    print("Saving SHAP summary plot ...")
    plt.figure()
    shap.summary_plot(shap_values_to_plot, X_sample, show=False)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "shap_summary.png"), dpi=150, bbox_inches="tight")
    plt.close()

    if y_test is not None:
        fraud_idx_in_test = y_test[y_test == 1].index
        matching = [i for i in X_sample.index if i in fraud_idx_in_test]
        example_idx = matching[0] if matching else X_sample.index[0]
    else:
        example_idx = X_sample.index[0]

    example_row = X_test.loc[[example_idx]]
    example_shap = explainer.shap_values(example_row)
    if isinstance(example_shap, list):
        example_shap = example_shap[1]

    print(f"Saving SHAP waterfall plot for transaction index {example_idx} ...")
    expected_value = explainer.expected_value
    if isinstance(expected_value, (list, np.ndarray)):
        expected_value = expected_value[1] if len(np.shape(expected_value)) else expected_value

    plt.figure()
    shap.plots._waterfall.waterfall_legacy(
        expected_value,
        example_shap[0],
        feature_names=feature_cols,
        show=False,
    )
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "shap_example.png"), dpi=150, bbox_inches="tight")
    plt.close()

    print("\nDone.")
    print(f"Saved: {OUTPUT_DIR}/shap_summary.png")
    print(f"Saved: {OUTPUT_DIR}/shap_example.png")
    print(f"Example explained transaction index: {example_idx}")


if __name__ == "__main__":
    main()
