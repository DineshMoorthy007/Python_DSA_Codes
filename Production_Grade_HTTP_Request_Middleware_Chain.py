from abc import ABC, abstractmethod
from typing import Any

class Handler(ABC):
    """Abstract interface for defining the structural links in the chain."""
    @abstractmethod
    def set_next(self, handler: 'Handler') -> 'Handler':
        pass

    @abstractmethod
    def handle(self, request: dict[str, Any]) -> str | None:
        pass


class AbstractHandler(Handler):
    """Base helper class that implements the default chaining behavior."""
    def __init__(self):
        self._next_handler: Handler | None = None

    def set_next(self, handler: Handler) -> Handler:
        self._next_handler = handler
        # Returning the incoming handler allows for elegant method chaining
        return handler

    def handle(self, request: dict[str, Any]) -> str | None:
        if self._next_handler:
            return self._next_handler.handle(request)
        return None  # Reached the end of the chain with no objections


# --- Custom Concrete Middleware Handlers ---

class AuthenticationHandler(AbstractHandler):
    def handle(self, request: dict[str, Any]) -> str | None:
        print("[MIDDLEWARE] Checking authentication credentials...")
        if not request.get("authenticated", False):
            return "401 Unauthorized: Invalid or missing token credentials."
        return super().handle(request)


class ValidationHandler(AbstractHandler):
    def handle(self, request: dict[str, Any]) -> str | None:
        print("[MIDDLEWARE] Validating request body format...")
        if "payload" not in request or not request["payload"]:
            return "400 Bad Request: Missing structured data payload fields."
        return super().handle(request)


class RateLimitHandler(AbstractHandler):
    def handle(self, request: dict[str, Any]) -> str | None:
        print("[MIDDLEWARE] Checking rate limits...")
        if request.get("request_count", 0) > 3:
            return "429 Too Many Requests: Rate limit ceiling breached."
        return super().handle(request)


if __name__ == "__main__":
    print("--- Initializing Pipeline Middleware Chain ---")
    
    # 1. Instantiate the individual concrete middleware modules
    auth = AuthenticationHandler()
    validator = ValidationHandler()
    rate_limiter = RateLimitHandler()

    # 2. Stitch the pipeline chain together cleanly via method chaining
    auth.set_next(validator).set_next(rate_limiter)

    # Scenario A: An invalid request that will fail validation mid-chain
    bad_request = {
        "authenticated": True,
        "payload": "",
        "request_count": 1
    }
    print("\n[STREAM 1] Processing Bad Request Payload:")
    error = auth.handle(bad_request)
    print(f"Result -> {error if error else '200 OK: Request processed successfully.'}")

    print("-" * 65)

    # Scenario B: A clean request that passes all gates successfully
    good_request = {
        "authenticated": True,
        "payload": {"user_id": 99},
        "request_count": 1
    }
    print("[STREAM 2] Processing Valid Request Payload:")
    error = auth.handle(good_request)
    print(f"Result -> {error if error else '200 OK: Request processed successfully.'}")

# Output :
# --- Initializing Pipeline Middleware Chain ---

# [STREAM 1] Processing Bad Request Payload:
# [MIDDLEWARE] Checking authentication credentials...
# [MIDDLEWARE] Validating request body format...
# Result -> 400 Bad Request: Missing structured data payload fields.
# -----------------------------------------------------------------
# [STREAM 2] Processing Valid Request Payload:
# [MIDDLEWARE] Checking authentication credentials...
# [MIDDLEWARE] Validating request body format...
# [MIDDLEWARE] Checking rate limits...
# Result -> 200 OK: Request processed successfully.
