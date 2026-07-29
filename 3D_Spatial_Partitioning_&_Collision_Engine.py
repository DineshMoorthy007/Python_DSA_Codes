class Point3D:
    """Represents a coordinate point in 3D space."""
    def __init__(self, x: float, y: float, z: float, data: str = ""):
        self.x = x
        self.y = y
        self.z = z
        self.data = data

    def __repr__(self):
        return f"Point({self.x}, {self.y}, {self.z})"


class BoundingBox3D:
    """Defines a 3D axis-aligned bounding box (AABB)."""
    def __init__(self, center_x: float, center_y: float, center_z: float, half_size: float):
        self.cx = center_x
        self.cy = center_y
        self.cz = center_z
        self.half = half_size  # Half-width distance from center to boundaries

    def contains(self, point: Point3D) -> bool:
        """Checks if a 3D point lies strictly within this bounding box."""
        return (self.cx - self.half <= point.x <= self.cx + self.half and
                self.cy - self.half <= point.y <= self.cy + self.half and
                self.cz - self.half <= point.z <= self.cz + self.half)

    def intersects(self, other: 'BoundingBox3D') -> bool:
        """Checks if another 3D bounding box overlaps with this box."""
        return not (other.cx - other.half > self.cx + self.half or
                    other.cx + other.half < self.cx - self.half or
                    other.cy - other.half > self.cy + self.half or
                    other.cy + other.half < self.cy - self.half or
                    other.cz - other.half > self.cz + self.half or
                    other.cz + other.half < self.cz - self.half)


class OctreeNode:
    """A single node inside the Octree partitioning space into 8 sub-octants."""
    def __init__(self, boundary: BoundingBox3D, capacity: int = 4):
        self.boundary = boundary
        self.capacity = capacity
        self.points: list[Point3D] = []
        self.divided = False
        
        # Array holding references to the 8 child octant nodes
        self.children: list[OctreeNode | None] = [None] * 8

    def _subdivide(self) -> None:
        """Splits the current 3D region into 8 child octants."""
        cx, cy, cz = self.boundary.cx, self.boundary.cy, self.boundary.cz
        quarter = self.boundary.half / 2.0

        # Offsets defining the 8 sub-cube centers (+/- x, +/- y, +/- z)
        offsets = [
            (-1, -1, -1), (1, -1, -1), (-1, 1, -1), (1, 1, -1),
            (-1, -1,  1), (1, -1,  1), (-1, 1,  1), (1, 1,  1)
        ]

        for i, (ox, oy, oz) in enumerate(offsets):
            sub_box = BoundingBox3D(cx + ox * quarter, cy + oy * quarter, cz + oz * quarter, quarter)
            self.children[i] = OctreeNode(sub_box, self.capacity)

        self.divided = True

    def insert(self, point: Point3D) -> bool:
        """Inserts a 3D point into the Octree, subdividing if capacity is breached."""
        if not self.boundary.contains(point):
            return False  # Point is outside this spatial region

        if len(self.points) < self.capacity and not self.divided:
            self.points.append(point)
            return True

        if not self.divided:
            self._subdivide()
            # Push pre-existing points down to child octants
            existing_points = self.points
            self.points = []
            for p in existing_points:
                for child in self.children:
                    if child.insert(p):
                        break

        # Delegate point insertion to the appropriate child octant
        for child in self.children:
            if child.insert(point):
                return True

        return False

    def query_range(self, range_box: BoundingBox3D, found_points: list[Point3D]) -> None:
        """Gathers all 3D points that reside within a target search box."""
        if not self.boundary.intersects(range_box):
            return  # Spatial region does not overlap target search zone

        # Check points stored at this node level
        for p in self.points:
            if range_box.contains(p):
                found_points.append(p)

        # Recurse down child octants if subdivided
        if self.divided:
            for child in self.children:
                child.query_range(range_box, found_points)


if __name__ == "__main__":
    print("--- Initializing 3D Spatial Octree Engine ---\n")

    # Define root bounding box centered at (0, 0, 0) extending +/- 50 units
    world_bounds = BoundingBox3D(center_x=0.0, center_y=0.0, center_z=0.0, half_size=50.0)
    octree = OctreeNode(boundary=world_bounds, capacity=2)

    # Insert 3D entities into the world space
    entities = [
        Point3D(10, 12, -5, "Player"),
        Point3D(11, 15, -4, "Enemy_1"),
        Point3D(-35, 20, 40, "NPC_Vendor"),
        Point3D(12, 10, -6, "Item_Drop"),
        Point3D(45, -45, -45, "World_Boundary_Marker")
    ]

    for entity in entities:
        octree.insert(entity)

    # Perform a spatial range query around the Player (x: 10, y: 12, z: -5)
    search_zone = BoundingBox3D(center_x=10.0, center_y=12.0, center_z=-5.0, half_size=5.0)
    nearby_entities = []
    octree.query_range(search_zone, nearby_entities)

    print(f"[SPATIAL SEARCH] Querying entities around range box at (10, 12, -5)...")
    print("-" * 65)
    print(f"[SUCCESS] Nearby Entities Located: {len(nearby_entities)}")
    for obj in nearby_entities:
        print(f"  Found Entity: '{obj.data}' at Coordinates ({obj.x}, {obj.y}, {obj.z})")
