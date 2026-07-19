from abc import ABC, abstractmethod
from typing import List

class TransactionCommand(ABC):
    """Abstract interface defining the contract for executable and reversible events."""
    @abstractmethod
    def execute(self) -> bool:
        """Runs the operation. Returns True if successful."""
        pass

    @abstractmethod
    def undo(self) -> None:
        """Reverses the exact mutations caused by this specific execution frame."""
        pass


class BankAccountReceiver:
    """The Receiver class. Holds the actual state and performs the low-level logic."""
    def __init__(self, account_holder: str, initial_balance: int):
        self.account_holder = account_holder
        self.balance = initial_balance

    def deposit(self, amount: int) -> None:
        self.balance += amount
        print(f"  [LEDGER] Account '{self.account_holder}': Deposited ${amount:,}. Balance: ${self.balance:,}")

    def withdraw(self, amount: int) -> bool:
        if self.balance >= amount:
            self.balance -= amount
            print(f"  [LEDGER] Account '{self.account_holder}': Withdrew ${amount:,}. Balance: ${self.balance:,}")
            return True
        print(f"  [LEDGER ALERT] Account '{self.account_holder}': Insufficient funds for withdrawal of ${amount:,}.")
        return False


# --- Concrete Reversible Command Objects ---

class DepositCommand(TransactionCommand):
    def __init__(self, account: BankAccountReceiver, amount: int):
        self.account = account
        self.amount = amount
        self._execution_status = False

    def execute(self) -> bool:
        self.account.deposit(self.amount)
        self._execution_status = True
        return True

    def undo(self) -> None:
        if self._execution_status:
            # Reversing a deposit requires subtracting the amount
            self.account.balance -= self.amount
            print(f"  [UNDO] Rolled back deposit of ${self.amount:,}. Balance: ${self.account.balance:,}")


class WithdrawCommand(TransactionCommand):
    def __init__(self, account: BankAccountReceiver, amount: int):
        self.account = account
        self.amount = amount
        self._execution_status = False

    def execute(self) -> bool:
        if self.account.withdraw(self.amount):
            self._execution_status = True
            return True
        return False

    def undo(self) -> None:
        if self._execution_status:
            # Reversing a withdrawal requires adding the amount back
            self.account.deposit(self.amount)
            print(f"  [UNDO] Rolled back withdrawal of ${self.amount:,}. Balance: ${self.account.balance:,}")


class TransactionInvoker:
    """The Invoker class. Coordinates command execution loops and tracks history."""
    def __init__(self):
        self._history_stack: List[TransactionCommand] = []

    def execute_transaction(self, command: TransactionCommand) -> None:
        print(f"[INVOKER] Attempting to process transaction frame...")
        if command.execute():
            # If execution passes validation, cache it in the undo history stack
            self._history_stack.append(command)
        print("-" * 65)

    def trigger_rollback(self) -> None:
        """Pops the last successful operation out of history and undoes it."""
        if not self._history_stack:
            print("[INVOKER ALERT] Rollback aborted: History stack is entirely clear.")
            return

        command = self._history_stack.pop()
        print(f"[INVOKER] Rolling back last transaction step...")
        command.undo()
        print("-" * 65)


if __name__ == "__main__":
    print("--- Initializing Encapsulated Transaction Processing Suite ---\n")
    
    # 1. Spin up our target data structures (Receivers)
    checking_account = BankAccountReceiver(account_holder="Alice Dev", initial_balance=500)
    
    # 2. Spin up our pipeline controller (Invoker)
    atm_invoker = TransactionInvoker()

    # 3. Create and execute discrete command structures
    tx1 = DepositCommand(checking_account, 1000)
    atm_invoker.execute_transaction(tx1)

    tx2 = WithdrawCommand(checking_account, 300)
    atm_invoker.execute_transaction(tx2)

    # 4. Try an invalid transaction (Will fail validation and won't hit history stack)
    tx3 = WithdrawCommand(checking_account, 5000)
    atm_invoker.execute_transaction(tx3)

    # 5. Reverse operations cleanly
    atm_invoker.trigger_rollback()  # Undoes the $300 withdrawal
    atm_invoker.trigger_rollback()  # Undoes the $1,000 deposit

# Output :
# --- Initializing Encapsulated Transaction Processing Suite ---

# [INVOKER] Attempting to process transaction frame...
#   [LEDGER] Account 'Alice Dev': Deposited $1,000. Balance: $1,500
# -----------------------------------------------------------------
# [INVOKER] Attempting to process transaction frame...
#   [LEDGER] Account 'Alice Dev': Withdrew $300. Balance: $1,200
# -----------------------------------------------------------------
# [INVOKER] Attempting to process transaction frame...
#   [LEDGER ALERT] Account 'Alice Dev': Insufficient funds for withdrawal of $5,000.
# -----------------------------------------------------------------
# [INVOKER] Rolling back last transaction step...
#   [LEDGER] Account 'Alice Dev': Deposited $300. Balance: $1,500
#   [UNDO] Rolled back withdrawal of $300. Balance: $1,500
# -----------------------------------------------------------------
# [INVOKER] Rolling back last transaction step...
#   [UNDO] Rolled back deposit of $1,000. Balance: $500
# -----------------------------------------------------------------
