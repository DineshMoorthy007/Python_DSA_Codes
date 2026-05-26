import sys

class CommandDispatcher:
    def __init__(self):
        # The core data structure: Mapping strings to callable functions
        self._registry = {}

    def register(self, command_name):
        """A decorator pattern to dynamically register new commands."""
        def decorator(func):
            self._registry[command_name] = func
            return func
        return decorator

    def execute(self, command_str, *args, **kwargs):
        """Routes and executes incoming text commands safely."""
        if command_str not in self._registry:
            print(f"[ERR] Command '{command_str}' is unrecognized.")
            return False
        
        # Pull the function out of the dict and execute it instantly
        return self._registry[command_str](*args, **kwargs)

# --- Instantiation and Dynamic Registration ---
dispatcher = CommandDispatcher()

@dispatcher.register("SYS_INFO")
def system_info():
    print(f"[EXEC] OS Platform: {sys.platform} | Python: {sys.version.split()}")

@dispatcher.register("TELEMETRY")
def send_telemetry(device_id, status="ONLINE"):
    print(f"[EXEC] Device {device_id} reporting state: {status}")

print("--- Initializing Registry Dispatcher ---")
# Simulating incoming instruction packets
dispatcher.execute("SYS_INFO")
dispatcher.execute("TELEMETRY", "NODE-404", status="MAINTENANCE")
dispatcher.execute("FORMAT_DRIVE")

# Output :
# --- Initializing Registry Dispatcher ---
# [EXEC] OS Platform: win32 | Python: ['3.14.4', '(tags/v3.14.4:23116f9,', 'Apr', '7', '2026,', '14:10:54)', '[MSC', 'v.1944', '64', 'bit', '(AMD64)]']
# [EXEC] Device NODE-404 reporting state: MAINTENANCE
# [ERR] Command 'FORMAT_DRIVE' is unrecognized.
