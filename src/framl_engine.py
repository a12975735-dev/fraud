"""Unified FRAML view: fraud rings, mule heuristics, and GraphSAGE lookup."""

import json
from pathlib import Path

INDEX_PATH = Path(__file__).resolve().parents[1] / "models" / "framl_index.json"


def _load_index() -> dict:
    if not INDEX_PATH.exists():
        return {"rings": [], "mule_destinations": [], "high_risk_countries": [], "embeddings": {}}
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


_INDEX = _load_index()
_RING_ACCOUNTS = {account for ring in _INDEX.get("rings", []) for account in ring}
_MULES = set(_INDEX.get("mule_destinations", []))
_HIGH_RISK_REGIONS = set(_INDEX.get("high_risk_countries", []))


def score_framl(tx: dict) -> dict:
    origin = str(tx.get("nameOrig") or tx.get("originAccount") or "")
    dest = str(tx.get("nameDest") or tx.get("destAccount") or "")
    region = str(tx.get("region") or "").upper()
    amount = float(tx.get("amount") or 0.0)
    tx_type = str(tx.get("type") or "").upper()
    flags = []
    gnn_score = 0

    if origin in _RING_ACCOUNTS or dest in _RING_ACCOUNTS:
        flags.append("fraud_ring_member")
        gnn_score = max(gnn_score, 82)
    if dest in _MULES:
        flags.append("money_mule_destination")
        gnn_score = max(gnn_score, 88)
    if region in _HIGH_RISK_REGIONS and amount >= 5000:
        flags.append("high_risk_corridor")
        gnn_score = max(gnn_score, 60)
    if tx_type in {"TRANSFER", "CASH_OUT"} and amount >= 100000 and dest.startswith("M"):
        flags.append("merchant_drain_pattern")
        gnn_score = max(gnn_score, 70)

    embeddings = _INDEX.get("embeddings", {})
    origin_embedding = embeddings.get(origin)
    dest_embedding = embeddings.get(dest)

    return {
        "aml_flag": len(flags) > 0,
        "aml_labels": flags,
        "gnn_risk_score": gnn_score,
        "origin_in_ring": origin in _RING_ACCOUNTS,
        "dest_in_ring": dest in _RING_ACCOUNTS,
        "origin_embedding": origin_embedding,
        "dest_embedding": dest_embedding,
        "region": region or None,
    }


def reload_index() -> None:
    global _INDEX, _RING_ACCOUNTS, _MULES, _HIGH_RISK_REGIONS
    _INDEX = _load_index()
    _RING_ACCOUNTS = {account for ring in _INDEX.get("rings", []) for account in ring}
    _MULES = set(_INDEX.get("mule_destinations", []))
    _HIGH_RISK_REGIONS = set(_INDEX.get("high_risk_countries", []))
