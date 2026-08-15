import time
import threading
from enum import Enum, auto
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = auto()     # Normal operations: requests flow through directly
    OPEN = auto()       # Tripped state: requests fail immediately without calling downstream
    HALF_OPEN = auto()  # Probe state: allows limited trial requests to test downstream health


class CircuitBreakerOpenException(Exception):
    """Raised when an operation is attempted while the circuit is tripped OPEN."""
    pass


class CircuitBreaker:
    """A thread-safe Circuit Breaker implementing failure thresholds and exponential backoff."""
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 2.0,
        backoff_factor: float = 2.0,
        max_timeout: float = 30.0
    ):
        self.failure_threshold = failure_threshold
        self.base_timeout = recovery_timeout
        self.current_timeout = recovery_timeout
        self.backoff_factor = backoff_factor
        self.max_timeout = max_timeout

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float = 0.0
        self._lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Executes the protected function through the circuit breaker state machine."""
        with self._lock:
            now = time.monotonic()

            # Transition 1: OPEN -> HALF_OPEN (Probe if recovery timeout window has expired)
            if self.state == CircuitState.OPEN:
                if now - self.last_failure_time >= self.current_timeout:
                    self.state = CircuitState.HALF_OPEN
                    print("\n  [PROBE] Circuit entered HALF-OPEN state. Sending canary trial request...")
                else:
                    # Circuit remains tripped -> fail fast immediately
                    raise CircuitBreakerOpenException(
                        f"Circuit is OPEN. Fast-failing request. Retry in {self.current_timeout - (now - self.last_failure_time):.1f}s."
                    )

        # Execute downstream call outside the lock to avoid holding the mutex during network I/O
        try:
            result = func(*args, **kwargs)
        except Exception as err:
            self._handle_failure()
            raise err
        else:
            self._handle_success()
            return result

    def _handle_success(self) -> None:
        """Handles successful execution: resets counters and closes circuit if in HALF_OPEN."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                print("  [RECOVERED] Canary probe succeeded! Closing circuit breaker.")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.current_timeout = self.base_timeout  # Reset exponential backoff

    def _handle_failure(self) -> None:
        """Handles execution failure: records fault and trips circuit if threshold is reached."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.monotonic()

            if self.state == CircuitState.HALF_OPEN:
                # Canary probe failed -> immediately trip OPEN and apply exponential backoff
                self.state = CircuitState.OPEN
                self.current_timeout = min(self.max_timeout, self.current_timeout * self.backoff_factor)
                print(f"  [PROBE FAILED] Downstream still unhealthy. Backing off for {self.current_timeout:.1f}s.")
            elif self.failure_count >= self.failure_threshold:
                # Failure threshold reached -> trip circuit OPEN
                self.state = CircuitState.OPEN
                print(f"\n  [TRIPPED] Failure threshold ({self.failure_threshold}) breached! Circuit is now OPEN.")


# --- Simulation Script ---

def flaky_external_service(should_fail: bool) -> str:
    """Simulates an unreliable external HTTP API endpoint."""
    if should_fail:
        raise ConnectionError("503 Service Unavailable: Database Connection Refused")
    return "200 OK: Payload Delivered"


if __name__ == "__main__":
    print("--- Initializing Resilient Circuit Breaker Engine ---\n")

    # Configure breaker: trips after 3 consecutive failures, initial 1.5s recovery window
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.5, backoff_factor=2.0)

    print("[PHASE 1: Simulating Downstream Service Outage]")
    for i in range(1, 6):
        try:
            res = breaker.call(flaky_external_service, should_fail=True)
            print(f"Request #{i} -> {res}")
        except CircuitBreakerOpenException as e:
            print(f"Request #{i} -> [FAIL FAST] {e}")
        except ConnectionError as e:
            print(f"Request #{i} -> [DOWNSTREAM ERROR] {e}")
        time.sleep(0.1)

    print("\n[PHASE 2: Waiting for Recovery Timeout (1.6s)]")
    time.sleep(1.6)

    print("\n[PHASE 3: Downstream Service Recovers]")
    for i in range(6, 9):
        try:
            res = breaker.call(flaky_external_service, should_fail=False)
            print(f"Request #{i} -> [SUCCESS] {res}")
        except Exception as e:
            print(f"Request #{i} -> [ERROR] {e}")
        time.sleep(0.1)

    print("-" * 65)

# Output :
# --- Initializing Resilient Circuit Breaker Engine ---

# [PHASE 1: Simulating Downstream Service Outage]
# Request #1 -> [DOWNSTREAM ERROR] 503 Service Unavailable: Database Connection Refused
# Request #2 -> [DOWNSTREAM ERROR] 503 Service Unavailable: Database Connection Refused

#   [TRIPPED] Failure threshold (3) breached! Circuit is now OPEN.
# Request #3 -> [DOWNSTREAM ERROR] 503 Service Unavailable: Database Connection Refused
# Request #4 -> [FAIL FAST] Circuit is OPEN. Fast-failing request. Retry in 1.4s.
# Request #5 -> [FAIL FAST] Circuit is OPEN. Fast-failing request. Retry in 1.3s.

# [PHASE 2: Waiting for Recovery Timeout (1.6s)]

# [PHASE 3: Downstream Service Recovers]

#   [PROBE] Circuit entered HALF-OPEN state. Sending canary trial request...
#   [RECOVERED] Canary probe succeeded! Closing circuit breaker.
# Request #6 -> [SUCCESS] 200 OK: Payload Delivered
# Request #7 -> [SUCCESS] 200 OK: Payload Delivered
# Request #8 -> [SUCCESS] 200 OK: Payload Delivered
# -----------------------------------------------------------------
# [FINAL STATE] Breaker State: CLOSED | Failure Count: 0
#     print(f"[FINAL STATE] Breaker State: {breaker.state.name} | Failure Count: {breaker.failure_count}")
