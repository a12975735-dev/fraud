"""Summarise the JSON Lines decision audit trail."""

import json
from collections import Counter
from pathlib import Path


AUDIT_LOG_PATH = Path(__file__).resolve().parents[1] / "outputs" / "audit_log.jsonl"


def main() -> None:
    if not AUDIT_LOG_PATH.exists():
        print("No audit log found. Score a transaction before generating a report.")
        return

    risk_levels: Counter[str] = Counter()
    reason_codes: Counter[str] = Counter()
    total_decisions = 0

    with AUDIT_LOG_PATH.open(encoding="utf-8") as audit_file:
        for line_number, line in enumerate(audit_file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping malformed audit entry on line {line_number}.")
                continue
            total_decisions += 1
            risk_levels[record.get("risk_level", "unknown").lower()] += 1
            for reason in record.get("top_reason_codes", []):
                if isinstance(reason, dict) and reason.get("feature"):
                    reason_codes[reason["feature"]] += 1

    print("Audit trail summary")
    print(f"Total decisions logged: {total_decisions}")
    print("Risk level breakdown:")
    for level in ("low", "medium", "high"):
        print(f"  {level}: {risk_levels[level]}")
    print("Top 3 SHAP reason codes:")
    for reason, count in reason_codes.most_common(3):
        print(f"  {reason}: {count}")


if __name__ == "__main__":
    main()
