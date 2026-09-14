import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split


def main():
    base = os.path.dirname(os.path.dirname(__file__))
    # preferred location under data/
    data_path = os.path.join(base, 'data', 'PS_20174392719_1491204439457_log.csv')
    # fallback to repository root where the file may already exist
    if not os.path.exists(data_path):
        alt = os.path.join(base, 'PS_20174392719_1491204439457_log.csv')
        if os.path.exists(alt):
            data_path = alt
            print(f"Found data file at repository root, using: {data_path}")
        else:
            print(f"DATA FILE NOT FOUND: looked at {data_path} and {alt}")
            sys.exit(1)

    df = pd.read_csv(data_path)
    print("Loaded file:", data_path)
    print("Shape:", df.shape)
    print("Columns:", list(df.columns))

    label_col = 'isFraud' if 'isFraud' in df.columns else None
    if label_col is None:
        # try lowercase fallback
        for c in df.columns:
            if c.lower() == 'isfraud' or c.lower() == 'fraud':
                label_col = c
                break

    if label_col is None:
        print("Warning: no fraud label column found. Expected 'isFraud'.")
    else:
        vc = df[label_col].value_counts(normalize=True) * 100
        print("Class balance (%):")
        print(vc.to_dict())

    # We'll perform a stratified split first, then compute features using training-set statistics
    account_col = 'nameOrig' if 'nameOrig' in df.columns else None
    if account_col is None:
        print("Warning: no account identifier column found (expected 'nameOrig'). Some features will be skipped.")

    # Split first (stratified)
    if label_col is None or label_col not in df.columns:
        print("Cannot perform stratified split: fraud label missing.")
        out_dir = os.path.join(base, 'data', 'processed')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'processed.csv')
        df.to_csv(out_path, index=False)
        print("Saved processed data to", out_path)
        return

    train, test = train_test_split(df, test_size=0.2, stratify=df[label_col], random_state=42)

    # 1) Transaction velocity and 2) Amount deviation: compute using TRAIN only
    if account_col and 'amount' in train.columns:
        # train-side grouped stats
        train_counts = train.groupby(account_col)['step'].transform('count')
        train['transaction_velocity'] = train_counts
        train_mean_amt = train.groupby(account_col)['amount'].transform('mean')
        train['amount_deviation'] = (train['amount'] - train_mean_amt).abs()
    elif 'amount' in train.columns:
        train['transaction_velocity'] = 1
        train['amount_deviation'] = (train['amount'] - train['amount'].mean()).abs()
    else:
        train['transaction_velocity'] = 1
        train['amount_deviation'] = 0.0

    # 3) Balance discrepancy is row-local; compute for both train and test independently
    if {'oldbalanceOrg', 'newbalanceOrig', 'amount'}.issubset(train.columns):
        expected_new_train = train['oldbalanceOrg'] - train['amount']
        train['balance_discrepancy'] = (expected_new_train - train['newbalanceOrig']).abs()
    else:
        train['balance_discrepancy'] = 0.0

    # Apply TRAIN stats to TEST
    if account_col and 'amount' in test.columns:
        # dicts for fast mapping
        train_counts_series = train.groupby(account_col)['step'].count()
        train_mean_series = train.groupby(account_col)['amount'].mean()
        overall_train_mean = train['amount'].mean()
        overall_train_vel = int(round(train_counts_series.mean())) if not train_counts_series.empty else 1

        test['transaction_velocity'] = test[account_col].map(train_counts_series).fillna(overall_train_vel).astype(int)
        test['amount_deviation'] = (test['amount'] - test[account_col].map(train_mean_series).fillna(overall_train_mean)).abs()
    elif 'amount' in test.columns:
        test['transaction_velocity'] = 1
        test['amount_deviation'] = (test['amount'] - train['amount'].mean()).abs()
    else:
        test['transaction_velocity'] = 1
        test['amount_deviation'] = 0.0

    if {'oldbalanceOrg', 'newbalanceOrig', 'amount'}.issubset(test.columns):
        expected_new_test = test['oldbalanceOrg'] - test['amount']
        test['balance_discrepancy'] = (expected_new_test - test['newbalanceOrig']).abs()
    else:
        test['balance_discrepancy'] = 0.0

    # Drop obviously irrelevant columns (keep features needed)
    drop_cols = [c for c in ['nameOrig', 'nameDest'] if c in train.columns]
    if drop_cols:
        train = train.drop(columns=drop_cols)
        test = test.drop(columns=drop_cols)

    # Handle nulls: drop rows with any nulls (simple and safe for this MVP)
    total_nulls = int(train.isnull().sum().sum() + test.isnull().sum().sum())
    print(f"Total null values in processed train+test data: {total_nulls}")
    if total_nulls > 0:
        train = train.dropna()
        test = test.dropna()
        print("Dropped rows with nulls. New train/test shapes:", train.shape, test.shape)

    # Ensure label column exists for stratified split
    if label_col is None or label_col not in df.columns:
        print("Cannot perform stratified split: fraud label missing.")
        # Save processed file anyway
        out_dir = os.path.join(base, 'data', 'processed')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'processed.csv')
        df.to_csv(out_path, index=False)
        print("Saved processed data to", out_path)
        return

    print("Train shape:", train.shape, "Test shape:", test.shape)

    out_dir = os.path.join(base, 'data', 'processed')
    os.makedirs(out_dir, exist_ok=True)
    train_path = os.path.join(out_dir, 'train.csv')
    test_path = os.path.join(out_dir, 'test.csv')
    train.to_csv(train_path, index=False)
    test.to_csv(test_path, index=False)

    print("Saved processed train/test to:")
    print(" -", train_path)
    print(" -", test_path)

    # Show a sample of engineered features from train
    cols_to_show = ['transaction_velocity', 'amount_deviation', 'balance_discrepancy']
    existing = [c for c in cols_to_show if c in train.columns]
    print("Sample engineered features (train):")
    print(train[existing].head(10).to_string(index=False))


if __name__ == '__main__':
    main()
