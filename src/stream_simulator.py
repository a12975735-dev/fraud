"""Lightweight real-time transaction producer-consumer simulation.

This module simulates the producer-consumer pattern of a real-time streaming
platform (e.g. Apache Kafka) using Python's built-in queue and threading
modules. In a production deployment, this would be replaced by an actual
message broker such as Kafka or AWS Kinesis; the simulation demonstrates the
same architectural pattern — decoupled, asynchronous transaction ingestion and
scoring — within the scope of this project.
"""

import argparse
import csv
import json
import queue
import random
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
TEST_PATH = BASE_DIR / "data" / "processed" / "test.csv"
LOG_PATH = BASE_DIR / "outputs" / "stream_simulation_log.csv"
SENTINEL = object()


def api_payload(row):
    """Map a PaySim test row to the fields accepted by the scoring API."""
    return {
        "amount": float(row["amount"]),
        "oldbalanceDest": float(row.get("oldbalanceDest", 0.0)),
        "newbalanceDest": float(row.get("newbalanceDest", 0.0)),
        "step": int(row.get("step", 0)),
        "transaction_velocity": float(row.get("transaction_velocity", 0.0)),
        "amount_deviation": float(row.get("amount_deviation", 0.0)),
        "balance_discrepancy": float(row.get("balance_discrepancy", 0.0)),
        "type": str(row.get("type", "TRANSFER")),
    }


def score_transaction(endpoint, payload, timeout):
    """Call the existing FastAPI scoring endpoint using the standard library."""
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def producer(transactions, message_queue, delay_min, delay_max):
    """Place transactions onto the queue one at a time, like a broker producer."""
    for transaction_id, row in transactions.iterrows():
        produced_at = time.perf_counter()
        message_queue.put((int(transaction_id), api_payload(row), produced_at))
        print(f"[PRODUCER] Streamed transaction #{transaction_id}")
        time.sleep(random.uniform(delay_min, delay_max))
    message_queue.put(SENTINEL)


def consumer(message_queue, endpoint, timeout, records):
    """Pull queued messages continuously and send them to the scoring API."""
    while True:
        item = message_queue.get()
        try:
            if item is SENTINEL:
                return

            transaction_id, payload, produced_at = item
            timestamp = datetime.now(timezone.utc).isoformat()
            try:
                result = score_transaction(endpoint, payload, timeout)
                latency_ms = round((time.perf_counter() - produced_at) * 1000, 2)
                risk_score = result["risk_score"]
                risk_level = result["risk_level"]
                print(
                    f"[CONSUMER] Transaction #{transaction_id} | "
                    f"risk={risk_score} ({risk_level}) | latency={latency_ms:.2f} ms"
                )
            except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError) as error:
                latency_ms = round((time.perf_counter() - produced_at) * 1000, 2)
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
        finally:
            message_queue.task_done()


def save_log(records):
    LOG_PATH.parent.mkdir(exist_ok=True)
    with LOG_PATH.open("w", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(
            log_file,
            fieldnames=["transaction_id", "risk_score", "risk_level", "latency_ms", "timestamp"],
        )
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(description="Simulate a real-time fraud-scoring stream.")
    parser.add_argument("--count", type=int, default=200, help="Transactions to stream (default: 200).")
    parser.add_argument("--delay-min", type=float, default=0.05, help="Minimum producer delay in seconds.")
    parser.add_argument("--delay-max", type=float, default=0.05, help="Maximum producer delay in seconds.")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8000/score_transaction")
    parser.add_argument("--timeout", type=float, default=10.0, help="API request timeout in seconds.")
    args = parser.parse_args()

    if args.count <= 0 or args.delay_min < 0 or args.delay_max < args.delay_min:
        parser.error("count must be positive and 0 <= delay-min <= delay-max.")

    transactions = pd.read_csv(TEST_PATH, nrows=args.count)
    if len(transactions) < args.count:
        raise ValueError(f"Requested {args.count} transactions, but only found {len(transactions)}.")

    message_queue = queue.Queue()
    records = []
    start_time = time.perf_counter()

    consumer_thread = threading.Thread(
        target=consumer, args=(message_queue, args.endpoint, args.timeout, records), name="consumer"
    )
    producer_thread = threading.Thread(
        target=producer,
        args=(transactions, message_queue, args.delay_min, args.delay_max),
        name="producer",
    )
    consumer_thread.start()
    producer_thread.start()
    producer_thread.join()
    consumer_thread.join()
    elapsed_seconds = time.perf_counter() - start_time

    save_log(records)
    successful = [record for record in records if isinstance(record["risk_score"], int)]
    average_latency = sum(record["latency_ms"] for record in successful) / len(successful) if successful else 0
    high_risk = sum(record["risk_level"] == "high" for record in successful)
    throughput = len(records) / elapsed_seconds if elapsed_seconds else 0

    print("\n--- Stream simulation summary ---")
    print(f"Total transactions processed: {len(records)}")
    print(f"Average end-to-end latency: {average_latency:.2f} ms")
    print(f"Transactions flagged high-risk: {high_risk}")
    print(f"Throughput: {throughput:.2f} transactions/second")
    print(f"Saved full log: {LOG_PATH}")


if __name__ == "__main__":
    main()
