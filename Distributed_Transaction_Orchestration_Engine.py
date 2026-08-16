from enum import Enum, auto
from typing import Callable, Any

class SagaStepStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()
    FAILED = auto()
    COMPENSATED = auto()


class SagaStep:
    """A discrete unit of work pairing a forward action with a backward compensating action."""
    def __init__(
        self,
        name: str,
        action: Callable[[dict], Any],
        compensation: Callable[[dict], None]
    ):
        self.name = name
        self.action = action
        self.compensation = compensation
        self.status = SagaStepStatus.PENDING


class SagaOrchestrator:
    """Manages forward execution and backward compensation for multi-service transactions."""
    def __init__(self, name: str):
        self.name = name
        self.steps: list[SagaStep] = []

    def add_step(
        self,
        name: str,
        action: Callable[[dict], Any],
        compensation: Callable[[dict], None]
    ) -> 'SagaOrchestrator':
        """Appends a new forward action and its matching rollback compensation."""
        self.steps.append(SagaStep(name, action, compensation))
        return self

    def execute(self, context: dict) -> bool:
        """Executes saga steps sequentially; rolls back completed steps on failure."""
        print(f"--- [SAGA START] Initiating Transaction: {self.name} ---")
        executed_steps: list[SagaStep] = []

        for step in self.steps:
            print(f"  [EXECUTE] Running Step: '{step.name}'...")
            try:
                step.action(context)
                step.status = SagaStepStatus.COMPLETED
                executed_steps.append(step)
            except Exception as err:
                print(f"  [FAILURE] Step '{step.name}' encountered an error: {err}")
                step.status = SagaStepStatus.FAILED
                self._compensate(executed_steps, context)
                return False

        print(f"--- [SAGA SUCCESS] Transaction '{self.name}' completed without faults ---\n")
        return True

    def _compensate(self, completed_steps: list[SagaStep], context: dict) -> None:
        """Rolls back all previously executed steps in reverse order (LIFO)."""
        print("\n  [ROLLBACK] Initiating compensating actions in reverse order...")
        for step in reversed(completed_steps):
            try:
                print(f"    <- [COMPENSATE] Reversing step: '{step.name}'...")
                step.compensation(context)
                step.status = SagaStepStatus.COMPENSATED
            except Exception as comp_err:
                # In real-world systems, compensation failures are pushed to a Dead Letter Queue (DLQ)
                print(f"    !! [CRITICAL] Compensation failed for '{step.name}': {comp_err}")
        print("--- [SAGA ABORTED] State restored to baseline consistency ---\n")


# --- Microservice Domain Simulation ---

def reserve_inventory(ctx: dict):
    if ctx.get("stock_empty"):
        raise ValueError("Insufficient inventory in warehouse")
    print("      -> Warehouse: 1 unit reserved.")

def release_inventory(ctx: dict):
    print("      <- Warehouse: Released reserved inventory.")

def process_payment(ctx: dict):
    if ctx.get("insufficient_funds"):
        raise ValueError("Payment gateway declined transaction (Insufficient Funds)")
    print("      -> Payment Gateway: $99.00 charged.")

def refund_payment(ctx: dict):
    print("      <- Payment Gateway: $99.00 refunded.")

def create_shipping_label(ctx: dict):
    if ctx.get("invalid_address"):
        raise ValueError("Invalid courier destination address")
    print("      -> Logistics: Waybill and tracking label generated.")

def cancel_shipping_label(ctx: dict):
    print("      <- Logistics: Waybill cancelled.")


if __name__ == "__main__":
    # Define Saga pipeline steps
    def build_checkout_saga() -> SagaOrchestrator:
        return (
            SagaOrchestrator("E-Commerce Order Checkout")
            .add_step("Reserve Inventory", reserve_inventory, release_inventory)
            .add_step("Process Payment", process_payment, refund_payment)
            .add_step("Create Shipping Label", create_shipping_label, cancel_shipping_label)
        )

    # Scenario 1: Successful end-to-end checkout
    order_context_success = {"user_id": 101, "item_id": 404}
    saga_1 = build_checkout_saga()
    saga_1.execute(order_context_success)

    # Scenario 2: Payment fails midway -> triggers automatic compensation
    order_context_failure = {"user_id": 102, "item_id": 404, "insufficient_funds": True}
    saga_2 = build_checkout_saga()
    saga_2.execute(order_context_failure)

# Output :
# --- [SAGA START] Initiating Transaction: E-Commerce Order Checkout ---
#   [EXECUTE] Running Step: 'Reserve Inventory'...
#       -> Warehouse: 1 unit reserved.
#   [EXECUTE] Running Step: 'Process Payment'...
#       -> Payment Gateway: $99.00 charged.
#   [EXECUTE] Running Step: 'Create Shipping Label'...
#       -> Logistics: Waybill and tracking label generated.
# --- [SAGA SUCCESS] Transaction 'E-Commerce Order Checkout' completed without faults ---

# --- [SAGA START] Initiating Transaction: E-Commerce Order Checkout ---
#   [EXECUTE] Running Step: 'Reserve Inventory'...
#       -> Warehouse: 1 unit reserved.
#   [EXECUTE] Running Step: 'Process Payment'...
#   [FAILURE] Step 'Process Payment' encountered an error: Payment gateway declined transaction (Insufficient Funds)

#   [ROLLBACK] Initiating compensating actions in reverse order...
#     <- [COMPENSATE] Reversing step: 'Reserve Inventory'...
#       <- Warehouse: Released reserved inventory.
# --- [SAGA ABORTED] State restored to baseline consistency ---
