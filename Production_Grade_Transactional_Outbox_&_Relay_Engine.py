import time
import uuid
import json
import threading
from enum import Enum, auto
from typing import Dict, List, Optional, Any

class OutboxStatus(Enum):
    PENDING = auto()
    PUBLISHED = auto()
    FAILED = auto()


class OutboxMessage:
    """Represents an event record stored in the transactional outbox table."""
    def __init__(self, topic: str, payload: Dict[str, Any]):
        self.id = str(uuid.uuid4())
        self.topic = topic
        self.payload = payload
        self.status = OutboxStatus.PENDING
        self.created_at = time.time()
        self.retry_count = 0

    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "topic": self.topic,
            "payload": self.payload,
            "created_at": self.created_at
        })


class MockDatabaseSession:
    """Simulates a database session supporting ACID transactions."""
    def __init__(self, db_store: 'MockDatabase'):
        self.db = db_store
        self.pending_orders: Dict[str, Dict[str, Any]] = {}
        self.pending_outbox: List[OutboxMessage] = []
        self._in_transaction = False

    def __enter__(self):
        self._in_transaction = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # An error occurred -> Rollback transaction
            self.rollback()
            return False
        # No errors -> Atomically commit changes
        self.commit()
        return True

    def insert_order(self, order_id: str, order_data: Dict[str, Any]) -> None:
        self.pending_orders[order_id] = order_data

    def insert_outbox(self, message: OutboxMessage) -> None:
        self.pending_outbox.append(message)

    def commit(self) -> None:
        with self.db.lock:
            self.db.orders.update(self.pending_orders)
            self.db.outbox.extend(self.pending_outbox)
        self.pending_orders.clear()
        self.pending_outbox.clear()
        self._in_transaction = False

    def rollback(self) -> None:
        self.pending_orders.clear()
        self.pending_outbox.clear()
        self._in_transaction = False


class MockDatabase:
    """Thread-safe simulated persistent database."""
    def __init__(self):
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.outbox: List[OutboxMessage] = []
        self.lock = threading.Lock()

    def session(self) -> MockDatabaseSession:
        return MockDatabaseSession(self)


class MessageBroker:
    """Simulates a message broker (e.g., Kafka / RabbitMQ)."""
    def __init__(self, flaky: bool = False):
        self.flaky = flaky
        self.published_events: List[Dict[str, Any]] = []

    def publish(self, message: OutboxMessage) -> bool:
        if self.flaky and message.retry_count == 0:
            # Simulate a transient network error on the first attempt
            raise ConnectionError("Transient network timeout connecting to message broker")
        
        self.published_events.append(json.loads(message.to_json()))
        return True


class OutboxRelayWorker:
    """Background polling worker that scans pending outbox records and publishes them."""
    def __init__(self, db: MockDatabase, broker: MessageBroker, poll_interval: float = 0.2):
        self.db = db
        self.broker = broker
        self.poll_interval = poll_interval
        self.running = True

    def process_pending_messages(self) -> int:
        processed = 0
        with self.db.lock:
            # Fetch pending records
            pending = [m for m in self.db.outbox if m.status == OutboxStatus.PENDING]

        for msg in pending:
            try:
                self.broker.publish(msg)
                with self.db.lock:
                    msg.status = OutboxStatus.PUBLISHED
                processed += 1
                print(f"  [RELAY PUBLISHED] Event ID '{msg.id[:8]}...' sent to topic '{msg.topic}'")
            except Exception as err:
                with self.db.lock:
                    msg.retry_count += 1
                    if msg.retry_count >= 3:
                        msg.status = OutboxStatus.FAILED
                print(f"  [RELAY RETRY] Failed to publish '{msg.id[:8]}...': {err} (Retry #{msg.retry_count})")
        return processed

    def run_loop(self) -> None:
        while self.running:
            self.process_pending_messages()
            time.sleep(self.poll_interval)


# --- Application Workflow Simulation ---

def create_order(db: MockDatabase, order_id: str, amount: float, customer: str, should_fail: bool = False):
    """Business logic: Atomically inserts order and writes outbox event within one transaction."""
    try:
        with db.session() as tx:
            # 1. Mutate business entity state
            tx.insert_order(order_id, {"amount": amount, "customer": customer, "status": "CREATED"})
            
            # 2. Append event to outbox in the same transaction boundary
            event_payload = {"order_id": order_id, "amount": amount, "customer": customer}
            outbox_event = OutboxMessage(topic="orders.created", payload=event_payload)
            tx.insert_outbox(outbox_event)
            
            if should_fail:
                raise RuntimeError("Simulated internal DB constraint violation during write")

        print(f"[ORDER CREATED] Order '{order_id}' and Outbox Event committed atomically.")
    except Exception as e:
        print(f"[TRANSACTION ROLLED BACK] Order '{order_id}' creation aborted: {e}")


if __name__ == "__main__":
    print("--- Initializing Transactional Outbox & Event Relay Engine ---\n")

    db = MockDatabase()
    broker = MessageBroker(flaky=True)  # Will fail on first attempt to verify retry mechanism
    relay = OutboxRelayWorker(db, broker)

    # Start relay poller on a background thread
    worker_thread = threading.Thread(target=relay.run_loop, daemon=True)
    worker_thread.start()

    print("[PHASE 1: Successful Order with Transient Network Retry]")
    create_order(db, "ORD-9901", 149.99, "alice@example.com")
    time.sleep(0.6)  # Give relay worker time to poll and retry

    print("\n[PHASE 2: Aborted Transaction (Zero Phantom Events)]")
    # Simulate a transaction failure midway (neither order nor outbox event should commit)
    create_order(db, "ORD-9902", 49.50, "bob@example.com", should_fail=True)
    time.sleep(0.4)

    relay.running = False

    print("\n" + "-" * 65)
    print(f"[FINAL DATABASE STATE]")
    print(f"  Committed Orders in DB : {list(db.orders.keys())}")
    print(f"  Outbox Table Records   : {len(db.outbox)} (Status: {db.outbox[0].status.name})")
    print(f"  Broker Received Events : {len(broker.published_events)}")

# Output :
# --- Initializing Transactional Outbox & Event Relay Engine ---

# [PHASE 1: Successful Order with Transient Network Retry]
# [ORDER CREATED] Order 'ORD-9901' and Outbox Event committed atomically.
#   [RELAY RETRY] Failed to publish 'b43b36fc...': Transient network timeout connecting to message broker (Retry #1)
#   [RELAY PUBLISHED] Event ID 'b43b36fc...' sent to topic 'orders.created'

# [PHASE 2: Aborted Transaction (Zero Phantom Events)]
# [TRANSACTION ROLLED BACK] Order 'ORD-9902' creation aborted: Simulated internal DB constraint violation during write

# -----------------------------------------------------------------
# [FINAL DATABASE STATE]
#   Committed Orders in DB : ['ORD-9901']
#   Outbox Table Records   : 1 (Status: PUBLISHED)
#   Broker Received Events : 1
