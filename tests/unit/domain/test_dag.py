"""Unit tests for DAG data structure."""
import pytest

from aedt.domain.models.dag import DAG


class TestDAGInit:
    """Test DAG initialization."""

    def test_init_creates_empty_dag(self):
        """Test that __init__ creates empty structures."""
        dag = DAG()
        assert dag.nodes == {}
        assert dag.edges == {}
        assert dag.reverse_edges == {}


class TestDAGAddNode:
    """Test add_node method."""

    def test_add_node_single(self):
        """Test adding a single node."""
        dag = DAG()
        dag.add_node("1", {"id": "1", "name": "Epic 1"})

        assert "1" in dag.nodes
        assert dag.nodes["1"] == {"id": "1", "name": "Epic 1"}
        assert dag.edges["1"] == []
        assert dag.reverse_edges["1"] == []

    def test_add_multiple_nodes(self):
        """Test adding multiple nodes."""
        dag = DAG()
        dag.add_node("1", {"id": "1"})
        dag.add_node("2", {"id": "2"})
        dag.add_node("3", {"id": "3"})

        assert len(dag.nodes) == 3
        assert all(node_id in dag.nodes for node_id in ["1", "2", "3"])


class TestDAGAddEdge:
    """Test add_edge method."""

    def test_add_edge_single(self):
        """Test adding a single edge."""
        dag = DAG()
        dag.add_node("1", {"id": "1"})
        dag.add_node("2", {"id": "2"})
        dag.add_edge("2", "1")  # 2 depends on 1

        assert "1" in dag.edges["2"]
        assert "2" in dag.reverse_edges["1"]

    def test_add_multiple_edges_from_same_node(self):
        """Test adding multiple dependencies from one node."""
        dag = DAG()
        for i in range(1, 5):
            dag.add_node(str(i), {"id": str(i)})

        dag.add_edge("4", "1")  # 4 depends on 1
        dag.add_edge("4", "2")  # 4 depends on 2
        dag.add_edge("4", "3")  # 4 depends on 3

        assert len(dag.edges["4"]) == 3
        assert all(dep_id in dag.edges["4"] for dep_id in ["1", "2", "3"])


class TestHasCycle:
    """Test has_cycle method."""

    def test_no_cycle_linear_chain(self):
        """Test linear dependency chain has no cycle."""
        dag = DAG()
        dag.add_node("1", {"id": "1"})
        dag.add_node("2", {"id": "2"})
        dag.add_node("3", {"id": "3"})
        dag.add_edge("2", "1")  # 2 → 1
        dag.add_edge("3", "2")  # 3 → 2

        assert dag.has_cycle() is False

    def test_no_cycle_parallel_dependencies(self):
        """Test parallel dependencies have no cycle."""
        dag = DAG()
        for i in range(1, 5):
            dag.add_node(str(i), {"id": str(i)})

        dag.add_edge("2", "1")  # 2 → 1
        dag.add_edge("3", "1")  # 3 → 1
        dag.add_edge("4", "2")  # 4 → 2
        dag.add_edge("4", "3")  # 4 → 3

        assert dag.has_cycle() is False

    def test_cycle_simple(self):
        """Test simple cycle detection: 2 → 3 → 2."""
        dag = DAG()
        dag.add_node("1", {"id": "1"})
        dag.add_node("2", {"id": "2"})
        dag.add_node("3", {"id": "3"})
        dag.add_edge("2", "3")  # 2 → 3
        dag.add_edge("3", "2")  # 3 → 2 (cycle!)

        assert dag.has_cycle() is True

    def test_cycle_self_reference(self):
        """Test self-referencing cycle: 1 → 1."""
        dag = DAG()
        dag.add_node("1", {"id": "1"})
        dag.add_edge("1", "1")  # 1 → 1 (self cycle)

        assert dag.has_cycle() is True

    def test_cycle_complex(self):
        """Test complex cycle: 1 → 2 → 3 → 4 → 2."""
        dag = DAG()
        for i in range(1, 5):
            dag.add_node(str(i), {"id": str(i)})

        dag.add_edge("2", "1")  # 2 → 1
        dag.add_edge("3", "2")  # 3 → 2
        dag.add_edge("4", "3")  # 4 → 3
        dag.add_edge("2", "4")  # 2 → 4 (cycle: 2→4→3→2)

        assert dag.has_cycle() is True


class TestFindCycle:
    """Test find_cycle method."""

    def test_find_cycle_returns_empty_when_no_cycle(self):
        """Test find_cycle returns empty list when no cycle."""
        dag = DAG()
        dag.add_node("1", {"id": "1"})
        dag.add_node("2", {"id": "2"})
        dag.add_edge("2", "1")

        cycle = dag.find_cycle()
        assert cycle == []

    def test_find_cycle_simple(self):
        """Test find_cycle identifies simple cycle."""
        dag = DAG()
        dag.add_node("2", {"id": "2"})
        dag.add_node("3", {"id": "3"})
        dag.add_edge("2", "3")  # 2 → 3
        dag.add_edge("3", "2")  # 3 → 2

        cycle = dag.find_cycle()
        # Cycle should contain both nodes
        assert len(cycle) > 0
        assert "2" in cycle and "3" in cycle


class TestTopologicalSort:
    """Test topological_sort method."""

    def test_topological_sort_linear(self):
        """Test topological sort on linear chain."""
        dag = DAG()
        dag.add_node("1", {"id": "1", "name": "Epic 1"})
        dag.add_node("2", {"id": "2", "name": "Epic 2"})
        dag.add_node("3", {"id": "3", "name": "Epic 3"})
        dag.add_edge("2", "1")  # 2 depends on 1
        dag.add_edge("3", "2")  # 3 depends on 2

        result = dag.topological_sort()

        # Result should be in order: 1, 2, 3
        assert len(result) == 3
        ids = [node["id"] for node in result]
        assert ids.index("1") < ids.index("2")
        assert ids.index("2") < ids.index("3")

    def test_topological_sort_parallel(self):
        """Test topological sort with parallel dependencies."""
        dag = DAG()
        for i in range(1, 5):
            dag.add_node(str(i), {"id": str(i)})

        dag.add_edge("2", "1")  # 2 → 1
        dag.add_edge("3", "1")  # 3 → 1
        dag.add_edge("4", "2")  # 4 → 2
        dag.add_edge("4", "3")  # 4 → 3

        result = dag.topological_sort()
        ids = [node["id"] for node in result]

        # Epic 1 should come before 2 and 3
        assert ids.index("1") < ids.index("2")
        assert ids.index("1") < ids.index("3")
        # Epic 4 should come last
        assert ids.index("4") == 3

    def test_topological_sort_raises_on_cycle(self):
        """Test topological sort raises error when cycle exists."""
        dag = DAG()
        dag.add_node("1", {"id": "1"})
        dag.add_node("2", {"id": "2"})
        dag.add_edge("1", "2")
        dag.add_edge("2", "1")  # Cycle

        with pytest.raises(ValueError, match="cycle"):
            dag.topological_sort()


class TestGetParallelNodes:
    """Test get_parallel_nodes method."""

    def test_get_parallel_nodes_empty_completed(self):
        """Test get_parallel_nodes with no completed nodes."""
        dag = DAG()
        dag.add_node("1", {"id": "1"})
        dag.add_node("2", {"id": "2"})
        dag.add_edge("2", "1")  # 2 depends on 1

        parallel = dag.get_parallel_nodes(set())

        # Only Epic 1 should be ready (no dependencies)
        assert len(parallel) == 1
        assert parallel[0]["id"] == "1"

    def test_get_parallel_nodes_with_completed(self):
        """Test get_parallel_nodes after completing some nodes."""
        dag = DAG()
        for i in range(1, 5):
            dag.add_node(str(i), {"id": str(i)})

        dag.add_edge("2", "1")  # 2 → 1
        dag.add_edge("3", "1")  # 3 → 1
        dag.add_edge("4", "2")  # 4 → 2
        dag.add_edge("4", "3")  # 4 → 3

        # After completing Epic 1
        parallel = dag.get_parallel_nodes({"1"})
        parallel_ids = {node["id"] for node in parallel}

        # Epic 2 and 3 should be ready
        assert parallel_ids == {"2", "3"}

        # After completing 1, 2, 3
        parallel = dag.get_parallel_nodes({"1", "2", "3"})
        parallel_ids = {node["id"] for node in parallel}

        # Epic 4 should be ready
        assert parallel_ids == {"4"}


class TestDAGMetrics:
    """Test DAG metric methods."""

    def test_get_node_count(self):
        """Test get_node_count returns correct count."""
        dag = DAG()
        assert dag.get_node_count() == 0

        dag.add_node("1", {"id": "1"})
        assert dag.get_node_count() == 1

        for i in range(2, 6):
            dag.add_node(str(i), {"id": str(i)})
        assert dag.get_node_count() == 5

    def test_get_edge_count(self):
        """Test get_edge_count returns correct count."""
        dag = DAG()
        for i in range(1, 4):
            dag.add_node(str(i), {"id": str(i)})

        assert dag.get_edge_count() == 0

        dag.add_edge("2", "1")
        assert dag.get_edge_count() == 1

        dag.add_edge("3", "1")
        dag.add_edge("3", "2")
        assert dag.get_edge_count() == 3
