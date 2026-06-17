from abc import ABC, abstractmethod

class Observer(ABC):
    """Abstract interface defining the blueprint for all listening entities."""
    @abstractmethod
    def update(self, payload: str) -> None:
        pass


class Subject:
    """The central core that monitors state changes and broadcasts notifications."""
    def __init__(self):
        # A set prevents duplicate subscriptions from the same entity
        self._observers: set[Observer] = set()
        self._state: str = ""

    def attach(self, observer: Observer) -> None:
        """Registers an observer to the broadcasting network."""
        self._observers.add(observer)

    def detach(self, observer: Observer) -> None:
        """Removes an observer from the broadcasting network."""
        self._observers.discard(observer)

    def set_state(self, new_state: str) -> None:
        """Updates the internal state and automatically triggers a broadcast."""
        print(f"\n[SUBJECT] State updating to: '{new_state}'")
        self._state = new_state
        self._notify_all()

    def _notify_all(self) -> None:
        """Dispatches the updated state information to every single subscriber."""
        for observer in self._observers:
            observer.update(self._state)


# --- Custom Implementations of the Observer Interface ---

class MobileAppNotification(Observer):
    def update(self, payload: str) -> None:
        print(f"  [MOBILE ALERT] Push notification dispatched: System is now {payload}")


class AnalyticsDashboard(Observer):
    def update(self, payload: str) -> None:
        print(f"  [ANALYTICS] Telemetry logged: State transition to '{payload}' captured.")


if __name__ == "__main__":
    print("--- Initializing Observer Event Engine ---")
    
    # 1. Instantiate the core monitor engine
    system_monitor = Subject()
    
    # 2. Spin up separate consumer interfaces
    phone_subscriber = MobileAppNotification()
    dashboard_subscriber = AnalyticsDashboard()
    
    # 3. Hook the components into the broadcasting stream
    system_monitor.attach(phone_subscriber)
    system_monitor.attach(dashboard_subscriber)
    
    # 4. Trigger state changes to see the automated broadcast cascade
    system_monitor.set_state("ONLINE")
    system_monitor.set_state("MAINTENANCE_REQUIRED")
    
    # 5. Remove a subscriber dynamically
    print("\n--- Disconnecting Mobile App Client ---")
    system_monitor.detach(phone_subscriber)
    
    # 6. Trigger another update to verify decoupling
    system_monitor.set_state("OFFLINE")

# Output :
# --- Initializing Observer Event Engine ---

# [SUBJECT] State updating to: 'ONLINE'
#   [ANALYTICS] Telemetry logged: State transition to 'ONLINE' captured.
#   [MOBILE ALERT] Push notification dispatched: System is now ONLINE

# [SUBJECT] State updating to: 'MAINTENANCE_REQUIRED'
#   [ANALYTICS] Telemetry logged: State transition to 'MAINTENANCE_REQUIRED' captured.
#   [MOBILE ALERT] Push notification dispatched: System is now MAINTENANCE_REQUIRED

# --- Disconnecting Mobile App Client ---

# [SUBJECT] State updating to: 'OFFLINE'
#   [ANALYTICS] Telemetry logged: State transition to 'OFFLINE' captured.
