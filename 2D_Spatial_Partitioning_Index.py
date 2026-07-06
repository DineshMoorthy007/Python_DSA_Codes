class Point:
    """Represents a 2D coordinate node in space."""
    def __init__(self, x: float, y: float, data: any = None):
        self.x = x
        self.y = y
        self.data = data  # Optional payload (e.g., vehicle ID, player entity)


class BoundingBox:
    """Defines a rectangular anchor region boundary."""
    def __init__(self, x: float, y: float, half_width: float, half_height: float):
        self.x = x  # Center X coordinate
        self.y = y  # Center Y coordinate
        self.half_width = half_width
        self.half_height = half_height

    def contains(self, point: Point) -> bool:
        """Checks if a point falls within the boundaries of this box."""
        return (self.x - self.half_width <= point.x <= self.x + self.half_width and
                self.y - self.half_height <= point.y <= self.y + self.half_height)

    def intersects(self, other: 'BoundingBox') -> bool:
        """Checks if another bounding region overlaps with this box."""
        return not (other.x - other.half_width > self.x + self.half_width or
                    other.x + other.half_width < self.x - self.half_width or
                    other.y - other.half_height > self.y + self.half_height or
                    other.y + other.half_height < self.y - self.half_height)


class Quadtree:
    """A spatial tree structure that partitions 2D space into four quadrants."""
    def __init__(self, boundary: BoundingBox, capacity: int = 4):
        self.boundary = boundary
        self.capacity = capacity  # Maximum points a single quadrant can hold before splitting
        self.points: list[Point] = []
        self.divided = False
        
        # Child sub-quadrants
        self.north_west: Quadtree | None = None
        self.north_east: Quadtree | None = None
        self.south_west: Quadtree | None = None
        self.south_east: Quadtree | None = None

    def _subdivide(self) -> None:
        """Splits the current region into four equal sub-quadrants."""
        x, y = self.boundary.x, self.boundary.y
        hw, hh = self.boundary.half_width / 2, self.boundary.half_height / 2

        self.north_west = Quadtree(BoundingBox(x - hw, y + hh, hw, hh), self.capacity)
        self.north_east = Quadtree(BoundingBox(x + hw, y + hh, hw, hh), self.capacity)
        self.south_west = Quadtree(BoundingBox(x - hw, y - hh, hw, hh), self.capacity)
        self.south_east = Quadtree(BoundingBox(x + hw, y - hh, hw, hh), self.capacity)
        self.divided = True

    def insert(self, point: Point) -> bool:
        """Inserts a point into the quadtree. Returns True if successful."""
        if not self.boundary.contains(point):
            return False  # Ignore points outside this node's region boundary

        # If there's room and it hasn't split yet, add the point directly
        if len(self.points) < self.capacity and not self.divided:
            self.points.append(point)
            return True

        # Otherwise, subdivide if we haven't already
        if not self.divided:
            self._subdivide()

        # Delegate the point to the correct sub-quadrant child
        if self.north_west.insert(point): return True
        if self.north_east.insert(point): return True
        if self.south_west.insert(point): return True
        if self.south_east.insert(point): return True

        return False

    def query_range(self, search_range: BoundingBox, found_points: list[Point] = None) -> list[Point]:
        """Finds all points falling within a specific search range box."""
        if found_points is None:
            found_points = []

        # If the search range does not overlap this quadrant, abort immediately
        if not self.boundary.intersects(search_range):
            return found_points

        # Check local points in this node
        for point in self.points:
            if search_range.contains(point):
                found_points.append(point)

        # If divided, pass the query down to all children
        if self.divided:
            self.north_west.query_range(search_range, found_points)
            self.north_east.query_range(search_range, found_points)
            self.south_west.query_range(search_range, found_points)
            self.south_east.query_range(search_range, found_points)

        return found_points


if __name__ == "__main__":
    print("--- Initializing Spatial Quadtree Partitioning Index ---")
    
    # 1. Create a global boundary tracking space from -100 to +100
    global_boundary = BoundingBox(x=0, y=0, half_width=100, half_height=100)
    spatial_index = Quadtree(global_boundary, capacity=2)

    # 2. Scatter target nodes across the map
    spatial_index.insert(Point(10, 10, "Vehicle_Alpha"))
    spatial_index.insert(Point(12, 15, "Vehicle_Beta"))
    spatial_index.insert(Point(15, 10, "Vehicle_Gamma"))  # This third insert forces a split!
    spatial_index.insert(Point(-50, -50, "Isolated_Server"))

    # 3. Query a localized radar window range
    radar_window = BoundingBox(x=12, y=12, half_width=5, half_height=5)
    matches = spatial_index.query_range(radar_window)
    
    print("-" * 60)
    print(f"[SUCCESS] Spatial Lookup Finished. Objects within radar window:")
    for match in matches:
        print(f"  Located: {match.data} at position ({match.x}, {match.y})")

# Output :
# --- Initializing Spatial Quadtree Partitioning Index ---
# ------------------------------------------------------------
# [SUCCESS] Spatial Lookup Finished. Objects within radar window:
#   Located: Vehicle_Alpha at position (10, 10)
#   Located: Vehicle_Beta at position (12, 15)
#   Located: Vehicle_Gamma at position (15, 10)
