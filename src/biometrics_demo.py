"""Synthetic keystroke-dynamics demonstration for the fraud-detection MVP.

This file uses only SYNTHETIC data. It does not collect, infer, or identify
real biometric information.
"""

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_SEED = 42
N_SESSIONS_PER_CLASS = 800
N_KEY_PAIRS = 8


def generate_synthetic_keystrokes():
    """Create clearly labelled SYNTHETIC legitimate and impostor sessions.

    Each session contains dwell times (key-down to key-up) and flight times
    (key-up to the next key-down), measured in milliseconds.
    """
    rng = np.random.default_rng(RANDOM_SEED)

    # SYNTHETIC legitimate-user pattern: repeatable timing with low variation.
    genuine_dwell = rng.normal(loc=92, scale=7, size=(N_SESSIONS_PER_CLASS, N_KEY_PAIRS))
    genuine_flight = rng.normal(loc=118, scale=10, size=(N_SESSIONS_PER_CLASS, N_KEY_PAIRS))

    # SYNTHETIC impostor pattern: now set to realistically overlap with genuine users.
    impostor_dwell = rng.normal(loc=105, scale=25, size=(N_SESSIONS_PER_CLASS, N_KEY_PAIRS))
    impostor_flight = rng.normal(loc=135, scale=30, size=(N_SESSIONS_PER_CLASS, N_KEY_PAIRS))

    genuine = np.hstack([genuine_dwell, genuine_flight])
    impostor = np.hstack([impostor_dwell, impostor_flight])
    # The live page submits only aggregate timings, so train on the same two
    # features it can provide: mean dwell time and mean flight time.
    X = np.vstack([
        np.column_stack([genuine_dwell.mean(axis=1), genuine_flight.mean(axis=1)]),
        np.column_stack([impostor_dwell.mean(axis=1), impostor_flight.mean(axis=1)]),
    ])
    y = np.concatenate([np.ones(N_SESSIONS_PER_CLASS, dtype=int), np.zeros(N_SESSIONS_PER_CLASS, dtype=int)])
    return X, y, genuine, impostor


def equal_error_rate(y_true, scores):
    """Return the threshold where false-accept and false-reject rates meet."""
    fpr, tpr, thresholds = roc_curve(y_true, scores)
    fnr = 1 - tpr
    index = np.argmin(np.abs(fpr - fnr))
    return float((fpr[index] + fnr[index]) / 2), float(thresholds[index])


def save_separation_plot(genuine, impostor, output_path):
    """Plot interpretable aggregate dwell/flight features for both classes."""
    plt.figure(figsize=(8, 6))
    plt.scatter(genuine[:, :N_KEY_PAIRS].mean(axis=1), genuine[:, N_KEY_PAIRS:].mean(axis=1),
                alpha=0.55, label="Genuine user", color="#2ca02c")
    plt.scatter(impostor[:, :N_KEY_PAIRS].mean(axis=1), impostor[:, N_KEY_PAIRS:].mean(axis=1),
                alpha=0.55, label="Impostor", color="#d62728")
    plt.xlabel("Mean dwell time (ms)")
    plt.ylabel("Mean flight time (ms)")
    plt.title("SYNTHETIC keystroke dynamics: genuine vs impostor sessions")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def main():
    X, y, genuine, impostor = generate_synthetic_keystrokes()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=RANDOM_SEED
    )

    classifier = make_pipeline(StandardScaler(), LogisticRegression(random_state=RANDOM_SEED))
    classifier.fit(X_train, y_train)
    probabilities = classifier.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    accuracy = accuracy_score(y_test, predictions)
    eer, threshold = equal_error_rate(y_test, probabilities)

    output_dir = Path(__file__).resolve().parents[1] / "outputs"
    model_dir = Path(__file__).resolve().parents[1] / "models"
    output_dir.mkdir(exist_ok=True)
    model_dir.mkdir(exist_ok=True)
    output_path = output_dir / "biometrics_separation.png"
    model_path = model_dir / "biometrics_classifier.pkl"
    save_separation_plot(genuine, impostor, output_path)
    # The fitted Pipeline includes both the StandardScaler and classifier.
    joblib.dump(classifier, model_path)

    print("Synthetic keystroke-dynamics demo")
    print(f"Sessions: {len(y)} ({N_SESSIONS_PER_CLASS} genuine, {N_SESSIONS_PER_CLASS} impostor)")
    print(f"Classifier: Logistic Regression")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Equal Error Rate (EER): {eer:.4f}")
    print(f"EER threshold: {threshold:.4f}")
    print(f"Saved: {output_path}")
    print(f"Saved classifier pipeline: {model_path}")


if __name__ == "__main__":
    main()
