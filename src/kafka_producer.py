"""
Real-time Kafka Transaction Streaming Producer
----------------------------------------------
Ingests transaction logs (PaySim dataset) and streams JSON payloads to the Kafka topic
'transactions-stream' for real-time microservices fraud scoring.
"""

import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union

import pandas as pd
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import (
    KafkaConnectionError,
    KafkaTimeoutError,
    TopicAlreadyExistsError,
    BrokerNotAvailableError,
    NodeNotReadyError,
    MetadataEmptyBrokerList,
)

try:
    from kafka.errors import NoBrokersAvailable
except ImportError:
    # kafka-python 2.x removed NoBrokersAvailable; empty broker lists raise this instead.
    NoBrokersAvailable = MetadataEmptyBrokerList

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("KafkaProducer")

# Configuration Constants
DEFAULT_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
DEFAULT_TOPIC = os.getenv("KAFKA_TOPIC", "transactions-stream")
BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = BASE_DIR / "data" / "processed" / "test.csv"


class KafkaTransactionProducer:
    """
    Production-ready Kafka Producer for streaming financial transactions.
    Supports live Kafka broker connection as well as graceful dry-run simulation mode.
    """

    def __init__(
        self,
        bootstrap_servers: str = DEFAULT_BOOTSTRAP_SERVERS,
        topic: str = DEFAULT_TOPIC,
        client_id: str = "fraud-transaction-producer"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.client_id = client_id
        self.producer: Optional[KafkaProducer] = None
        self.is_dry_run = False

        self._initialize_producer()

    def _initialize_producer(self) -> None:
        """Connect to Kafka broker and create target topic if missing."""
        try:
            self._ensure_topic()
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                value_serializer=lambda msg: json.dumps(msg).encode("utf-8"),
                acks="all",
                retries=3,
                request_timeout_ms=5000
            )
            logger.info(f"Connected to Kafka broker at '{self.bootstrap_servers}' on topic '{self.topic}'.")
        except (KafkaConnectionError, KafkaTimeoutError, NoBrokersAvailable, Exception) as err:
            logger.warning(f"Unable to connect to live Kafka broker at '{self.bootstrap_servers}': {err}")
            logger.warning("Falling back to Simulated Stream Mode for local testing.")
            self.is_dry_run = True
            self.producer = None

    def _ensure_topic(self) -> None:
        """Create target Kafka topic if it does not already exist."""
        try:
            admin = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id=f"{self.client_id}-admin",
                request_timeout_ms=3000
            )
            new_topic = NewTopic(name=self.topic, num_partitions=1, replication_factor=1)
            admin.create_topics([new_topic])
            logger.info(f"Created Kafka topic '{self.topic}'.")
            admin.close()
        except TopicAlreadyExistsError:
            pass
        except Exception as e:
            logger.debug(f"Topic administration check notice: {e}")

    @staticmethod
    def format_payload(transaction_id: Union[int, str], row: Union[pd.Series, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sanitize and format raw transaction record into standard JSON transaction message.
        """
        if isinstance(row, pd.Series):
            payload = json.loads(row.to_json())
        else:
            payload = dict(row)

        now_epoch = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()

        payload["transaction_id"] = transaction_id
        payload["produced_at"] = now_epoch
        payload["timestamp_iso"] = now_iso
        payload["source"] = "PaySim_Stream_Producer"

        return payload

    def send_transaction(self, payload: Dict[str, Any], timeout: float = 5.0) -> bool:
        """
        Publish a single transaction message to Kafka topic.
        """
        if self.is_dry_run or self.producer is None:
            logger.info(
                f"[SIMULATION] Streamed Transaction #{payload.get('transaction_id')} "
                f"| amount={payload.get('amount', 0.0):.2f} | type={payload.get('type', 'TRANSFER')}"
            )
            return True

        try:
            future = self.producer.send(self.topic, value=payload)
            metadata = future.get(timeout=timeout)
            logger.info(
                f"[PRODUCER] Sent Transaction #{payload.get('transaction_id')} "
                f"to {metadata.topic} [partition {metadata.partition} @ offset {metadata.offset}]"
            )
            return True
        except Exception as err:
            logger.error(f"Failed to publish transaction #{payload.get('transaction_id')}: {err}")
            return False

    def stream_from_csv(
        self,
        csv_path: Union[str, Path] = DEFAULT_DATA_PATH,
        count: int = 200,
        delay_range: Tuple[float, float] = (0.05, 0.15)
    ) -> int:
        """
        Stream rows from transaction dataset CSV into Kafka topic.
        """
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Transaction dataset CSV not found at '{path}'")

        logger.info(f"Reading dataset from '{path}' (target count: {count} transactions)...")
        df = pd.read_csv(path, nrows=count)

        sent_count = 0
        for tx_id, row in df.iterrows():
            payload = self.format_payload(tx_id, row)
            success = self.send_transaction(payload)
            if success:
                sent_count += 1

            if delay_range[1] > 0:
                time.sleep(random.uniform(delay_range[0], delay_range[1]))

        self.flush()
        logger.info(f"Successfully streamed {sent_count}/{len(df)} transactions.")
        return sent_count

    def flush(self) -> None:
        """Flush pending messages in producer queue."""
        if self.producer:
            self.producer.flush()

    def close(self) -> None:
        """Close producer connection cleanly."""
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
                logger.info("Kafka producer closed cleanly.")
            except Exception as e:
                logger.warning(f"Error closing Kafka producer: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main() -> None:
    logger.info("Starting Real-time Kafka Transaction Streaming Producer...\n")
    
    # Instantiate and stream transactions
    with KafkaTransactionProducer() as producer:
        if DEFAULT_DATA_PATH.exists():
            producer.stream_from_csv(csv_path=DEFAULT_DATA_PATH, count=20, delay_range=(0.02, 0.05))
        else:
            logger.info("Dataset CSV not found; generating synthetic sample stream...")
            for i in range(10):
                sample_record = {
                    "amount": round(random.uniform(1000, 250000), 2),
                    "step": 1,
                    "type": "TRANSFER",
                    "oldbalanceOrg": 50000.0,
                    "newbalanceOrig": 0.0,
                    "oldbalanceDest": 10000.0,
                    "newbalanceDest": 60000.0
                }
                payload = producer.format_payload(f"syn-{i+1}", sample_record)
                producer.send_transaction(payload)
                time.sleep(0.05)


if __name__ == "__main__":
    main()
