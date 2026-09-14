"""Level-1 rule screen for known-bad scenarios (proposal §6.1)."""

from pathlib import Path

BLACKLIST_PATH = Path(__file__).resolve().parents[1] / "config" / "ip_blacklist.txt"


def load_ip_blacklist() -> set[str]:
    if not BLACKLIST_PATH.exists():
        return set()
    blocked = set()
    for line in BLACKLIST_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            blocked.add(stripped)
    return blocked


_IP_BLACKLIST = load_ip_blacklist()


def evaluate_rules(tx: dict) -> dict:
    """Return a deterministic known-bad hit, or a pass-through result."""
    source_ip = str(tx.get("sourceIp") or tx.get("source_ip") or "")
    amount = float(tx.get("amount") or 0.0)
    tx_type = str(tx.get("type") or "").upper()
    hits = []

    if source_ip in _IP_BLACKLIST:
        hits.append({"rule": "blacklisted_ip", "detail": source_ip})
    if amount >= 10000 and str(tx.get("nameOrig") or "").startswith("NEW"):
        hits.append({"rule": "new_account_high_value", "detail": f"amount={amount}"})
    if tx_type == "CASH_OUT" and amount >= 200000:
        hits.append({"rule": "large_cash_out", "detail": f"amount={amount}"})

    triggered = len(hits) > 0
    return {
        "level": 1,
        "triggered": triggered,
        "hits": hits,
        "risk_score": 99 if triggered else 0,
        "label": "known_bad" if triggered else "pass",
    }
