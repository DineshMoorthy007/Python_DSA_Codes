import threading
import time

class WriterPreferenceRWLock:
    """A Read-Write Lock favoring waiting writers to prevent writer starvation.
    
    Allows simultaneous readers when no writer is active or queued,
    but blocks new readers if a writer is waiting to acquire the lock.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        
        self._active_readers = 0
        self._waiting_writers = 0
        self._active_writer = False

    def acquire_read(self) -> None:
        """Acquires a shared read lock. 
        
        Blocks if a writer is active OR if any writers are waiting in line.
        """
        with self._cond:
            # Writer Preference Rule: Block new readers if waiting_writers > 0
            while self._active_writer or self._waiting_writers > 0:
                self._cond.wait()
            self._active_readers += 1

    def release_read(self) -> None:
        """Releases a shared read lock and notifies waiting threads if last reader."""
        with self._cond:
            self._active_readers -= 1
            if self._active_readers == 0:
                # Wake up all waiting threads (specifically target waiting writers)
                self._cond.notify_all()

    def acquire_write(self) -> None:
        """Acquires an exclusive write lock.
        
        Blocks if any readers or another writer are currently active.
        """
        with self._cond:
            self._waiting_writers += 1
            try:
                # Block until zero active readers and zero active writers remain
                while self._active_readers > 0 or self._active_writer:
                    self._cond.wait()
                self._active_writer = True
            finally:
                self._waiting_writers -= 1

    def release_write(self) -> None:
        """Releases the exclusive write lock and wakes waiting readers/writers."""
        with self._cond:
            self._active_writer = False
            # Wake up all threads (waiting writers get priority in acquire_read)
            self._cond.notify_all()


# --- Concurrent Execution Simulation ---

shared_database: dict[str, str] = {"config_key": "v1.0.0"}
rw_lock = WriterPreferenceRWLock()

def reader_task(reader_id: int):
    rw_lock.acquire_read()
    try:
        val = shared_database["config_key"]
        print(f"  [READER {reader_id}] Shared Read Executing -> Value: '{val}'")
        time.sleep(0.05)  # Simulate read work
    finally:
        rw_lock.release_read()

def writer_task(writer_id: int, new_val: str):
    print(f"\n[WRITER {writer_id} QUEUED] Requesting exclusive write access...")
    rw_lock.acquire_write()
    try:
        print(f"  --> [WRITER {writer_id} ACTIVE] Mutating Shared Config to '{new_val}'...")
        time.sleep(0.1)  # Simulate write mutation
        shared_database["config_key"] = new_val
    finally:
        rw_lock.release_write()
        print(f"  <-- [WRITER {writer_id} RELEASED] Exclusive lock freed.\n")


if __name__ == "__main__":
    print("--- Initializing Writer-Preference RWLock Execution Pipeline ---\n")

    # Spin up 3 initial concurrent readers
    threads = []
    for i in range(1, 4):
        t = threading.Thread(target=reader_task, args=(i,))
        threads.append(t)
        t.start()

    time.sleep(0.01)  # Ensure initial readers grab the lock first

    # Spin up a writer while readers are executing
    writer_thread = threading.Thread(target=writer_task, args=(1, "v2.0.0"))
    threads.append(writer_thread)
    writer_thread.start()

    # Spin up late-arriving readers (Should be BLOCKED behind the waiting writer)
    for i in range(4, 7):
        t = threading.Thread(target=reader_task, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("-" * 65)
    print(f"[SUCCESS] Final System State Post-Concurrency: {shared_database}")

# Output :
# --- Initializing Writer-Preference RWLock Execution Pipeline ---

#   [READER 1] Shared Read Executing -> Value: 'v1.0.0'
#   [READER 2] Shared Read Executing -> Value: 'v1.0.0'
#   [READER 3] Shared Read Executing -> Value: 'v1.0.0'

# [WRITER 1 QUEUED] Requesting exclusive write access...
#   --> [WRITER 1 ACTIVE] Mutating Shared Config to 'v2.0.0'...
#   <-- [WRITER 1 RELEASED] Exclusive lock freed.
#   [READER 4] Shared Read Executing -> Value: 'v2.0.0'

#   [READER 5] Shared Read Executing -> Value: 'v2.0.0'  [READER 6] Shared Read Executing -> Value: 'v2.0.0'

# -----------------------------------------------------------------
# [SUCCESS] Final System State Post-Concurrency: {'config_key': 'v2.0.0'}
