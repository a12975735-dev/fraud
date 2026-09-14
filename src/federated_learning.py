"""Single-machine Federated Averaging demonstration for fraud detection."""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_curve, precision_recall_fscore_support, roc_auc_score


# Keep the same leakage-safe seven features used by the final ensemble model.
FEATURE_COLS = [
    "step",
    "amount",
    "oldbalanceDest",
    "newbalanceDest",
    "transaction_velocity",
    "amount_deviation",
    "balance_discrepancy",
]
LABEL_COL = "isFraud"


def transform_features(data: pd.DataFrame) -> np.ndarray:
    """Apply fixed, non-data-sharing feature scaling for stable local training."""
    features = data[FEATURE_COLS].astype(np.float64).copy()
    # Fixed transformations are shared code/configuration, not statistics from another bank.
    for column in ["amount", "oldbalanceDest", "newbalanceDest", "amount_deviation", "balance_discrepancy"]:
        features[column] = np.log1p(features[column].clip(lower=0))
    features["step"] /= 744.0  # PaySim contains 744 hourly simulation steps.
    features["transaction_velocity"] = np.log1p(features["transaction_velocity"].clip(lower=0))
    return features.to_numpy()


def find_best_threshold(coefficients: np.ndarray, intercept: np.ndarray, X: np.ndarray, y: np.ndarray,
                         min_recall: float = 0.6) -> float:
    """Pick the threshold with the best precision subject to a minimum recall floor.

    Fraud detection systems generally need a recall guarantee (catching most fraud)
    more than they need to maximize F1 in the abstract. This finds the highest
    precision achievable while still catching at least `min_recall` of fraud cases,
    using training data only (never the test set).
    """
    probabilities = expit(X @ coefficients.ravel() + intercept.ravel()[0])
    precisions, recalls, thresholds = precision_recall_curve(y, probabilities)

    precisions, recalls = precisions[:-1], recalls[:-1]

    valid = recalls >= min_recall
    if not np.any(valid):
        best_index = np.argmax(recalls)
    else:
        valid_indices = np.where(valid)[0]
        best_index = valid_indices[np.argmax(precisions[valid_indices])]

    return float(thresholds[best_index])



def evaluate(name: str, coefficients: np.ndarray, intercept: np.ndarray, X_test: np.ndarray,
             y_test: np.ndarray, threshold: float = 0.5) -> dict[str, float | str]:
    probabilities = expit(X_test @ coefficients.ravel() + intercept.ravel()[0])
    predictions = (probabilities >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, predictions, average="binary", zero_division=0
    )
    return {
        "Model": name,
        "Threshold": round(threshold, 4),
        "Accuracy": accuracy_score(y_test, predictions),
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "AUC-ROC": roc_auc_score(y_test, probabilities),
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    processed_dir = project_root / "data" / "processed"
    usecols = FEATURE_COLS + [LABEL_COL]

    train = pd.read_csv(processed_dir / "train.csv", usecols=usecols)
    test = pd.read_csv(processed_dir / "test.csv", usecols=usecols)
    print(f"Loaded training data: {train.shape}; held-out test data: {test.shape}")

    # Banks receive non-overlapping, chronological transaction chunks.
    ordered_train = train.sort_values("step", kind="stable").reset_index(drop=True)
    bank_indices = np.array_split(np.arange(len(ordered_train)), 3)
    banks = [ordered_train.iloc[indices] for indices in bank_indices]
    X_test = transform_features(test)
    y_test = test[LABEL_COL].to_numpy()

    local_models: list[LogisticRegression] = []
    results: list[dict[str, float | str]] = []
    for bank_number, bank_data in enumerate(banks, start=1):
        X_bank = transform_features(bank_data)
        y_bank = bank_data[LABEL_COL].to_numpy()
        model = LogisticRegression(
            solver="lbfgs", max_iter=250, class_weight="balanced", random_state=42
        )
        model.fit(X_bank, y_bank)
        local_models.append(model)
        threshold = find_best_threshold(model.coef_, model.intercept_, X_bank, y_bank, min_recall=0.6)
        results.append(evaluate(f"Local Bank {bank_number}", model.coef_, model.intercept_, X_test, y_test, threshold))
        print(f"Trained Local Bank {bank_number} on {len(bank_data):,} private transactions.")

    # This simulates Federated Averaging (McMahan et al., 2017) using in-memory data partitions rather than genuinely separate institutions/machines. No raw data crosses partition boundaries — only model parameters are combined, demonstrating the core federated learning principle within a single-machine simulation.
    global_coef = np.mean([model.coef_ for model in local_models], axis=0)
    global_intercept = np.mean([model.intercept_ for model in local_models], axis=0)
    global_threshold = float(np.mean([
        find_best_threshold(model.coef_, model.intercept_,
                             transform_features(bank_data), bank_data[LABEL_COL].to_numpy(), min_recall=0.6)
        for model, bank_data in zip(local_models, banks)
    ]))

    results.append(evaluate("Federated Global (Averaged Predictions)", global_coef, global_intercept, X_test, y_test, global_threshold))

    comparison = pd.DataFrame(results)
    metric_columns = ["Accuracy", "Precision", "Recall", "F1", "AUC-ROC"]
    comparison[metric_columns] = comparison[metric_columns].apply(lambda column: column.map(lambda value: f"{value:.4f}"))
    print("\nFederated learning comparison on the shared held-out test set:")
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()

