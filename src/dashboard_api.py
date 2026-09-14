import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.dashboard_core import load_scored_transactions, get_shap_values_json

app = Flask(__name__)
# Enable CORS for the React frontend
CORS(app)

# Load data into memory once
print("Loading test dataset and predicting scores...")
transactions_df, X_df = load_scored_transactions(limit=10000)

@app.route('/api/dashboard/stats', methods=['GET'])
def get_stats():
    total_tx = len(transactions_df)
    high_risk = len(transactions_df[transactions_df['risk_level'] == 'High'])
    medium_risk = len(transactions_df[transactions_df['risk_level'] == 'Medium'])
    low_risk = len(transactions_df[transactions_df['risk_level'] == 'Low'])
    flagged = high_risk + medium_risk
    
    return jsonify({
        "total_transactions": total_tx,
        "flagged_transactions": flagged,
        "high_risk": high_risk,
        "risk_distribution": {
            "Low": low_risk,
            "Medium": medium_risk,
            "High": high_risk
        }
    })

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    # Return transactions above Medium threshold, sorted by risk_score desc
    alerts_df = transactions_df[transactions_df['risk_level'].isin(['High', 'Medium'])].copy()
    alerts_df = alerts_df.sort_values(by='risk_score', ascending=False).head(50)
    
    # Map to the shape expected by the React frontend
    alerts = []
    for idx, row in alerts_df.iterrows():
        alerts.append({
            "id": f"TXN-{idx}",
            "original_index": int(idx),
            "time": "14:35:28",  # Mock time for UI
            "type": "Transaction",
            "score": float(row['risk_score']),
            "status": "New",
            "amount": float(row['amount']),
            "account": str(row.get('nameOrig', 'Unknown')),
            "merchant": str(row.get('nameDest', 'Unknown'))
        })
    return jsonify({"alerts": alerts})

@app.route('/api/alerts/<int:original_index>/shap', methods=['GET'])
def get_shap(original_index):
    if original_index not in X_df.index:
        return jsonify({"error": "Transaction index not found"}), 404
        
    feature_row = X_df.loc[[original_index]]
    shap_results = get_shap_values_json(feature_row)
    return jsonify({"shap_features": shap_results})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
