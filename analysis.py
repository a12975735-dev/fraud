import pandas as pd
import json
import urllib.request
from pathlib import Path

req_alerts = urllib.request.urlopen('http://localhost:5001/api/alerts')
alerts_data = json.loads(req_alerts.read().decode())['alerts']

top_5 = alerts_data[:5]
print('--- TOP 5 SHAP VALUES ---')
for alert in top_5:
    idx = alert['original_index']
    req_shap = urllib.request.urlopen(f'http://localhost:5001/api/alerts/{idx}/shap')
    shap_data = json.loads(req_shap.read().decode())['shap_features']
    print(f"Alert TXN-{idx} (Score: {alert['score']}):")
    for f in shap_data[:5]:
        print(f"  {f['label']}: {f['value']}")

BASE_DIR = Path('c:/fraud-detection-project')
TEST_PATH = BASE_DIR / 'data' / 'processed' / 'test.csv'
test_df = pd.read_csv(TEST_PATH)
if len(test_df) > 10000:
    test_df = test_df.sample(10000, random_state=42).copy()

flagged_indices = [a['original_index'] for a in alerts_data]
y_true = test_df['isFraud']
y_pred = [1 if idx in flagged_indices else 0 for idx in test_df.index]

tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0

print('\n--- PRECISION / RECALL ---')
print(f'Total rows in sample: {len(test_df)}')
print(f'Actual Frauds (isFraud=1): {sum(y_true)}')
print(f'Flagged by model (TP + FP): {len(flagged_indices)}')
print(f'True Positives: {tp}')
print(f'False Positives: {fp}')
print(f'False Negatives: {fn}')
print(f'Precision: {precision:.4f}')
print(f'Recall: {recall:.4f}')
