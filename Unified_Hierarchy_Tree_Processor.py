from abc import ABC, abstractmethod

class CorporateComponent(ABC):
    """Abstract interface defining the blueprint for both leaf items and composites."""
    
    @abstractmethod
    def get_budget(self) -> int:
        """Returns the cost footprint of this component segment."""
        pass

    @abstractmethod
    def display(self, depth: int = 0) -> None:
        """Renders the structural hierarchy layout to the console."""
        pass


class Employee(CorporateComponent):
    """The Leaf object. It has no sub-children and executes the base work."""
    def __init__(self, name: str, salary: int):
        self.name = name
        self.salary = salary

    def get_budget(self) -> int:
        return self.salary

    def display(self, depth: int = 0) -> None:
        indent = "  " * depth
        print(f"{indent}- {self.name} (Salary: ${self.salary:,})")


class Department(CorporateComponent):
    """The Composite object. It holds children sub-components and delegates tasks."""
    def __init__(self, department_name: str):
        self.department_name = department_name
        self._children: list[CorporateComponent] = []

    def add(self, component: CorporateComponent) -> None:
        """Hooks a new leaf or composite component into this branch level."""
        self._children.append(component)

    def remove(self, component: CorporateComponent) -> None:
        """Removes a component from this branch level."""
        self._children.remove(component)

    def get_budget(self) -> int:
        # The core trick: Recursively sum up budgets across all child components
        total_budget = sum(child.get_budget() for child in self._children)
        return total_budget

    def display(self, depth: int = 0) -> None:
        indent = "  " * depth
        print(f"{indent}[Department: {self.department_name}]")
        for child in self._children:
            # Delegate rendering down to the next structural level
            child.display(depth + 1)


if __name__ == "__main__":
    print("--- Initializing Corporate Structure Composite Engine ---\n")
    
    # 1. Spin up individual Leaf nodes (Employees)
    dev1 = Employee("Alice Lin", 120000)
    dev2 = Employee("Bob Chen", 110000)
    designer = Employee("Sarah Smith", 95000)
    cfo = Employee("Marcus Vance", 250000)

    # 2. Build sub-composite branches (Departments)
    engineering_dept = Department("Engineering")
    design_dept = Department("UX/UI Design")
    hq_branch = Department("Global Headquarters")

    # 3. Stitch the structural hierarchy tree together
    engineering_dept.add(dev1)
    engineering_dept.add(dev2)
    
    design_dept.add(designer)
    
    # Nested composite: Adding sub-departments into a parent corporate branch
    hq_branch.add(cfo)
    hq_branch.add(engineering_dept)
    hq_branch.add(design_dept)

    # 4. Uniform Execution: Treat single nodes and composite blocks identically
    print("[EXECUTION 1] Isolated Branch Display:")
    engineering_dept.display()
    print(f"Engineering Total Budget: ${engineering_dept.get_budget():,}\n")
    
    print("-" * 60)
    
    print("[EXECUTION 2] Global Tree Roll-up Display:")
    hq_branch.display()
    print(f"\nTotal Corporate Burn Rate Budget: ${hq_branch.get_budget():,}")

# Output :
# --- Initializing Corporate Structure Composite Engine ---

# [EXECUTION 1] Isolated Branch Display:
# [Department: Engineering]
#   - Alice Lin (Salary: $120,000)
#   - Bob Chen (Salary: $110,000)
# Engineering Total Budget: $230,000

# ------------------------------------------------------------
# [EXECUTION 2] Global Tree Roll-up Display:
# [Department: Global Headquarters]
#   - Marcus Vance (Salary: $250,000)
#   [Department: Engineering]
#     - Alice Lin (Salary: $120,000)
#     - Bob Chen (Salary: $110,000)
#   [Department: UX/UI Design]
#     - Sarah Smith (Salary: $95,000)

# Total Corporate Burn Rate Budget: $575,000
