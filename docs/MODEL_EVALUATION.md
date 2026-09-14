# Model Performance Evaluation Report

Compares the ensemble fraud model against the traditional rule-based detector
using accuracy, precision, recall, F1, and ROC-AUC (proposal §2.1 / §7.2).

## Rule-based baseline

{'model': 'RuleBased', 'accuracy': 0.2051183317564148, 'precision': 0.0015705126623200352, 'recall': 0.9683505782105903, 'f1': 0.0031359393232205366, 'auc': 0.5862411001450385}

## Ensemble model

{'model': 'Ensemble_reduced', 'accuracy': 0.9991905850105774, 'precision': 0.697869593285991, 'recall': 0.6579427875836884, 'f1': 0.6773182957393483, 'auc': 0.9474892851884194}

Target KPI from the proposal: fraud accuracy 90–98%, false-positive rate <10%.
These figures are computed on the project's held-out PaySim test split.
