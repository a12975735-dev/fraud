"""LIME local explanations for the ensemble fraud model (proposal §5.1)."""

from __future__ import annotations

FEATURE_NAMES_FALLBACK = [
    "amount",
    "oldbalanceDest",
    "newbalanceDest",
    "step",
    "transaction_velocity",
    "amount_deviation",
    "balance_discrepancy",
]


def lime_reason_codes(model, X, feature_names: list[str] | None = None, num_samples: int = 80) -> list[dict]:
    """Return LIME feature weights, or an empty list if lime is unavailable/slow."""
    names = feature_names or FEATURE_NAMES_FALLBACK
    try:
        from lime.lime_tabular import LimeTabularExplainer
        import numpy as np

        background = np.repeat(X.to_numpy(), 12, axis=0)
        explainer = LimeTabularExplainer(
            background,
            feature_names=names,
            class_names=["legit", "fraud"],
            mode="classification",
            discretize_continuous=False,
        )
        explanation = explainer.explain_instance(
            X.to_numpy()[0],
            model.predict_proba,
            num_features=min(5, len(names)),
            num_samples=num_samples,
        )
        return [
            {"feature": str(name).split(" ")[0], "impact": round(float(weight), 4), "method": "LIME"}
            for name, weight in explanation.as_list(label=1)
        ]
    except Exception:
        return []
