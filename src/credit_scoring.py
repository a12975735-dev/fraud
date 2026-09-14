"""
Production-ready Credit Scoring Script
---------------------------------------
Predictive credit scoring using alternative credit features, XGBoost Classifier,
hyperparameter tuning with RandomizedSearchCV, and SHAP explainability.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score
from xgboost import XGBClassifier
import shap


def generate_synthetic_data(n_samples: int = 3000, random_state: int = 42) -> pd.DataFrame:
    """
    Generate synthetic data containing alternative credit features and binary default risk label.

    Features:
    - utility_payment_ratio: float in [0.0, 1.0]
    - avg_monthly_cashflow: float in [500.0, 20000.0]
    - cashflow_volatility: float in [0.0, 1.0]
    - social_engagement_score: float in [0.0, 100.0]
    - credit_inquiries_3m: int in [0, 10]
    - default_risk: binary target label (0 or 1)
    """
    np.random.seed(random_state)

    utility_payment_ratio = np.random.uniform(0.0, 1.0, size=n_samples)
    avg_monthly_cashflow = np.random.uniform(500.0, 20000.0, size=n_samples)
    cashflow_volatility = np.random.uniform(0.0, 1.0, size=n_samples)
    social_engagement_score = np.random.uniform(0.0, 100.0, size=n_samples)
    credit_inquiries_3m = np.random.randint(0, 11, size=n_samples)

    # Non-linear log-odds formula with synthetic noise
    log_odds = (
        -3.5 * utility_payment_ratio
        - 0.00025 * (avg_monthly_cashflow - 5000.0)
        + 3.0 * (cashflow_volatility ** 1.3)
        - 0.025 * (social_engagement_score - 50.0)
        + 0.45 * credit_inquiries_3m
        + np.random.normal(0, 0.5, size=n_samples)
    )

    probability = 1.0 / (1.0 + np.exp(-log_odds))
    default_risk = (probability > 0.5).astype(int)

    df = pd.DataFrame({
        'utility_payment_ratio': utility_payment_ratio,
        'avg_monthly_cashflow': avg_monthly_cashflow,
        'cashflow_volatility': cashflow_volatility,
        'social_engagement_score': social_engagement_score,
        'credit_inquiries_3m': credit_inquiries_3m,
        'default_risk': default_risk
    })

    return df


class CreditRiskModel:
    """
    Predictive Credit Risk Model encapsulating training, evaluation, risk prediction,
    and SHAP explainability.
    """

    FEATURE_COLUMNS = [
        'utility_payment_ratio',
        'avg_monthly_cashflow',
        'cashflow_volatility',
        'social_engagement_score',
        'credit_inquiries_3m'
    ]

    def __init__(self, model_path: Optional[str] = None):
        self.model: Optional[XGBClassifier] = None
        self.feature_columns: List[str] = list(self.FEATURE_COLUMNS)
        self.explainer: Optional[shap.TreeExplainer] = None

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def load_model(self, model_path: str) -> None:
        """Load a saved model dictionary or model instance from file."""
        saved_obj = joblib.load(model_path)
        if isinstance(saved_obj, dict) and 'model' in saved_obj:
            self.model = saved_obj['model']
            self.feature_columns = saved_obj.get('features', list(self.FEATURE_COLUMNS))
        else:
            self.model = saved_obj
            self.feature_columns = list(self.FEATURE_COLUMNS)

        if self.model is not None:
            self.explainer = shap.TreeExplainer(self.model)

    def train_and_save(
        self,
        df: Optional[pd.DataFrame] = None,
        model_path: str = 'models/credit_scoring.pkl',
        n_samples: int = 3000,
        random_state: int = 42
    ) -> Dict[str, float]:
        """
        Train XGBClassifier with hyperparameter tuning, compute metrics, initialize SHAP explainer,
        and save the model artifact.
        """
        if df is None:
            df = generate_synthetic_data(n_samples=n_samples, random_state=random_state)

        X = df[self.feature_columns]
        y = df['default_risk']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=random_state, stratify=y
        )

        base_xgb = XGBClassifier(
            eval_metric='logloss',
            random_state=random_state
        )

        param_distributions = {
            'n_estimators': [50, 100, 150, 200],
            'max_depth': [3, 4, 5, 6],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'subsample': [0.6, 0.8, 1.0],
            'colsample_bytree': [0.6, 0.8, 1.0],
            'scale_pos_weight': [1.0, 1.5, 2.0]
        }

        search = RandomizedSearchCV(
            estimator=base_xgb,
            param_distributions=param_distributions,
            n_iter=10,
            scoring='roc_auc',
            cv=3,
            random_state=random_state,
            n_jobs=-1
        )

        print("Tuning XGBoost hyperparameters with RandomizedSearchCV...")
        search.fit(X_train, y_train)

        self.model = search.best_estimator_

        # Evaluate performance on test set
        y_pred = self.model.predict(X_test)
        y_prob = self.model.predict_proba(X_test)[:, 1]

        metrics = {
            'Accuracy': float(accuracy_score(y_test, y_pred)),
            'ROC-AUC': float(roc_auc_score(y_test, y_prob)),
            'Precision': float(precision_score(y_test, y_pred, zero_division=0)),
            'Recall': float(recall_score(y_test, y_pred, zero_division=0))
        }

        print("\n=== Model Performance Metrics ===")
        for metric_name, value in metrics.items():
            print(f"{metric_name:10s}: {value:.4f}")

        # Initialize SHAP TreeExplainer
        self.explainer = shap.TreeExplainer(self.model)

        # Ensure directory exists and save artifact
        os.makedirs(os.path.dirname(model_path) or '.', exist_ok=True)
        artifact = {
            'model': self.model,
            'features': self.feature_columns
        }
        joblib.dump(artifact, model_path)
        print(f"\nTrained model successfully saved to '{model_path}'")

        return metrics

    def predict_risk(self, feature_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict credit risk for a single input record.

        Returns:
        - risk_score: 0 to 100 scale (higher means higher default risk)
        - decision: 'APPROVED' if probability <= 0.35 else 'REVIEW'
        - probability: Default probability (0 to 1)
        """
        if self.model is None:
            raise ValueError("Model has not been trained or loaded yet.")

        df_input = pd.DataFrame([feature_dict])[self.feature_columns]
        prob = float(self.model.predict_proba(df_input)[0, 1])

        risk_score = round(prob * 100.0, 2)
        decision = 'APPROVED' if prob <= 0.35 else 'REVIEW'

        return {
            'risk_score': risk_score,
            'decision': decision,
            'probability': round(prob, 4)
        }

    def explain_prediction(self, feature_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Compute SHAP values for the prediction and return feature contributions sorted by magnitude.
        """
        if self.model is None:
            raise ValueError("Model has not been trained or loaded yet.")

        if self.explainer is None:
            self.explainer = shap.TreeExplainer(self.model)

        df_input = pd.DataFrame([feature_dict])[self.feature_columns]
        shap_values = self.explainer.shap_values(df_input)

        # Extract 1D array of SHAP values for single sample
        if isinstance(shap_values, list):
            # Binary classification list format [class_0, class_1]
            raw_contributions = shap_values[1][0]
        elif len(np.shape(shap_values)) == 2:
            raw_contributions = shap_values[0]
        else:
            raw_contributions = np.squeeze(shap_values)

        explanations = []
        for feat, val in zip(self.feature_columns, raw_contributions):
            contrib = float(val)
            explanations.append({
                'feature': feat,
                'contribution': round(contrib, 4),
                'direction': 'Increases Risk' if contrib > 0 else 'Decreases Risk',
                'abs_impact': abs(contrib)
            })

        # Sort by impact magnitude descending
        explanations.sort(key=lambda x: x['abs_impact'], reverse=True)
        for item in explanations:
            del item['abs_impact']

        return explanations


if __name__ == '__main__':
    print("Initializing CreditRiskModel pipeline...\n")
    model = CreditRiskModel()

    # Train model and save artifact
    metrics = model.train_and_save(model_path='models/credit_scoring.pkl', n_samples=3000, random_state=42)

    print("\n" + "=" * 50)
    print("TESTING PREDICTIONS & EXPLANATIONS")
    print("=" * 50)

    # Low-risk sample user
    low_risk_user = {
        'utility_payment_ratio': 0.95,
        'avg_monthly_cashflow': 15000.0,
        'cashflow_volatility': 0.10,
        'social_engagement_score': 85.0,
        'credit_inquiries_3m': 0
    }

    # High-risk sample user
    high_risk_user = {
        'utility_payment_ratio': 0.20,
        'avg_monthly_cashflow': 1200.0,
        'cashflow_volatility': 0.85,
        'social_engagement_score': 20.0,
        'credit_inquiries_3m': 7
    }

    print("\n--- Low Risk Applicant ---")
    low_risk_pred = model.predict_risk(low_risk_user)
    print("Prediction Result:", low_risk_pred)
    print("Top Feature Contributions:")
    for item in model.explain_prediction(low_risk_user):
        print(f"  - {item['feature']:25s}: {item['contribution']:+.4f} ({item['direction']})")

    print("\n--- High Risk Applicant ---")
    high_risk_pred = model.predict_risk(high_risk_user)
    print("Prediction Result:", high_risk_pred)
    print("Top Feature Contributions:")
    for item in model.explain_prediction(high_risk_user):
        print(f"  - {item['feature']:25s}: {item['contribution']:+.4f} ({item['direction']})")
