"""Append-only audit logging for automated fraud-scoring decisions.

This append-only audit log provides the record-keeping foundation required under GDPR Article 22 (right to explanation for automated decisions) and the EU AI Act's requirements for high-risk AI systems (Article 12, record-keeping). A production system would additionally require tamper-evident storage (e.g. a write-once database or blockchain-backed log), role-based access control for auditors, and automated model-drift/fairness monitoring, which are noted as further extensions.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4


AUDIT_LOG_PATH = Path(__file__).resolve().parents[1] / "outputs" / "audit_log.jsonl"
_WRITE_LOCK = Lock()


def log_decision(*, model_name: str, input_features: dict, risk_score: int,
                 risk_level: str, top_reason_codes: list[dict]) -> str:
    """Append one immutable-style JSON Lines decision record and return its ID."""
    decision_id = str(uuid4())
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision_id": decision_id,
        "model_name": model_name,
        "input_features": input_features,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "top_reason_codes": top_reason_codes,
    }

    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    encoded_record = json.dumps(record, default=str, separators=(",", ":"))
    # Append mode ensures a new record is added rather than replacing earlier decisions.
    with _WRITE_LOCK, AUDIT_LOG_PATH.open("a", encoding="utf-8") as audit_file:
        audit_file.write(encoded_record + "\n")
        audit_file.flush()
        os.fsync(audit_file.fileno())
    return decision_id
