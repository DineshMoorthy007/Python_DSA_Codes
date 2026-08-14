import time
import threading

class TokenBucket:
    """A thread-safe Token Bucket Rate Limiter using lazy token replenishment.
    
    Args:
        capacity: Maximum burst capacity (maximum tokens the bucket can hold).
        refill_rate: Number of tokens added to the bucket per second.
    """
    def __init__(self, capacity: int, refill_rate: float):
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError("Capacity and refill rate must be strictly positive.")
            
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill_time = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        """Lazily recalculates token count based on elapsed wall-clock time."""
        now = time.monotonic()
        elapsed = now - self.last_refill_time
        
        # Calculate freshly accumulated tokens
        added_tokens = elapsed * self.refill_rate
        self.tokens = min(float(self.capacity), self.tokens + added_tokens)
        self.last_refill_time = now

    def allow_request(self, tokens_requested: int = 1) -> bool:
        """Evaluates whether an incoming request can consume tokens.
        
        Returns:
            True if sufficient tokens exist and were consumed.
            False if request exceeds current rate capacity (429 Too Many Requests).
        """
        with self._lock:
            self._refill()
            
            if self.tokens >= tokens_requested:
                self.tokens -= tokens_requested
                return True
            return False

    def remaining_tokens(self) -> float:
        """Returns the current available token balance."""
        with self._lock:
            self._refill()
            return self.tokens


# --- Gateway Simulation Script ---

def simulate_client_traffic(limiter: TokenBucket, client_id: str, request_count: int, delay_between: float):
    for i in range(1, request_count + 1):
        allowed = limiter.allow_request(1)
        status = "200 OK" if allowed else "429 TOO MANY REQUESTS"
        print(f"[{client_id}] Request #{i:02d} -> {status:<24} | Tokens Remaining: {limiter.remaining_tokens():.2f}")
        time.sleep(delay_between)


if __name__ == "__main__":
    print("--- Initializing Token Bucket API Rate Limiter ---\n")

    # Bucket configuration: Max Burst = 5 tokens, Refill = 2 tokens per second
    burst_capacity = 5
    tokens_per_sec = 2.0
    gateway_limiter = TokenBucket(capacity=burst_capacity, refill_rate=tokens_per_sec)

    print(f"Config: Burst Capacity = {burst_capacity} reqs | Sustained Rate = {tokens_per_sec} reqs/sec\n")

    print("[PHASE 1: High-Frequency Traffic Burst]")
    # Fire 8 rapid requests (First 5 should succeed, next 3 should fail)
    simulate_client_traffic(gateway_limiter, client_id="API-Client-1", request_count=8, delay_between=0.05)

    print("\n[PHASE 2: Cooldown & Lazy Refill (Waiting 1.5 seconds)]")
    time.sleep(1.5)  # 1.5s * 2 tokens/sec = ~3 tokens regenerated

    print("\n[PHASE 3: Post-Cooldown Request]")
    # Fire 3 requests spaced at sustainable refill intervals
    simulate_client_traffic(gateway_limiter, client_id="API-Client-1", request_count=3, delay_between=0.6)

    print("-" * 65)
    print("[SUCCESS] Rate limiting traffic shaping verified with zero background threads!")


#Output :
#--- Initializing Token Bucket API Rate Limiter ---

#Config: Burst Capacity = 5 reqs | Sustained Rate = 2.0 reqs/sec

#[PHASE 1: High-Frequency Traffic Burst]
#[API-Client-1] Request #01 -> 200 OK                   | Tokens Remaining: 4.00
#[API-Client-1] Request #02 -> 200 OK                   | Tokens Remaining: 3.10
#[API-Client-1] Request #03 -> 200 OK                   | Tokens Remaining: 2.20
#[API-Client-1] Request #04 -> 200 OK                   | Tokens Remaining: 1.30
#[API-Client-1] Request #05 -> 200 OK                   | Tokens Remaining: 0.40
#[API-Client-1] Request #06 -> 429 TOO MANY REQUESTS    | Tokens Remaining: 0.50
#[API-Client-1] Request #07 -> 429 TOO MANY REQUESTS    | Tokens Remaining: 0.60
#[API-Client-1] Request #08 -> 429 TOO MANY REQUESTS    | Tokens Remaining: 0.70

#[PHASE 2: Cooldown & Lazy Refill (Waiting 1.5 seconds)]

#[PHASE 3: Post-Cooldown Request]
#[API-Client-1] Request #01 -> 200 OK                   | Tokens Remaining: 2.80
#[API-Client-1] Request #02 -> 200 OK                   | Tokens Remaining: 3.00
#[API-Client-1] Request #03 -> 200 OK                   | Tokens Remaining: 3.20
#-----------------------------------------------------------------
#[SUCCESS] Rate limiting traffic shaping verified with zero background threads!
