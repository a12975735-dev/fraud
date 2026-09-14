"""Interactive Streamlit dashboard for the clean fraud-detection ensemble."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import streamlit as st

from dashboard_core import (
    load_scored_transactions,
    fpr_from_precision_recall,
    get_shap_explainer,
    OUTPUT_DIR
)

st.set_page_config(page_title="Fraud Detection Dashboard", layout="wide")

@st.cache_data
def get_cached_scored_transactions(limit):
    return load_scored_transactions(limit)

def colour_risk(value):
    colours = {"Low": "#d9ead3", "Medium": "#fff2cc", "High": "#f4cccc"}
    return f"background-color: {colours.get(value, 'white')}"

def selected_shap_image(row, feature_row):
    """Create a waterfall plot for the transaction selected in the table."""
    explainer = get_shap_explainer()
    values = explainer.shap_values(feature_row)
    if isinstance(values, list):
        values = values[1]
    elif getattr(values, "ndim", 0) == 3:
        values = values[:, :, 1]

    expected = explainer.expected_value
    if isinstance(expected, (list, np.ndarray)):
        expected = expected[1]

    output_path = OUTPUT_DIR / "shap_selected_transaction.png"
    plt.figure()
    shap.plots._waterfall.waterfall_legacy(
        expected, values[0], feature_names=list(feature_row.columns), show=False
    )
    plt.title(f"SHAP explanation: transaction {row.name}")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    return output_path



st.title("Fraud Detection Dashboard")
st.caption("Scores use the leakage-cleaned ensemble: no old origin balances or isFlaggedFraud.")

sample_size = st.sidebar.slider("Transactions to score and display", 100, 10_000, 1_000, step=100)
with st.spinner("Loading transactions and computing risk scores..."):
    transactions, X = get_cached_scored_transactions(sample_size)

st.subheader("Scored transactions")
display_columns = [c for c in ["step", "type", "amount", "oldbalanceDest", "newbalanceDest", "risk_score", "risk_level"] if c in transactions]
display = transactions[display_columns]
selection = st.dataframe(
    display.style.map(colour_risk, subset=["risk_level"]),
    on_select="rerun",
    selection_mode="single-row",
    width="stretch",
    height=430,
)

st.subheader("Estimated false-positive rate comparison")
positives = int((transactions["isFraud"] == 1).sum())
negatives = int((transactions["isFraud"] == 0).sum())
rates = pd.DataFrame({
    "Model": ["Rule-based", "Ensemble"],
    "False positive rate": [
        fpr_from_precision_recall(0.0016, 0.9684, positives, negatives),
        fpr_from_precision_recall(0.6979, 0.6579, positives, negatives),
    ],
}).set_index("Model")
st.bar_chart(rates)
st.caption("Rates are estimated from the provided precision/recall values and the displayed sample's class counts.")

if selection.selection.rows:
    position = selection.selection.rows[0]
    selected = transactions.iloc[position]
    image_path = selected_shap_image(selected, X.iloc[[position]])
    st.subheader(f"SHAP explanation for selected transaction {selected.name}")
    st.image(str(image_path), width="stretch")
else:
    st.info("Click a transaction row to generate and view its SHAP explanation.")
