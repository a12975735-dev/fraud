import os
import joblib
import pandas as pd
import numpy as np
import shap
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.ensemble import VotingClassifier

base = 'c:/fraud-detection-project'
train_path = os.path.join(base, 'data', 'processed', 'train.csv')
test_path = os.path.join(base, 'data', 'processed', 'test.csv')

train = pd.read_csv(train_path)
test = pd.read_csv(test_path)

def prepare_features(df):
    df = df.copy()
    label_col = 'isFraud'
    y = df[label_col]
    leakage_cols = [c for c in ['isFlaggedFraud'] if c in df.columns]
    X = df.drop(columns=[label_col, *leakage_cols])
    if 'type' in X.columns:
        X = pd.get_dummies(X, columns=['type'], drop_first=True)
    X = X.select_dtypes(include=[np.number]).fillna(0)
    return X, y

X_train, y_train = prepare_features(train)
X_test, y_test = prepare_features(test)

# Drop post-transaction / destination balances
drop_cols = [c for c in X_train.columns if c in [
    'oldbalanceDest', 'newbalanceDest', 'newbalanceOrig', 
    'balance_discrepancy', 'errorBalanceDest', 'errorBalanceOrig'
]]
print("Dropping columns:", drop_cols)

X_train_red = X_train.drop(columns=drop_cols, errors='ignore')
X_test_red = X_test.drop(columns=drop_cols, errors='ignore')

neg = (y_train == 0).sum()
pos = (y_train == 1).sum()
scale_pos_weight = max(1, neg // max(1, pos))

xgb_r = XGBClassifier(n_estimators=200, eval_metric='logloss', scale_pos_weight=scale_pos_weight, n_jobs=8, random_state=42)
lgb_r = LGBMClassifier(n_estimators=200, class_weight='balanced', n_jobs=-1, random_state=42)

print("Training XGB...")
xgb_r.fit(X_train_red, y_train)
print("Training LGBM...")
lgb_r.fit(X_train_red, y_train)

ensemble_red = VotingClassifier(estimators=[('xgb', xgb_r), ('lgb', lgb_r)], voting='soft')
sample_n = min(10000, len(X_train_red))
sample_idx = X_train_red.sample(n=sample_n, random_state=42).index
ensemble_red.fit(X_train_red.loc[sample_idx], y_train.loc[sample_idx])

# Save the model
model_path = os.path.join(base, 'models', 'ensemble_no_oldbalances.pkl')
joblib.dump(ensemble_red, model_path)
print(f"Saved to {model_path}")

# Evaluate precision/recall on 10,000 sample using risk_score > 30 (Medium/High) logic
test_df_sample = test.sample(10000, random_state=42).copy()
X_test_sample = X_test_red.loc[test_df_sample.index]

scores = ensemble_red.predict_proba(X_test_sample)[:, 1]
risk_levels = pd.cut(scores, bins=[-0.01, 0.30, 0.70, 1.0], labels=["Low", "Medium", "High"]).astype(str)

test_df_sample['risk_score'] = scores
test_df_sample['risk_level'] = risk_levels
test_df_sample['is_flagged'] = test_df_sample['risk_level'].isin(['Medium', 'High']).astype(int)

y_true = test_df_sample['isFraud']
y_pred = test_df_sample['is_flagged']

tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0

print(f'\n--- NEW CONFUSION MATRIX ---')
print(f'True Positives: {tp}')
print(f'False Positives: {fp}')
print(f'False Negatives: {fn}')
print(f'Precision: {precision:.4f}')
print(f'Recall: {recall:.4f}')

# Get top SHAP features for a flagged alert
flagged = test_df_sample[test_df_sample['is_flagged'] == 1]
if len(flagged) > 0:
    first_alert_idx = flagged.index[0]
    first_alert_row = X_test_sample.loc[[first_alert_idx]]
    
    shap_model = ensemble_red.estimators_[0]
    explainer = shap.TreeExplainer(shap_model)
    values = explainer.shap_values(first_alert_row)
    if isinstance(values, list): values = values[1]
    elif getattr(values, "ndim", 0) == 3: values = values[:, :, 1]
    
    feature_names = list(first_alert_row.columns)
    shap_vals = values[0]
    results = [{"label": str(name), "value": float(val)} for name, val in zip(feature_names, shap_vals)]
    results.sort(key=lambda x: abs(x["value"]), reverse=True)
    
    print("\n--- NEW TOP SHAP FEATURES ---")
    for r in results[:5]:
        print(f"  {r['label']}: {r['value']}")
