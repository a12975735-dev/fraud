"""Consume Kafka transactions and score them through the local FastAPI service."""

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from kafka import KafkaConsumer
from kafka.errors import KafkaConnectionError, KafkaTimeoutError

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "transactions-stream"
GROUP_ID = "fraud-scoring-consumer"
TRANSACTION_COUNT = 200
ENDPOINT = "http://127.0.0.1:8000/score_transaction"
LOG_PATH = Path(__file__).resolve().parents[1] / "outputs" / "kafka_stream_log.csv"


def api_payload(transaction: dict) -> dict:
    """Keep only the fields accepted by the existing scoring endpoint."""
    return {
        "amount": float(transaction["amount"]),
        "oldbalanceDest": float(transaction.get("oldbalanceDest", 0.0)),
        "newbalanceDest": float(transaction.get("newbalanceDest", 0.0)),
        "step": int(transaction.get("step", 0)),
        "transaction_velocity": float(transaction.get("transaction_velocity", 0.0)),
        "amount_deviation": float(transaction.get("amount_deviation", 0.0)),
        "balance_discrepancy": float(transaction.get("balance_discrepancy", 0.0)),
        "type": str(transaction.get("type", "TRANSFER")),
    }


def score_transaction(payload: dict) -> dict:
    request = Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def save_log(records: list[dict]) -> None:
    LOG_PATH.parent.mkdir(exist_ok=True)
    with LOG_PATH.open("w", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(
            log_file,
            fieldnames=["transaction_id", "risk_score", "risk_level", "latency_ms", "timestamp"],
        )
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    try:
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            group_id=GROUP_ID,
            auto_offset_reset="latest",
            enable_auto_commit=False,
        )
    except (KafkaConnectionError, KafkaTimeoutError) as error:
        raise SystemExit(
            "Could not connect to Kafka at localhost:9092. Ensure the fraud-kafka container is running."
        ) from error

    records = []
    start_time = time.perf_counter()
    print(f"[CONSUMER] Subscribed to Kafka topic '{TOPIC}'. Waiting for transactions...")

    try:
        for message in consumer:
            transaction = json.loads(message.value.decode("utf-8"))
            transaction_id = transaction.get("transaction_id", "unknown")
            timestamp = datetime.now(timezone.utc).isoformat()
            try:
                result = score_transaction(api_payload(transaction))
                latency_ms = round((time.time() - transaction.get("produced_at", time.time())) * 1000, 2)
                risk_score = result["risk_score"]
                risk_level = result["risk_level"]
                print(
                    f"[CONSUMER] Transaction #{transaction_id} | "
                    f"risk={risk_score} ({risk_level}) | latency={latency_ms:.2f} ms"
                )
            except (HTTPError, URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError) as error:
                latency_ms = round((time.time() - transaction.get("produced_at", time.time())) * 1000, 2)
                risk_score = ""
                risk_level = f"error: {error}"
                print(f"[CONSUMER] Transaction #{transaction_id} | {risk_level}")

            records.append({
                "transaction_id": transaction_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "latency_ms": latency_ms,
                "timestamp": timestamp,
            })
            consumer.commit()
            if len(records) == TRANSACTION_COUNT:
                break
    finally:
        consumer.close()

    elapsed_seconds = time.perf_counter() - start_time
    save_log(records)
    successful = [record for record in records if isinstance(record["risk_score"], int)]
    average_latency = sum(record["latency_ms"] for record in successful) / len(successful) if successful else 0
    high_risk = sum(record["risk_level"] == "high" for record in successful)
    throughput = len(records) / elapsed_seconds if elapsed_seconds else 0

    print("\n--- Kafka stream summary ---")
    print(f"Total transactions processed: {len(records)}")
    print(f"Average end-to-end latency: {average_latency:.2f} ms")
    print(f"Transactions flagged high-risk: {high_risk}")
    print(f"Throughput: {throughput:.2f} transactions/second")
    print(f"Saved full log: {LOG_PATH}")


if __name__ == "__main__":
    main()
