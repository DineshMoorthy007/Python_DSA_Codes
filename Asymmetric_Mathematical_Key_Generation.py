import random

class DiffieHellmanNode:
    """Represents a single participant in the secure key exchange network."""
    def __init__(self, name: str, shared_prime: int, shared_base: int):
        self.name = name
        self.prime = shared_prime
        self.base = shared_base
        
        # Generate a secure, completely secret private key known only to this instance
        self.__private_key = random.randint(2, shared_prime - 2)

    def generate_public_key(self) -> int:
        """Calculates the public key payload to send over the insecure network.
        
        Formula: Public = (base ^ private_key) % prime
        """
        # Utilizing Python's pow(base, exp, mod) for optimized O(log exp) runtime
        return pow(self.base, self.__private_key, self.prime)

    def compute_shared_secret(self, incoming_public_key: int) -> int:
        """Computes the final matching secret key using the other party's public key.
        
        Formula: Secret = (incoming_public ^ private_key) % prime
        """
        return pow(incoming_public_key, self.__private_key, self.prime)


if __name__ == "__main__":
    print("--- Initializing Diffie-Hellman Cryptographic Engine ---")
    
    # 1. Publicly agreed-upon parameters (A large prime and its primitive root base)
    # In production, these parameters use massive 2048-bit numbers
    public_prime = 23
    public_base = 5
    
    print(f"Public Parameters -> Shared Prime (p): {public_prime} | Shared Base (g): {public_base}")
    print("-" * 65)

    # 2. Instantiate two completely independent communication nodes
    alice = DiffieHellmanNode("Alice", public_prime, public_base)
    bob = DiffieHellmanNode("Bob", public_prime, public_base)

    # 3. Exchange step: Generate and exchange public key fingerprints publicly
    alice_public = alice.generate_public_key()
    bob_public = bob.generate_public_key()

    print(f"[PUBLIC NETWORK] Alice transmits Public Key: {alice_public}")
    print(f"[PUBLIC NETWORK] Bob transmits Public Key:   {bob_public}")
    print("-" * 65)

    # 4. Derivation step: Process keys locally using secret internal private values
    alice_secret = alice.compute_shared_secret(bob_public)
    bob_secret = bob.compute_shared_secret(alice_public)

    print(f"[LOCAL COMPUTE] Alice's Derived Symmetric Secret: {alice_secret}")
    print(f"[LOCAL COMPUTE] Bob's Derived Symmetric Secret:   {bob_secret}")
    
    # Assert validation check
    if alice_secret == bob_secret:
        print("\n[SUCCESS] Shared symmetric keys match perfectly! Secure channel established.")
