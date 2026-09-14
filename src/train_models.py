import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

try:
    from catboost import CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedShuffleSplit


def load_data(base):
    train_path = os.path.join(base, 'data', 'processed', 'train.csv')
    test_path = os.path.join(base, 'data', 'processed', 'test.csv')
    if not os.path.exists(train_path) or not os.path.exists(test_path):
        raise FileNotFoundError('Processed train/test CSVs not found in data/processed/')
    train = pd.read_csv(train_path)
    test = pd.read_csv(test_path)
    return train, test


def prepare_features(df):
    df = df.copy()
    label_col = None
    def _norm(name):
        return ''.join(ch for ch in str(name).lower() if ch.isalnum())
    for c in df.columns:
        n = _norm(c)
        if n == 'isfraud' or n == 'fraud':
            label_col = c
            break
    if label_col is None:
        raise KeyError('Label column is missing (expected isFraud)')
    y = df[label_col]
    leakage_cols = [c for c in ['isFlaggedFraud'] if c in df.columns]
    X = df.drop(columns=[label_col, *leakage_cols])
    if 'type' in X.columns:
        X = pd.get_dummies(X, columns=['type'], drop_first=True)
    X = X.select_dtypes(include=[np.number]).fillna(0)
    return X, y


def rule_based_detector(X):
    amt = X.get('amount', pd.Series(0))
    vel = X.get('transaction_velocity', pd.Series(0))
    preds = ((amt > 200000) | ((vel <= 1) & (amt > 10000))).astype(int)
    return preds


def evaluate_model(name, y_true, y_pred, y_score=None):
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    if y_score is None:
        try:
            auc = roc_auc_score(y_true, y_pred)
        except Exception:
            auc = float('nan')
    else:
        auc = roc_auc_score(y_true, y_score)
    return {
        'model': name,
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1': f1,
        'auc': auc,
    }


def main():
    base = os.path.dirname(os.path.dirname(__file__))
    train, test = load_data(base)

    MAX_TRAIN = 200_000
    label_col = None
    def _norm(name):
        return ''.join(ch for ch in str(name).lower() if ch.isalnum())
    for c in train.columns:
        n = _norm(c)
        if n == 'isfraud' or n == 'fraud':
            label_col = c
            break
    if label_col is None:
        raise KeyError('Label column is missing from processed train CSV (expected isFraud)')

    if len(train) > MAX_TRAIN:
        sss = StratifiedShuffleSplit(n_splits=1, train_size=MAX_TRAIN, random_state=42)
        train_idx, _ = next(sss.split(train, train[label_col]))
        train = train.iloc[train_idx].reset_index(drop=True)

    X_train, y_train = prepare_features(train)
    X_test, y_test = prepare_features(test)

    neg = (y_train == 0).sum()
    pos = (y_train == 1).sum()
    scale_pos_weight = max(1, neg // max(1, pos))

    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', n_jobs=-1, random_state=42)
    xgb = XGBClassifier(n_estimators=200, eval_metric='logloss', scale_pos_weight=scale_pos_weight, n_jobs=8, random_state=42)
    lgb = LGBMClassifier(n_estimators=200, class_weight='balanced', n_jobs=-1, random_state=42)

    estimators = [('xgb', xgb), ('lgb', lgb)]

    print('Training Random Forest...')
    rf.fit(X_train, y_train)
    print('Training XGBoost...')
    xgb.fit(X_train, y_train)
    print('Training LightGBM...')
    lgb.fit(X_train, y_train)

    if CATBOOST_AVAILABLE:
        print('Training CatBoost...')
        cat = CatBoostClassifier(iterations=200, verbose=0, random_seed=42)
        cat.fit(X_train, y_train)
        estimators.append(('cat', cat))

    ensemble = VotingClassifier(estimators=estimators, voting='soft')
    print('Fitting ensemble...')
    sample_n = min(10000, len(X_train))
    sample_idx = X_train.sample(n=sample_n, random_state=42).index
    ensemble.fit(X_train.loc[sample_idx], y_train.loc[sample_idx])

    rule_preds = rule_based_detector(X_test)
    results = []

    rf_probs = rf.predict_proba(X_test)[:, 1]
    rf_preds = (rf_probs > 0.5).astype(int)
    results.append(evaluate_model('RandomForest', y_test, rf_preds, rf_probs))

    xgb_probs = xgb.predict_proba(X_test)[:, 1]
    xgb_preds = (xgb_probs > 0.5).astype(int)
    results.append(evaluate_model('XGBoost', y_test, xgb_preds, xgb_probs))

    lgb_probs = lgb.predict_proba(X_test)[:, 1]
    lgb_preds = (lgb_probs > 0.5).astype(int)
    results.append(evaluate_model('LightGBM', y_test, lgb_preds, lgb_probs))

    if CATBOOST_AVAILABLE:
        cat_probs = cat.predict_proba(X_test)[:, 1]
        cat_preds = (cat_probs > 0.5).astype(int)
        results.append(evaluate_model('CatBoost', y_test, cat_preds, cat_probs))

    ens_probs = ensemble.predict_proba(X_test)[:, 1]
    ens_preds = (ens_probs > 0.5).astype(int)
    results.append(evaluate_model('Ensemble', y_test, ens_preds, ens_probs))

    results.append(evaluate_model('RuleBased', y_test, rule_preds, None))

    df_res = pd.DataFrame(results).set_index('model')
    print('\nModel comparison:')
    print(df_res.round(4).to_string())

    os.makedirs(os.path.join(base, 'models'), exist_ok=True)
    joblib.dump(ensemble, os.path.join(base, 'models', 'ensemble.pkl'))
    print('\nSaved ensemble to models/ensemble.pkl')

    drop_cols = [c for c in ['oldbalanceOrg', 'newbalanceOrig'] if c in X_train.columns]
    if drop_cols:
        print('\nTraining harder-mode ensemble (drop columns:', drop_cols, ')')
        X_train_red = X_train.drop(columns=drop_cols)
        X_test_red = X_test.drop(columns=drop_cols, errors='ignore')

        xgb_r = XGBClassifier(n_estimators=200, eval_metric='logloss', scale_pos_weight=scale_pos_weight, n_jobs=8, random_state=42)
        lgb_r = LGBMClassifier(n_estimators=200, class_weight='balanced', n_jobs=-1, random_state=42)

        xgb_r.fit(X_train_red, y_train)
        lgb_r.fit(X_train_red, y_train)

        ensemble_red = VotingClassifier(estimators=[('xgb', xgb_r), ('lgb', lgb_r)], voting='soft')
        sample_n = min(10000, len(X_train_red))
        sample_idx = X_train_red.sample(n=sample_n, random_state=42).index
        ensemble_red.fit(X_train_red.loc[sample_idx], y_train.loc[sample_idx])

        ens_red_probs = ensemble_red.predict_proba(X_test_red)[:, 1]
        ens_red_preds = (ens_red_probs > 0.5).astype(int)
        results.append(evaluate_model('Ensemble_no_oldbalances', y_test, ens_red_preds, ens_red_probs))

        joblib.dump(ensemble_red, os.path.join(base, 'models', 'ensemble_no_oldbalances.pkl'))
        print('Saved reduced ensemble to models/ensemble_no_oldbalances.pkl')


if __name__ == '__main__':
    main()
