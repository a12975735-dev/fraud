import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score


def compute_features_full(df, account_col='nameOrig'):
    df = df.copy()
    if account_col and account_col in df.columns:
        df['transaction_velocity'] = df.groupby(account_col)['step'].transform('count')
        mean_amt = df.groupby(account_col)['amount'].transform('mean')
        df['amount_deviation'] = (df['amount'] - mean_amt).abs()
    else:
        df['transaction_velocity'] = 1
        df['amount_deviation'] = (df['amount'] - df['amount'].mean()).abs()
    expected_new = df['oldbalanceOrg'] - df['amount']
    df['balance_discrepancy'] = (expected_new - df['newbalanceOrig']).abs()
    return df


def compute_features_train_only(df, train_idx, test_idx, account_col='nameOrig'):
    # Only compute train-only derived features for the test subset to avoid mapping over whole DF
    train = df.loc[train_idx]
    test = df.loc[test_idx].copy()
    if account_col and account_col in df.columns:
        train_counts = train.groupby(account_col)['step'].count().to_dict()
        test['transaction_velocity_trainonly'] = test[account_col].map(train_counts).fillna(0).astype(int)
        train_mean = train.groupby(account_col)['amount'].mean().to_dict()
        overall_train_mean = train['amount'].mean()
        test['amount_deviation_trainonly'] = (test['amount'] - test[account_col].map(train_mean).fillna(overall_train_mean)).abs()
    else:
        test['transaction_velocity_trainonly'] = 1
        test['amount_deviation_trainonly'] = (test['amount'] - train['amount'].mean()).abs()
    expected_new = test['oldbalanceOrg'] - test['amount']
    test['balance_discrepancy_trainonly'] = (expected_new - test['newbalanceOrig']).abs()
    return test


def evaluate_rule(df_test):
    rule = ((df_test['oldbalanceOrg'] == df_test['amount']) & (df_test['newbalanceOrig'] == 0)).astype(int)
    return rule


def print_metrics(name, y_true, y_pred, y_score=None):
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
    print(f"{name}: accuracy={acc:.4f}, precision={prec:.4f}, recall={rec:.4f}, f1={f1:.4f}, auc={auc:.4f}")


def main():
    base = os.path.dirname(os.path.dirname(__file__))
    raw_path = os.path.join(base, 'PS_20174392719_1491204439457_log.csv')
    if not os.path.exists(raw_path):
        raw_path = os.path.join(base, 'data', 'PS_20174392719_1491204439457_log.csv')
    if not os.path.exists(raw_path):
        print('Raw data file not found:', raw_path)
        return

    df = pd.read_csv(raw_path)
    print('Loaded raw df shape:', df.shape, flush=True)
    label_col = None
    for c in df.columns:
        if c.lower() in ('isfraud', 'fraud'):
            label_col = c
            break
    if label_col is None:
        print('No label column found in raw data')
        return

    # Split as data_prep did
    train_idx, test_idx = train_test_split(df.index, test_size=0.2, stratify=df[label_col], random_state=42)
    train_idx = list(train_idx)
    test_idx = list(test_idx)

    # Method A: features computed on full dataset then split (leaky)
    df_fullfeat = compute_features_full(df)
    df_A_test = df_fullfeat.loc[test_idx].copy()

    # Method B: compute features using train-only stats
    df_B_test = compute_features_train_only(df, train_idx, test_idx)

    # Compare engineered features between methods for test set
    dif_amt = (df_A_test['amount_deviation'] != df_B_test['amount_deviation_trainonly']).sum()
    dif_vel = (df_A_test['transaction_velocity'] != df_B_test['transaction_velocity_trainonly']).sum()
    total_test = len(test_idx)
    print('\nFeature engineering comparison on test set:', flush=True)
    print('Total test rows:', total_test, flush=True)
    print('Rows where amount_deviation differs (A vs B):', dif_amt, f'({dif_amt/total_test:.4%})', flush=True)
    print('Rows where transaction_velocity differs (A vs B):', dif_vel, f'({dif_vel/total_test:.4%})', flush=True)
    print('balance_discrepancy difference count:', (df_A_test['balance_discrepancy'] != df_B_test['balance_discrepancy_trainonly']).sum(), flush=True)

    # Train XGBoost on Method A (leaky) using subsample for speed
    feat_cols = ['step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest', 'transaction_velocity', 'amount_deviation', 'balance_discrepancy']
    available = [c for c in feat_cols if c in df_fullfeat.columns]
    print('\nTraining XGBoost on leaky features (Method A) using subsample...', flush=True)
    X = df_fullfeat[available]
    y = df_fullfeat[label_col]
    MAX_TRAIN = 50000
    if len(X) > MAX_TRAIN:
        # sample stratified
        from sklearn.model_selection import StratifiedShuffleSplit
        sss = StratifiedShuffleSplit(n_splits=1, train_size=MAX_TRAIN, random_state=42)
        idx, _ = next(sss.split(X, y))
        Xs = X.iloc[idx]
        ys = y.iloc[idx]
    else:
        Xs = X
        ys = y

    model = XGBClassifier(n_estimators=100, use_label_encoder=False, eval_metric='logloss', n_jobs=8, random_state=42)
    model.fit(Xs, ys)

    # Feature importances
    importances = dict(zip(available, model.feature_importances_))
    sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    print('\nXGBoost feature importances (highest to lowest):', flush=True)
    for feat, imp in sorted_imp:
        print(f' - {feat}: {imp:.6f}', flush=True)

    # Check if single feature dominates
    total_imp = sum(importances.values())
    top_feat, top_imp = sorted_imp[0]
    if total_imp > 0 and top_imp / total_imp > 0.5:
        print(f"\nWARNING: single feature '{top_feat}' accounts for {top_imp/total_imp:.1%} of total importance")

    # Evaluate rule-based pattern on test set
    df_test = df_A_test
    y_test = df_test[label_col]
    rule_preds = evaluate_rule(df_test)
    print('\nRule-based (oldbalanceOrg==amount AND newbalanceOrig==0) performance on test set:', flush=True)
    print_metrics('RulePattern', y_test, rule_preds)

    # Also test using only balance columns with a simple model
    from sklearn.ensemble import RandomForestClassifier
    bal_cols = ['oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest']
    bal_cols = [c for c in bal_cols if c in df_fullfeat.columns]
    X_bal_train = df_fullfeat.loc[train_idx, bal_cols]
    y_bal_train = df_fullfeat.loc[train_idx, label_col]
    X_bal_test = df_fullfeat.loc[test_idx, bal_cols]
    y_bal_test = df_fullfeat.loc[test_idx, label_col]
    rf_bal = RandomForestClassifier(n_estimators=100, class_weight='balanced', n_jobs=-1, random_state=42)
    rf_bal.fit(X_bal_train, y_bal_train)
    bal_preds = rf_bal.predict(X_bal_test)
    bal_probs = rf_bal.predict_proba(X_bal_test)[:, 1]
    print('\nRandomForest using only balance columns performance:', flush=True)
    print_metrics('RF_balance_only', y_bal_test, bal_preds, bal_probs)


if __name__ == '__main__':
    main()
