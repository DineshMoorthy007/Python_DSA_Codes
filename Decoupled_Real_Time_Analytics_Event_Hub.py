from abc import ABC, abstractmethod
from typing import Any

class Observer(ABC):
    """Abstract interface for defining the update contract for event consumers."""
    @abstractmethod
    def update(self, event_type: str, payload: Any) -> None:
        """Invoked automatically by the Subject when a registered event triggers."""
        pass


class Subject:
    """The central hub managing subscriptions and broadcasting notifications."""
    def __init__(self):
        # A dictionary mapping event channels to sets of subscribed Observer objects
        self._subscribers: dict[str, set[Observer]] = {}

    def subscribe(self, event_type: str, observer: Observer) -> None:
        """Registers a detached observer module to an event topic stream."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(observer)
        print(f"[REGISTRY] Observer added to topic stream: '{event_type}'")

    def unsubscribe(self, event_type: str, observer: Observer) -> None:
        """Removes an observer's registration from a specific event topic channel."""
        if event_type in self._subscribers and observer in self._subscribers[event_type]:
            self._subscribers[event_type].remove(observer)
            print(f"[REGISTRY] Observer removed from topic stream: '{event_type}'")

    def notify(self, event_type: str, payload: Any) -> None:
        """Broadcasts data changes out to all listeners listening on the channel."""
        if event_type in self._subscribers:
            for observer in self._subscribers[event_type]:
                observer.update(event_type, payload)


# --- Concrete Observer System Implementation Modules ---

class AnalyticsEngine(Observer):
    def update(self, event_type: str, payload: Any) -> None:
        print(f"  [ANALYTICS] Ingesting telemetry data matrix: {payload}")


class AlertSystem(Observer):
    def update(self, event_type: str, payload: Any) -> None:
        # Specialized evaluation rule checking payload severity flags
        if payload.get("status") == "CRITICAL":
            print(f"  [ALERT INBOUND] !!! SEVERE EVENT TRIPPED: {payload.get('msg')} !!!")


if __name__ == "__main__":
    print("--- Initializing Decoupled System Event Broker ---")
    
    # 1. Instantiate the central event hub subject
    telemetry_broker = Subject()

    # 2. Spin up independent business logic consumer observer engines
    dashboard_analytics = AnalyticsEngine()
    ops_pager = AlertSystem()

    # 3. Hook up subscriptions onto target data streams
    telemetry_broker.subscribe("METRICS_STREAM", dashboard_analytics)
    telemetry_broker.subscribe("SYS_ALARM", dashboard_analytics)
    telemetry_broker.subscribe("SYS_ALARM", ops_pager)
    
    print("-" * 65)

    # 4. Trigger broadcasts: The subject remains totally blind to what its listeners do
    print("[EVENT] Dispatching standard resource metrics packet:")
    telemetry_broker.notify("METRICS_STREAM", {"cpu_util_pct": 42.8, "ram_used_gb": 12.1})
    
    print("\n[EVENT] Dispatching severe system alert event state changes:")
    telemetry_broker.notify("SYS_ALARM", {"status": "CRITICAL", "msg": "Database kernel panicking."})

# Output :
# --- Initializing Decoupled System Event Broker ---
# [REGISTRY] Observer added to topic stream: 'METRICS_STREAM'
# [REGISTRY] Observer added to topic stream: 'SYS_ALARM'
# [REGISTRY] Observer added to topic stream: 'SYS_ALARM'
# -----------------------------------------------------------------
# [EVENT] Dispatching standard resource metrics packet:
#   [ANALYTICS] Ingesting telemetry data matrix: {'cpu_util_pct': 42.8, 'ram_used_gb': 12.1}

# [EVENT] Dispatching severe system alert event state changes:
#   [ANALYTICS] Ingesting telemetry data matrix: {'status': 'CRITICAL', 'msg': 'Database kernel panicking.'}
#   [ALERT INBOUND] !!! SEVERE EVENT TRIPPED: Database kernel panicking. !!!
