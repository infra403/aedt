"""DAG (Directed Acyclic Graph) data structure for dependency management."""
from typing import Any, Dict, List, Set


class DAG:
    """Directed Acyclic Graph for managing dependencies between nodes."""

    def __init__(self):
        """Initialize an empty DAG."""
        self.nodes: Dict[str, Any] = {}  # Node ID → Node (Epic or Story)
        self.edges: Dict[str, List[str]] = {}  # Node ID → List of dependency IDs
        self.reverse_edges: Dict[str, List[str]] = {}  # Node ID → List of dependent IDs

    def add_node(self, node_id: str, node: Any) -> None:
        """
        Add a node to the DAG.

        Args:
            node_id: Unique identifier for the node
            node: The node object (Epic or Story)
        """
        self.nodes[node_id] = node
        if node_id not in self.edges:
            self.edges[node_id] = []
        if node_id not in self.reverse_edges:
            self.reverse_edges[node_id] = []

    def add_edge(self, from_id: str, to_id: str) -> None:
        """
        Add an edge: from_id depends on to_id.

        Args:
            from_id: ID of the node that has the dependency
            to_id: ID of the node that is depended upon
        """
        if from_id not in self.edges:
            self.edges[from_id] = []
        self.edges[from_id].append(to_id)

        if to_id not in self.reverse_edges:
            self.reverse_edges[to_id] = []
        self.reverse_edges[to_id].append(from_id)

    def has_cycle(self) -> bool:
        """
        Check if the DAG contains a cycle using DFS.

        Returns:
            True if a cycle is detected, False otherwise
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for dep_id in self.edges.get(node_id, []):
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True  # Cycle detected

            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        return False

    def find_cycle(self) -> List[str]:
        """
        Find and return the cycle path if one exists.

        Returns:
            List of node IDs forming the cycle, empty if no cycle
        """
        visited: Set[str] = set()
        rec_stack: List[str] = []
        cycle_path: List[str] = []

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.append(node_id)

            for dep_id in self.edges.get(node_id, []):
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    # Found cycle, extract the cycle path
                    cycle_start_index = rec_stack.index(dep_id)
                    cycle_path.extend(rec_stack[cycle_start_index:])
                    cycle_path.append(dep_id)  # Complete the cycle
                    return True

            rec_stack.pop()
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return cycle_path

        return []

    def topological_sort(self) -> List[Any]:
        """
        Perform topological sort using Kahn's algorithm.

        Returns:
            List of nodes in topological order (nodes with no dependencies first)

        Raises:
            ValueError: If the graph contains a cycle
        """
        if self.has_cycle():
            raise ValueError("Cannot perform topological sort on a graph with cycles")

        # Calculate in-degree: number of dependencies each node has
        in_degree = {node_id: len(self.edges.get(node_id, [])) for node_id in self.nodes}

        # Queue nodes with in-degree 0 (no dependencies)
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(self.nodes[node_id])

            # For each node that depends on this node, reduce its in-degree
            for dependent_id in self.reverse_edges.get(node_id, []):
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        return result

    def get_parallel_nodes(self, completed_ids: Set[str]) -> List[Any]:
        """
        Get all nodes whose dependencies are satisfied.

        Args:
            completed_ids: Set of completed node IDs

        Returns:
            List of nodes that can be executed in parallel
        """
        parallel = []
        for node_id, node in self.nodes.items():
            if node_id in completed_ids:
                continue  # Already completed

            # Check if all dependencies are completed
            deps = self.edges.get(node_id, [])
            if all(dep_id in completed_ids for dep_id in deps):
                parallel.append(node)

        return parallel

    def get_node_count(self) -> int:
        """Get the number of nodes in the DAG."""
        return len(self.nodes)

    def get_edge_count(self) -> int:
        """Get the total number of edges in the DAG."""
        return sum(len(deps) for deps in self.edges.values())
