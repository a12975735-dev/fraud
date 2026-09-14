import os
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

base = os.path.dirname(os.path.dirname(__file__))
test_path = os.path.join(base, 'data', 'processed', 'test.csv')
if not os.path.exists(test_path):
    raise FileNotFoundError('Processed test CSV not found: ' + test_path)

test = pd.read_csv(test_path)
# discover label column
label_col = None
for c in test.columns:
    n = ''.join(ch for ch in str(c).lower() if ch.isalnum())
    if n == 'isfraud' or n == 'fraud':
        label_col = c
        break
if label_col is None:
    raise KeyError('Label column not found in test CSV')

y_test = test[label_col]
X_test = test.drop(columns=[label_col])
if 'type' in X_test.columns:
    X_test = pd.get_dummies(X_test, columns=['type'], drop_first=True)
X_test = X_test.select_dtypes(include=['number']).fillna(0)

def eval_model(name, model, X, y):
    probs = model.predict_proba(X)[:, 1]
    preds = (probs > 0.5).astype(int)
    return {
        'model': name,
        'accuracy': accuracy_score(y, preds),
        'precision': precision_score(y, preds, zero_division=0),
        'recall': recall_score(y, preds, zero_division=0),
        'f1': f1_score(y, preds, zero_division=0),
        'auc': roc_auc_score(y, probs),
    }

results = []
for relpath, label in [('models/ensemble.pkl', 'Ensemble_full'), ('models/ensemble_no_oldbalances.pkl', 'Ensemble_reduced')]:
    p = os.path.join(base, relpath)
    if not os.path.exists(p):
        print('Model not found:', p)
        continue
    m = joblib.load(p)
    # attempt to align columns if model exposes `feature_names_in_`
    X_eval = X_test
    if hasattr(m, 'feature_names_in_'):
        cols = list(m.feature_names_in_)
        X_eval = X_test.reindex(columns=cols, fill_value=0)
    results.append(eval_model(label, m, X_eval, y_test))

if not results:
    print('No models evaluated.')
else:
    df = pd.DataFrame(results).set_index('model')
    print(df.round(4).to_string())
