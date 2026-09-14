"""
Flask Production API for Credit Risk Scoring and Behavioral Biometrics
-----------------------------------------------------------------------
Exposes production REST endpoints for:
- POST /api/v1/credit-score
- POST /api/v1/biometrics/score
"""

import os
import sys
from typing import Dict, Any
from flask import Flask, request, jsonify

# Add project root directory to python path if needed
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.biometrics_engine import score_biometrics as mlp_score_biometrics
from src.credit_scoring import CreditRiskModel

# Initialize Flask app
app = Flask(__name__)

# Initialize CreditRiskModel globally so it stays in memory across requests
MODEL_PATH = os.path.join(PROJECT_ROOT, 'models', 'credit_scoring.pkl')
credit_model = CreditRiskModel(MODEL_PATH)

# If pre-trained model artifact was not loaded, train and initialize it
if credit_model.model is None:
    print(f"Pre-trained credit scoring model not found at {MODEL_PATH}. Training new model...")
    credit_model.train_and_save(model_path=MODEL_PATH)


@app.route('/health', methods=['GET'])
def health_check():
    """Service health check endpoint."""
    return jsonify({
        "status": "UP",
        "service": "Fraud Detection & Credit Risk Scoring API"
    }), 200


@app.route('/api/v1/credit-score', methods=['POST'])
def predict_credit_score():
    """
    Production endpoint for predicting credit risk and generating SHAP explanations.

    Expects JSON request body with:
    - utility_payment_ratio (float)
    - avg_monthly_cashflow (float)
    - cashflow_volatility (float)
    - social_engagement_score (float)
    - credit_inquiries_3m (int)
    """
    try:
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({
                "status": "ERROR",
                "error": "Invalid request payload. Must provide a valid JSON object."
            }), 400

        required_features = [
            'utility_payment_ratio',
            'avg_monthly_cashflow',
            'cashflow_volatility',
            'social_engagement_score',
            'credit_inquiries_3m'
        ]

        missing = [feat for feat in required_features if feat not in data]
        if missing:
            return jsonify({
                "status": "ERROR",
                "error": f"Missing required credit feature(s): {', '.join(missing)}"
            }), 400

        # Perform risk prediction
        prediction = credit_model.predict_risk(data)

        # Generate SHAP feature contributions
        shap_explanation = credit_model.explain_prediction(data)

        return jsonify({
            "status": "SUCCESS",
            "risk_score": prediction['risk_score'],
            "decision": prediction['decision'],
            "probability": prediction['probability'],
            "shap_explanation": shap_explanation
        }), 200

    except ValueError as val_err:
        return jsonify({
            "status": "ERROR",
            "error": str(val_err)
        }), 400
    except Exception as err:
        return jsonify({
            "status": "ERROR",
            "error": f"Failed to compute credit score: {str(err)}"
        }), 500


@app.route('/api/v1/biometrics/score', methods=['POST'])
def score_biometrics():
    """
    Production endpoint for scoring behavioral biometrics and calculating EER anomaly score.

    Expects JSON request body with:
    - keystroke_features: { avg_dwell_time: float, avg_flight_time: float }
    - mouse_features: { mda: float, msd: float, total_distance: float, avg_speed: float }
    """
    try:
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({
                "status": "ERROR",
                "error": "Invalid request payload. Must provide a valid JSON object."
            }), 400

        keystroke = data.get('keystroke_features', {})
        mouse = data.get('mouse_features', {})

        if not keystroke or not mouse:
            return jsonify({
                "status": "ERROR",
                "error": "Missing 'keystroke_features' or 'mouse_features' in request body."
            }), 400

        dwell = float(keystroke.get('avg_dwell_time', 0.0))
        flight = float(keystroke.get('avg_flight_time', 0.0))
        msd = float(mouse.get('msd', 0.0))
        total_dist = float(mouse.get('total_distance', 0.0))
        avg_speed = float(mouse.get('avg_speed', 0.0))

        # Trained on synthetically generated data — no real user
        # biometric sessions were available for training. See dissertation
        # Section 6 / 8.2 for details and future work.
        result = mlp_score_biometrics(data)
        
        eer_score = float(result.get('biometric_score', 0))
        # Keep original logic: <= 45.0 means authenticated
        is_authenticated = bool(eer_score <= 45.0)

        return jsonify({
            "status": "SUCCESS",
            "eer_score": eer_score,
            "is_authenticated": is_authenticated,
            "genuine_probability": result.get('genuine_probability')
        }), 200

    except (TypeError, ValueError) as type_err:
        return jsonify({
            "status": "ERROR",
            "error": f"Invalid feature data types: {str(type_err)}"
        }), 400
    except Exception as err:
        return jsonify({
            "status": "ERROR",
            "error": f"Failed to score biometrics: {str(err)}"
        }), 500


@app.errorhandler(400)
def bad_request_error(error):
    message = getattr(error, 'description', str(error))
    return jsonify({
        "status": "ERROR",
        "error": f"Bad Request: {message}"
    }), 400


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        "status": "ERROR",
        "error": "Endpoint not found."
    }), 404


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "status": "ERROR",
        "error": "Internal Server Error occurred."
    }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
