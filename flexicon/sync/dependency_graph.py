"""
Dependency Graph - Phase 3.1

Models object dependencies as a directed acyclic graph (DAG) and provides
topological sorting for correct import order.

Author: FlexTools Development Team
Date: 2025-11-27
"""

import logging
from typing import Any, List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """Types of dependencies between objects."""

    OWNERSHIP = "ownership"  # Parent owns child (must import parent first)
    REFERENCE = "reference"  # Object references another (should exist)
    CROSS_REFERENCE = "cross_ref"  # Bidirectional reference


@dataclass
class DependencyNode:
    """
    Node in dependency graph representing a FLEx object.
    """

    guid: str
    object_type: str
    obj: Any = None  # Actual FLEx object
    dependencies: Set[str] = field(default_factory=set)  # GUIDs this depends on
    dependents: Set[str] = field(default_factory=set)  # GUIDs that depend on this
    dependency_types: Dict[str, DependencyType] = field(default_factory=dict)  # guid → type
    visited: bool = False  # For graph traversal
    in_progress: bool = False  # For cycle detection


class DependencyGraph:
    """
    Directed acyclic graph (DAG) of object dependencies.

    Manages dependencies between FLEx objects and provides topological
    sorting to determine correct import order.
    """

    def __init__(self):
        """Initialize empty dependency graph."""
        self.nodes: Dict[str, DependencyNode] = {}
        self._import_order: Optional[List[Tuple[str, str]]] = None  # Cached import order

    def add_object(self, guid: str, object_type: str, obj: Any = None):
        """
        Add object to graph.

        Args:
            guid: Object GUID
            object_type: Type of object (e.g., "LexEntry", "LexSense")
            obj: Actual FLEx object (optional)
        """
        if guid not in self.nodes:
            self.nodes[guid] = DependencyNode(guid=guid, object_type=object_type, obj=obj)
            self._import_order = None  # Invalidate cache
        else:
            # Update existing node
            if obj is not None:
                self.nodes[guid].obj = obj
            self.nodes[guid].object_type = object_type

    def add_dependency(self, from_guid: str, to_guid: str, dep_type: DependencyType = DependencyType.REFERENCE):
        """
        Add dependency: from_guid depends on to_guid.

        This means to_guid must be imported before from_guid.

        Args:
            from_guid: Object that depends on another
            to_guid: Object that is depended upon
            dep_type: Type of dependency
        """
        # Ensure both nodes exist
        if from_guid not in self.nodes:
            logger.warning(f"Adding dependency for unknown object {from_guid}")
            self.add_object(from_guid, "Unknown")

        if to_guid not in self.nodes:
            logger.warning(f"Adding dependency on unknown object {to_guid}")
            self.add_object(to_guid, "Unknown")

        # Add dependency
        self.nodes[from_guid].dependencies.add(to_guid)
        self.nodes[from_guid].dependency_types[to_guid] = dep_type

        # Add reverse (dependent) relationship
        self.nodes[to_guid].dependents.add(from_guid)

        # Invalidate cached import order
        self._import_order = None

    def remove_dependency(self, from_guid: str, to_guid: str):
        """
        Remove dependency between objects.

        Used for breaking cycles or handling optional dependencies.

        Args:
            from_guid: Object that depends on another
            to_guid: Object that is depended upon
        """
        if from_guid in self.nodes:
            self.nodes[from_guid].dependencies.discard(to_guid)
            if to_guid in self.nodes[from_guid].dependency_types:
                del self.nodes[from_guid].dependency_types[to_guid]

        if to_guid in self.nodes:
            self.nodes[to_guid].dependents.discard(from_guid)

        self._import_order = None

    def get_import_order(self) -> List[Tuple[str, str]]:
        """
        Get topologically sorted import order.

        Returns list of (guid, object_type) tuples in order they should
        be imported (dependencies first).

        Returns:
            List of (guid, object_type) tuples

        Raises:
            CircularDependencyError: If circular dependency detected
        """
        if self._import_order is not None:
            return self._import_order

        # Check for cycles first
        cycles = self.detect_cycles()
        if cycles:
            raise CircularDependencyError(cycles[0])

        # Perform topological sort using Kahn's algorithm
        # Calculate in-degree for each node
        in_degree = {guid: len(node.dependencies) for guid, node in self.nodes.items()}

        # Queue of nodes with no dependencies
        queue = [guid for guid, degree in in_degree.items() if degree == 0]

        result = []

        while queue:
            # Sort queue to ensure deterministic order
            queue.sort()

            # Process node with no remaining dependencies
            guid = queue.pop(0)
            node = self.nodes[guid]
            result.append((guid, node.object_type))

            # Reduce in-degree for dependent nodes
            for dependent_guid in node.dependents:
                in_degree[dependent_guid] -= 1
                if in_degree[dependent_guid] == 0:
                    queue.append(dependent_guid)

        # Cache result
        self._import_order = result
        return result

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies using depth-first search.

        Returns:
            List of cycles found, each cycle is a list of GUIDs
        """
        cycles = []

        # Reset visited flags
        for node in self.nodes.values():
            node.visited = False
            node.in_progress = False

        def dfs(guid: str, path: List[str]):
            """Depth-first search to detect cycles."""
            node = self.nodes[guid]

            if node.in_progress:
                # Found cycle - extract it from path
                cycle_start = path.index(guid)
                cycle = path[cycle_start:] + [guid]
                cycles.append(cycle)
                return

            if node.visited:
                return

            node.in_progress = True
            path.append(guid)

            for dep_guid in node.dependencies:
                if dep_guid in self.nodes:
                    dfs(dep_guid, path[:])

            path.pop()
            node.in_progress = False
            node.visited = True

        # Check from each node
        for guid in self.nodes:
            if not self.nodes[guid].visited:
                dfs(guid, [])

        return cycles

    def get_roots(self) -> List[str]:
        """
        Get root nodes (objects with no dependencies).

        Returns:
            List of GUIDs with no dependencies
        """
        return [guid for guid, node in self.nodes.items() if not node.dependencies]

    def get_leaves(self) -> List[str]:
        """
        Get leaf nodes (objects that nothing depends on).

        Returns:
            List of GUIDs with no dependents
        """
        return [guid for guid, node in self.nodes.items() if not node.dependents]

    def get_dependencies(self, guid: str, recursive: bool = False) -> List[str]:
        """
        Get all dependencies for an object.

        Args:
            guid: Object GUID
            recursive: If True, get transitive dependencies

        Returns:
            List of GUIDs this object depends on
        """
        if guid not in self.nodes:
            return []

        if not recursive:
            return list(self.nodes[guid].dependencies)

        # Get transitive dependencies
        visited = set()
        queue = [guid]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            if current in self.nodes:
                for dep in self.nodes[current].dependencies:
                    if dep not in visited:
                        queue.append(dep)

        visited.discard(guid)  # Remove self
        return list(visited)

    def get_dependents(self, guid: str, recursive: bool = False) -> List[str]:
        """
        Get all objects that depend on this object.

        Args:
            guid: Object GUID
            recursive: If True, get transitive dependents

        Returns:
            List of GUIDs that depend on this object
        """
        if guid not in self.nodes:
            return []

        if not recursive:
            return list(self.nodes[guid].dependents)

        # Get transitive dependents
        visited = set()
        queue = [guid]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            if current in self.nodes:
                for dep in self.nodes[current].dependents:
                    if dep not in visited:
                        queue.append(dep)

        visited.discard(guid)  # Remove self
        return list(visited)

    def get_subgraph(self, guids: List[str]) -> "DependencyGraph":
        """
        Extract subgraph containing only specified objects and their dependencies.

        Args:
            guids: List of GUIDs to include

        Returns:
            New DependencyGraph with only specified objects
        """
        subgraph = DependencyGraph()

        # Collect all objects and their transitive dependencies
        all_guids = set()
        for guid in guids:
            all_guids.add(guid)
            all_guids.update(self.get_dependencies(guid, recursive=True))

        # Add objects to subgraph
        for guid in all_guids:
            if guid in self.nodes:
                node = self.nodes[guid]
                subgraph.add_object(guid, node.object_type, node.obj)

        # Add dependencies
        for guid in all_guids:
            if guid in self.nodes:
                node = self.nodes[guid]
                for dep_guid in node.dependencies:
                    if dep_guid in all_guids:
                        dep_type = node.dependency_types.get(dep_guid, DependencyType.REFERENCE)
                        subgraph.add_dependency(guid, dep_guid, dep_type)

        return subgraph

    def summary(self) -> str:
        """
        Get summary of dependency graph.

        Returns:
            Human-readable summary string
        """
        lines = [
            "DEPENDENCY GRAPH SUMMARY",
            "=" * 40,
            f"Total objects: {len(self.nodes)}",
            f"Root objects: {len(self.get_roots())}",
            f"Leaf objects: {len(self.get_leaves())}",
            "",
        ]

        # Count by object type
        type_counts: Dict[str, int] = {}
        for node in self.nodes.values():
            type_counts[node.object_type] = type_counts.get(node.object_type, 0) + 1

        lines.append("Objects by type:")
        for obj_type, count in sorted(type_counts.items()):
            lines.append(f"  {obj_type}: {count}")

        # Count by dependency type
        dep_type_counts: Dict[DependencyType, int] = {}
        for node in self.nodes.values():
            for dep_type in node.dependency_types.values():
                dep_type_counts[dep_type] = dep_type_counts.get(dep_type, 0) + 1

        if dep_type_counts:
            lines.append("")
            lines.append("Dependencies by type:")
            for dep_type, count in sorted(dep_type_counts.items(), key=lambda x: x[0].value):
                lines.append(f"  {dep_type.value}: {count}")

        return "\n".join(lines)

    def __len__(self) -> int:
        """Return number of objects in graph."""
        return len(self.nodes)

    def __contains__(self, guid: str) -> bool:
        """Check if GUID is in graph."""
        return guid in self.nodes


class CircularDependencyError(Exception):
    """Raised when circular dependency is detected."""

    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        cycle_str = " → ".join(cycle)
        super().__init__(f"Circular dependency detected: {cycle_str}")
