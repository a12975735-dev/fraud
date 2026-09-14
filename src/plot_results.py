import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

base = os.path.dirname(os.path.dirname(__file__))
outputs_dir = os.path.join(base, 'outputs')
os.makedirs(outputs_dir, exist_ok=True)

# load test set
test_path = os.path.join(base, 'data', 'processed', 'test.csv')
if not os.path.exists(test_path):
    raise FileNotFoundError('Test CSV not found: ' + test_path)

df_test = pd.read_csv(test_path)
# find label
label_col = None
for c in df_test.columns:
    n = ''.join(ch for ch in str(c).lower() if ch.isalnum())
    if n == 'isfraud' or n == 'fraud':
        label_col = c
        break
if label_col is None:
    raise KeyError('Label column not found in test CSV')

y_test = df_test[label_col]
X_test = df_test.drop(columns=[label_col])
if 'type' in X_test.columns:
    X_test = pd.get_dummies(X_test, columns=['type'], drop_first=True)
X_test = X_test.select_dtypes(include=[np.number]).fillna(0)

# helper to align features
def align_X_for_model(model, X):
    # try model.feature_names_in_ then estimators_ members
    cols = None
    if hasattr(model, 'feature_names_in_'):
        cols = list(model.feature_names_in_)
    else:
        # try first estimator
        try:
            first = None
            if hasattr(model, 'named_estimators_'):
                first = list(model.named_estimators_.values())[0]
            elif hasattr(model, 'estimators_'):
                first = model.estimators_[0]
            if first is not None and hasattr(first, 'feature_names_in_'):
                cols = list(first.feature_names_in_)
        except Exception:
            cols = None
    if cols is not None:
        return X.reindex(columns=cols, fill_value=0)
    return X

# load models
models = []
for rel, label in [('models/ensemble.pkl', 'Ensemble_full'), ('models/ensemble_no_oldbalances.pkl', 'Ensemble_reduced')]:
    p = os.path.join(base, rel)
    if os.path.exists(p):
        m = joblib.load(p)
        models.append((label, m))
    else:
        print('Warning: model missing', p)

if not models:
    raise RuntimeError('No models found to evaluate')

# Plot ROC curves
plt.figure(figsize=(8, 6))
for label, m in models:
    X_eval = align_X_for_model(m, X_test)
    probs = m.predict_proba(X_eval)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, probs)
    roc_auc = auc(fpr, tpr)
    plt.plot(fpr, tpr, label=f"{label} (AUC={roc_auc:.4f})")

plt.plot([0, 1], [0, 1], 'k--', alpha=0.6)
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curves: Full vs Reduced Ensemble')
plt.legend(loc='lower right')
plt.grid(alpha=0.3)
roc_path = os.path.join(outputs_dir, 'roc_ensembles.png')
plt.tight_layout()
plt.savefig(roc_path, dpi=150)
plt.close()
print('Saved ROC plot to', roc_path)

# Feature importance for reduced ensemble
reduced = None
for label, m in models:
    if label == 'Ensemble_reduced':
        reduced = m
        break

if reduced is None:
    print('Reduced ensemble not found; skipping feature importance plot')
else:
    # determine feature names
    feat_names = None
    first_est = None
    if hasattr(reduced, 'named_estimators_') and len(reduced.named_estimators_)>0:
        first_est = list(reduced.named_estimators_.values())[0]
    elif hasattr(reduced, 'estimators_') and len(reduced.estimators_)>0:
        first_est = reduced.estimators_[0]

    if first_est is not None and hasattr(first_est, 'feature_names_in_'):
        feat_names = list(first_est.feature_names_in_)
    else:
        # fallback to columns from aligned X
        feat_names = list(align_X_for_model(reduced, X_test).columns)

    # aggregate importances from member estimators
    importances = np.zeros(len(feat_names))
    count = 0
    # use named_estimators_ mapping when available
    members = []
    if hasattr(reduced, 'named_estimators_'):
        members = list(reduced.named_estimators_.values())
    elif hasattr(reduced, 'estimators_'):
        members = reduced.estimators_

    for est in members:
        if hasattr(est, 'feature_importances_'):
            fi = np.array(est.feature_importances_)
            # if lengths differ, try to align by feature_names_in_
            if hasattr(est, 'feature_names_in_') and list(est.feature_names_in_) != feat_names:
                # align by name
                try:
                    est_names = list(est.feature_names_in_)
                    mapping = [est_names.index(n) if n in est_names else None for n in feat_names]
                    aligned = np.zeros(len(feat_names))
                    for i, idx in enumerate(mapping):
                        if idx is not None:
                            aligned[i] = fi[idx]
                    fi = aligned
                except Exception:
                    fi = np.zeros(len(feat_names))
            elif len(fi) != len(feat_names):
                fi = np.zeros(len(feat_names))
            importances += fi
            count += 1

    if count == 0:
        print('No feature_importances_ found on ensemble members; skipping plot')
    else:
        importances /= count
        # take top 20
        idx = np.argsort(importances)[::-1][:20]
        top_feats = [feat_names[i] for i in idx]
        top_vals = importances[idx]

        plt.figure(figsize=(10, 6))
        plt.barh(range(len(top_feats))[::-1], top_vals, color='C0')
        plt.yticks(range(len(top_feats))[::-1], top_feats)
        plt.xlabel('Average feature importance')
        plt.title('Top features (averaged) - Reduced Ensemble')
        plt.tight_layout()
        fi_path = os.path.join(outputs_dir, 'feature_importance_reduced.png')
        plt.savefig(fi_path, dpi=150)
        plt.close()
        print('Saved feature importance plot to', fi_path)
