import time
import threading

class TokenBucketRateLimiter:
    """A thread-safe rate limiter implementing the Token Bucket algorithm."""
    def __init__(self, capacity: int, refill_rate: float):
        # Maximum number of tokens the bucket can hold
        self.capacity = capacity
        # How many tokens are added to the bucket per second
        self.refill_rate = refill_rate
        # Initialize the bucket to its full capacity
        self.tokens = float(capacity)
        # Track the absolute timestamp of the last request evaluation
        self.last_refill_time = time.time()
        
        # Lock ensures thread safety across concurrent requests
        self.lock = threading.Lock()

    def _refill(self) -> None:
        """Internal helper to calculate token accumulation based on elapsed time."""
        now = time.time()
        elapsed_time = now - self.last_refill_time
        
        # Calculate tokens earned since last check
        tokens_to_add = elapsed_time * self.refill_rate
        
        # Update token balance without exceeding maximum capacity
        self.tokens = min(float(self.capacity), self.tokens + tokens_to_add)
        self.last_refill_time = now

    def allow_request(self, tokens_requested: int = 1) -> bool:
        """Evaluates whether a request can proceed. Returns True if permitted."""
        with self.lock:
            # Dynamically top up the bucket before evaluation
            self._refill()
            
            # Check if the bucket has enough tokens to fulfill the request
            if self.tokens >= tokens_requested:
                self.tokens -= tokens_requested
                return True
                
            return False  # Rate limit exceeded


if __name__ == "__main__":
    print("--- Initializing Traffic Control Gateway ---")
    # Capacity = 3 tokens, Refills at a rate of 1 token per second
    limiter = TokenBucketRateLimiter(capacity=3, refill_rate=1.0)

    # Simulating a sudden rapid burst of API requests
    print("\n[BURST PHASE] Simulating rapid incoming request fire:")
    for i in range(1, 6):
        allowed = limiter.allow_request()
        status = "ALLOWED" if allowed else "BLOCKED (429 Too Many Requests)"
        print(f"  Request #{i} -> {status}")
        
    print("-" * 55)
    print("[COOL DOWN] Pausing for 2 seconds to allow token regeneration...")
    time.sleep(2.0)
    
    print("\n[RECOVERY PHASE] Evaluating delayed traffic:")
    for i in range(6, 9):
        allowed = limiter.allow_request()
        status = "ALLOWED" if allowed else "BLOCKED"
        print(f"  Request #{i} -> {status}")

# Output :
# --- Initializing Traffic Control Gateway ---

# [BURST PHASE] Simulating rapid incoming request fire:
#   Request #1 -> ALLOWED
#   Request #2 -> ALLOWED
#   Request #3 -> ALLOWED
#   Request #4 -> BLOCKED (429 Too Many Requests)
#   Request #5 -> BLOCKED (429 Too Many Requests)
# -------------------------------------------------------
# [COOL DOWN] Pausing for 2 seconds to allow token regeneration...

# [RECOVERY PHASE] Evaluating delayed traffic:
#   Request #6 -> ALLOWED
#   Request #7 -> ALLOWED
#   Request #8 -> BLOCKED
