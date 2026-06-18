class CharacterStyleFlyweight:
    """The Flyweight object containing immutable, shared 'Intrinsic' state."""
    def __init__(self, font_family: str, size: int, color: str):
        self.font_family = font_family
        self.size = size
        self.color = color
        # Simulating heavy resource allocation (e.g., loading texture maps)
        self.texture_byte_size = 1024 * 1024  # 1 MB placeholder

    def render(self, character: str, x: int, y: int) -> None:
        """Combines intrinsic state with incoming extrinsic state to execute action."""
        print(f"  Character '{character}' at ({x}, {y}) using style "
              f"[{self.font_family}, {self.size}pt, {self.color}] "
              f"(Shared Block: {hex(id(self))})")


class FlyweightFactory:
    """The Manager that instantiates and pools Flyweight objects safely."""
    def __init__(self):
        self._flyweights: dict[tuple[str, int, str], CharacterStyleFlyweight] = {}

    def get_flyweight(self, font_family: str, size: int, color: str) -> CharacterStyleFlyweight:
        # Create a unique lookup key based on the style attributes
        key = (font_family, size, color)
        
        # If the style doesn't exist yet, allocate it once
        if key not in self._flyweights:
            print(f"[FACTORY] Allocating NEW structural style block: {key}")
            self._flyweights[key] = CharacterStyleFlyweight(font_family, size, color)
            
        return self._flyweights[key]

    def total_flyweights_created(self) -> int:
        return len(self._flyweights)


if __name__ == "__main__":
    print("--- Initializing Flyweight Resource Engine ---")
    factory = FlyweightFactory()

    # Extrinsic dataset: Coordinates and letters for a word block
    # Intrinsic target: They all share the exact same font profile
    document_text = "HELLO"
    coordinates = [(0, 0), (10, 0), (20, 0), (30, 0), (40, 0)]
    
    # Fetching shared style references from the manager
    print("\n--- Processing Text Render Pass ---")
    for char, (pos_x, pos_y) in zip(document_text, coordinates):
        # Even though we loop 5 times, we only invoke the heavy constructor once!
        shared_style = factory.get_flyweight("Cascadia Code", 12, "Neon_Green")
        shared_style.render(char, pos_x, pos_y)

    print("-" * 55)
    print(f"[SUMMARY] Total characters displayed: {len(document_text)}")
    print(f"[SUMMARY] Total heavy memory style blocks created: {factory.total_flyweights_created()}")

# Output :
# --- Initializing Flyweight Resource Engine ---

# --- Processing Text Render Pass ---
# [FACTORY] Allocating NEW structural style block: ('Cascadia Code', 12, 'Neon_Green')
#   Character 'H' at (0, 0) using style [Cascadia Code, 12pt, Neon_Green] (Shared Block: 0x21923a83380)
#   Character 'E' at (10, 0) using style [Cascadia Code, 12pt, Neon_Green] (Shared Block: 0x21923a83380)
#   Character 'L' at (20, 0) using style [Cascadia Code, 12pt, Neon_Green] (Shared Block: 0x21923a83380)
#   Character 'L' at (30, 0) using style [Cascadia Code, 12pt, Neon_Green] (Shared Block: 0x21923a83380)
#   Character 'O' at (40, 0) using style [Cascadia Code, 12pt, Neon_Green] (Shared Block: 0x21923a83380)
# -------------------------------------------------------
# [SUMMARY] Total characters displayed: 5
# [SUMMARY] Total heavy memory style blocks created: 1
