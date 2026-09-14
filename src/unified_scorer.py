"""Combine L1 rules, ensemble ML, L3 anomaly, FRAML/GNN, biometrics, SHAP, and LIME."""

from src.anomaly_engine import score_anomaly
from src.framl_engine import score_framl
from src.lime_explain import lime_reason_codes
from src.rule_engine import evaluate_rules
from src.step_up_auth import issue_challenge


def combine_scores(ml_score: int, rule_result: dict, anomaly: dict, framl: dict, biometric_score) -> int:
    scores = [ml_score, anomaly["anomaly_score"], framl["gnn_risk_score"]]
    if rule_result["triggered"]:
        scores.append(rule_result["risk_score"])
    if biometric_score is not None:
        scores.append(int(round(float(biometric_score) * 0.99)))
    return int(max(scores))


def risk_level_for(score: int) -> str:
    if score < 30:
        return "low"
    if score < 70:
        return "medium"
    return "high"


def attach_explanations(model, X, feature_cols, shap_reasons: list[dict]) -> dict:
    lime_reasons = lime_reason_codes(model, X, feature_cols)
    return {
        "shap": shap_reasons,
        "lime": lime_reasons,
        "top_reason_codes": shap_reasons,
    }


def build_unified_view(tx: dict, ml_score: int, shap_reasons: list[dict], model, X, feature_cols) -> dict:
    rules = evaluate_rules(tx)
    anomaly = score_anomaly(tx)
    framl = score_framl(tx)
    biometric = tx.get("biometricRiskScore")
    risk_score = combine_scores(ml_score, rules, anomaly, framl, biometric)
    risk_level = risk_level_for(risk_score)
    explanations = attach_explanations(model, X, feature_cols, shap_reasons)
    step_up = risk_level == "high" or (biometric is not None and float(biometric) >= 70)
    challenge = issue_challenge(tx) if step_up else None
    return {
        "risk_score": risk_score,
        "ml_risk_score": ml_score,
        "biometric_risk_score": biometric,
        "risk_level": risk_level,
        "top_reason_codes": explanations["top_reason_codes"],
        "shap_reason_codes": explanations["shap"],
        "lime_reason_codes": explanations["lime"],
        "level1_rules": rules,
        "level3_anomaly": anomaly,
        "framl": framl,
        "aml_flag": framl["aml_flag"] or rules["triggered"],
        "step_up_required": step_up,
        "step_up_challenge": challenge,
        "region": tx.get("region"),
        "sourceIp": tx.get("sourceIp") or tx.get("source_ip"),
        "nameOrig": tx.get("nameOrig") or tx.get("originAccount"),
        "nameDest": tx.get("nameDest") or tx.get("destAccount"),
    }
