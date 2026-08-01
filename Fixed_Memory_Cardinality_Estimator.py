import math
import mmh3

class HyperLogLog:
    """Estimates set cardinality using the HyperLogLog probabilistic algorithm.
    
    Provides logarithmic memory usage with an approximate error rate of 1.04 / sqrt(m).
    """
    def __init__(self, p: int = 10):
        if not (4 <= p <= 16):
            raise ValueError("Precision parameter 'p' must be between 4 and 16.")
            
        self.p = p
        self.m = 1 << p  # Number of register registers = 2^p
        self.registers = [0] * self.m
        
        # Alpha bias-correction constant based on register bucket count (m)
        if self.m == 16:
            self.alpha = 0.673
        elif self.m == 32:
            self.alpha = 0.697
        elif self.m == 64:
            self.alpha = 0.709
        else:
            self.alpha = 0.7213 / (1.0 + 1.079 / self.m)

    def _hash(self, item: str) -> int:
        """Generates a 64-bit MurmurHash3 integer."""
        # Force unsigned 64-bit integer bit representation
        return mmh3.hash64(item.encode('utf-8'))[0] & 0xFFFFFFFFFFFFFFFF

    def _rho(self, w: int, max_bits: int = 64) -> int:
        """Calculates the position of the first 1-bit (leading zeros + 1)."""
        if w == 0:
            return max_bits
        return (w & -w).bit_length()  # Position of lowest set bit

    def add(self, item: str) -> None:
        """Ingests an item into the HLL sketch."""
        x = self._hash(item)
        
        # Use top 'p' bits as the register index
        idx = x >> (64 - self.p)
        
        # Use remaining bits to count leading zeros
        w = x & ((1 << (64 - self.p)) - 1)
        rank = self._rho(w, 64 - self.p)
        
        # Keep maximum recorded leading-zero rank for this register
        self.registers[idx] = max(self.registers[idx], rank)

    def count(self) -> int:
        """Estimates total unique items ingested into the HLL sketch."""
        # Calculate harmonic mean across all register buckets
        indicator = sum(2.0 ** -reg for reg in self.registers)
        raw_estimate = (self.alpha * (self.m ** 2)) / indicator

        # Range Correction 1: Small cardinality correction (Linear Counting)
        if raw_estimate <= 2.5 * self.m:
            zero_registers = self.registers.count(0)
            if zero_registers != 0:
                return int(self.m * math.log(self.m / zero_registers))

        # Range Correction 2: Large cardinality correction for 64-bit hash boundary
        two_32 = 1 << 32
        if raw_estimate > (1.0 / 30.0) * two_32:
            return int(-two_32 * math.log(1.0 - (raw_estimate / two_32)))

        return int(raw_estimate)


if __name__ == "__main__":
    print("--- Initializing HyperLogLog Cardinality Engine ---\n")
    
    # Configure HLL with precision p=10 (1,024 register buckets)
    hll = HyperLogLog(p=10)
    
    actual_uniques = 50_000
    print(f"[INGESTION] Streaming {actual_uniques:,} unique telemetry items...")
    
    # Ingest distinct items (including duplicate hits)
    for i in range(actual_uniques):
        hll.add(f"user_session_{i}")
        # Intentionally inject duplicates to verify deduplication behavior
        if i % 3 == 0:
            hll.add(f"user_session_{i}")

    estimated_count = hll.count()
    error_margin = abs(estimated_count - actual_uniques) / actual_uniques * 100

    print("-" * 65)
    print(f"[RESULTS]")
    print(f"  Actual Unique Count    : {actual_uniques:,}")
    print(f"  Estimated Unique Count : {estimated_count:,}")
    print(f"  Estimation Error Rate  : {error_margin:.2f}%")
    print(f"  Memory Footprint       : ~{hll.m / 1024:.2f} KB ({hll.m} registers)")

# Output :
# --- Initializing HyperLogLog Cardinality Engine ---

# [INGESTION] Streaming 50,000 unique telemetry items...
# -----------------------------------------------------------------
# [RESULTS]
#   Actual Unique Count    : 50,000
#   Estimated Unique Count : 50,600
#   Estimation Error Rate  : 1.20%
#   Memory Footprint       : ~1.00 KB (1024 registers)
