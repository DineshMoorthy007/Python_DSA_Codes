import time
import random

def execute_network_request_with_backoff(
    max_retries: int = 4, 
    base_delay: float = 1.0, 
    max_delay: float = 32.0
) -> bool:
    """Executes a network request with exponential backoff and full jitter formatting.
    
    Args:
        max_retries: Total retry attempts before giving up.
        base_delay: Initial wait duration in seconds after the first crash.
        max_delay: Upper limit cap for the delay timing interval.
        
    Returns:
        True if the execution succeeds, False if the attempt limit is exhausted.
    """
    # Mocking an unreliable server connection that only succeeds on attempt 4
    simulated_server_success_attempt = 4
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[REQUEST] Dispatching network packet frame... (Attempt {attempt}/{max_retries})")
            
            # Simulated network constraint execution rule
            if attempt < simulated_server_success_attempt:
                raise ConnectionError("503 Service Unavailable: Remote gateway timeout.")
            
            # Success pathway
            print("  [SUCCESS] 200 OK: Data payload processed successfully.")
            return True

        except ConnectionError as error:
            print(f"  [FAILURE] Network alert: {error}")
            
            if attempt == max_retries:
                print("\n[CRITICAL] Maximum retry allocation exhausted. Aborting pipeline operation.")
                return False
            
            # Math Formula: Calculate raw exponential delay interval step
            # Delay = base_delay * (2 ^ (attempt - 1))
            raw_delay = base_delay * (2 ** (attempt - 1))
            
            # Bound the calculated delay below our max configuration limit cap
            bounded_delay = min(max_delay, raw_delay)
            
            # Apply 'Full Jitter' randomness to spread cluster concurrency windows
            # Random uniform float anywhere from 0 up to bounded_delay
            final_jitter_delay = random.uniform(0, bounded_delay)
            
            print(f"  [BACKOFF] Backing off. Sleeping for {final_jitter_delay:.2f} seconds...")
            time.sleep(final_jitter_delay)
            print("-" * 65)


if __name__ == "__main__":
    print("--- Initializing Resilient Network Gateway ---")
    success = execute_network_request_with_backoff(max_retries=4, base_delay=1.0, max_delay=10.0)
    print(f"\nExecution Pipeline Termination Status -> Result: {success}")

# Output :
# --- Initializing Resilient Network Gateway ---
# [REQUEST] Dispatching network packet frame... (Attempt 1/4)
#   [FAILURE] Network alert: 503 Service Unavailable: Remote gateway timeout.
#   [BACKOFF] Backing off. Sleeping for 0.49 seconds...
# -----------------------------------------------------------------
# [REQUEST] Dispatching network packet frame... (Attempt 2/4)
#   [FAILURE] Network alert: 503 Service Unavailable: Remote gateway timeout.
#   [BACKOFF] Backing off. Sleeping for 0.03 seconds...
# -----------------------------------------------------------------
# [REQUEST] Dispatching network packet frame... (Attempt 3/4)
#   [FAILURE] Network alert: 503 Service Unavailable: Remote gateway timeout.
#   [BACKOFF] Backing off. Sleeping for 3.20 seconds...
# -----------------------------------------------------------------
# [REQUEST] Dispatching network packet frame... (Attempt 4/4)
#   [SUCCESS] 200 OK: Data payload processed successfully.

# Execution Pipeline Termination Status -> Result: True
