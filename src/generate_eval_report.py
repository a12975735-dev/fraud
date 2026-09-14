"""Write the model-performance evaluation report required by proposal §7.2."""

from pathlib import Path

from src.train_models import evaluate_model, load_data, prepare_features, rule_based_detector

BASE = Path(__file__).resolve().parents[1]
REPORT_PATH = BASE / "docs" / "MODEL_EVALUATION.md"
OUTPUTS_PATH = BASE / "outputs" / "model_performance_report.md"


def main() -> None:
    lines = [
        "# Model Performance Evaluation Report",
        "",
        "Compares the ensemble fraud model against the traditional rule-based detector",
        "using accuracy, precision, recall, F1, and ROC-AUC (proposal §2.1 / §7.2).",
        "",
    ]
    try:
        train, test = load_data(str(BASE))
        X_test, y_test = prepare_features(test)
        rule_preds = rule_based_detector(X_test)
        rule_metrics = evaluate_model("RuleBased", y_test, rule_preds)
        lines += [
            "## Rule-based baseline",
            "",
            str(rule_metrics),
            "",
        ]
        import joblib
        import os
        model_path = os.path.join(BASE, "models", "ensemble_no_oldbalances.pkl")
        if os.path.exists(model_path):
            model = joblib.load(model_path)
            cols = list(getattr(model, "feature_names_in_", X_test.columns))
            X_eval = X_test.reindex(columns=cols, fill_value=0)
            probs = model.predict_proba(X_eval)[:, 1]
            preds = (probs > 0.5).astype(int)
            ml_metrics = evaluate_model("Ensemble_reduced", y_test, preds, probs)
            lines += [
                "## Ensemble model",
                "",
                str(ml_metrics),
                "",
                "Target KPI from the proposal: fraud accuracy 90–98%, false-positive rate <10%.",
                "These figures are computed on the project's held-out PaySim test split.",
            ]
        else:
            lines.append("Ensemble pickle not found; train models with `python src/train_models.py`.")
    except Exception as error:
        lines += [
            "Processed train/test data were not available in this environment.",
            f"Generator error: `{error}`",
            "",
            "Run `python src/data_prep.py` then `python src/train_models.py` then re-run this report.",
        ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines) + "\n"
    REPORT_PATH.write_text(text, encoding="utf-8")
    OUTPUTS_PATH.write_text(text, encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
