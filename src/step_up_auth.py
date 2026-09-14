"""Knowledge-based step-up challenge issued when biometrics deviate (proposal §6.2)."""

from uuid import uuid4

_CHALLENGES = [
    {
        "question_id": "payee-confirm",
        "prompt": "Type the last 4 characters of the destination account to confirm this session.",
        "expected": None,
    },
    {
        "question_id": "amount-confirm",
        "prompt": "Re-enter the transaction amount as an integer (no decimals) to continue.",
        "expected": None,
    },
]


def issue_challenge(tx: dict) -> dict:
    dest = str(tx.get("nameDest") or tx.get("destAccount") or "M0000")
    amount = int(float(tx.get("amount") or 0))
    challenge_id = str(uuid4())
    return {
        "challenge_id": challenge_id,
        "required": True,
        "method": "knowledge_based",
        "alternate_method": "video_confirmation_placeholder",
        "questions": [
            {
                "question_id": "payee-confirm",
                "prompt": f"Confirm last 4 of destination account ending {dest[-4:]}",
                "answer_hint": dest[-4:],
            },
            {
                "question_id": "amount-confirm",
                "prompt": "Re-enter the integer transaction amount",
                "answer_hint": str(amount),
            },
        ],
    }


def verify_challenge(tx: dict, answers: dict) -> dict:
    dest = str(tx.get("nameDest") or tx.get("destAccount") or "M0000")
    amount = str(int(float(tx.get("amount") or 0)))
    payee_ok = str(answers.get("payee-confirm") or "").strip() == dest[-4:]
    amount_ok = str(answers.get("amount-confirm") or "").strip() == amount
    passed = payee_ok and amount_ok
    return {"passed": passed, "payee_ok": payee_ok, "amount_ok": amount_ok}
