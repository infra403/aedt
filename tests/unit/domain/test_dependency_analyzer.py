"""Unit tests for DependencyAnalyzer."""
from unittest.mock import Mock

import pytest

from aedt.domain.dependency_analyzer import DependencyAnalyzer
from aedt.domain.exceptions import CircularDependencyError, InvalidDependencyError
from aedt.domain.models.epic import Epic


@pytest.fixture
def mock_logger():
    """Mock AEDTLogger."""
    logger = Mock()
    mock_module_logger = Mock()
    logger.get_logger.return_value = mock_module_logger
    return logger


@pytest.fixture
def analyzer(mock_logger):
    """Create DependencyAnalyzer instance."""
    return DependencyAnalyzer(mock_logger)


class TestDependencyAnalyzerInit:
    """Test DependencyAnalyzer initialization."""

    def test_init_stores_logger(self, mock_logger):
        """Test that __init__ stores logger."""
        analyzer = DependencyAnalyzer(mock_logger)
        assert analyzer.aedt_logger == mock_logger
        mock_logger.get_logger.assert_called_once_with("dependency_analyzer")


class TestBuildEpicDAG:
    """Test build_epic_dag method."""

    def test_build_dag_simple_chain(self, analyzer):
        """Test building DAG with simple linear dependencies."""
        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=["2"]),
        ]

        dag = analyzer.build_epic_dag(epics)

        assert dag.get_node_count() == 3
        assert dag.get_edge_count() == 2
        assert "1" in dag.edges["2"]
        assert "2" in dag.edges["3"]

    def test_build_dag_parallel_dependencies(self, analyzer):
        """Test building DAG with parallel dependencies (AC1)."""
        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=["1"]),
            Epic(id="4", title="Epic 4", depends_on=["2", "3"]),
        ]

        dag = analyzer.build_epic_dag(epics)

        assert dag.get_node_count() == 4
        assert dag.get_edge_count() == 4
        # Epic 1 has no dependencies
        assert dag.edges["1"] == []
        # Epic 2 and 3 depend on Epic 1
        assert "1" in dag.edges["2"]
        assert "1" in dag.edges["3"]
        # Epic 4 depends on Epic 2 and 3
        assert "2" in dag.edges["4"]
        assert "3" in dag.edges["4"]

    def test_build_dag_empty_list(self, analyzer):
        """Test building DAG from empty Epic list."""
        dag = analyzer.build_epic_dag([])

        assert dag.get_node_count() == 0
        assert dag.get_edge_count() == 0

    def test_build_dag_single_epic(self, analyzer):
        """Test building DAG from single Epic with no dependencies."""
        epics = [Epic(id="1", title="Epic 1", depends_on=[])]

        dag = analyzer.build_epic_dag(epics)

        assert dag.get_node_count() == 1
        assert dag.get_edge_count() == 0


class TestCircularDependencyDetection:
    """Test circular dependency detection (AC2)."""

    def test_detect_simple_cycle(self, analyzer):
        """Test detecting simple 2-node cycle (AC2)."""
        epics = [
            Epic(id="2", title="Epic 2", depends_on=["3"]),
            Epic(id="3", title="Epic 3", depends_on=["2"]),
        ]

        with pytest.raises(CircularDependencyError) as exc_info:
            analyzer.build_epic_dag(epics)

        assert "2" in str(exc_info.value) or "3" in str(exc_info.value)
        assert exc_info.value.cycle_path  # Should contain the cycle path

    def test_detect_self_reference_cycle(self, analyzer):
        """Test detecting self-referencing cycle."""
        epics = [Epic(id="1", title="Epic 1", depends_on=["1"])]

        with pytest.raises(CircularDependencyError):
            analyzer.build_epic_dag(epics)

    def test_detect_complex_cycle(self, analyzer):
        """Test detecting complex multi-node cycle."""
        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=["2"]),
            Epic(id="4", title="Epic 4", depends_on=["3"]),
            Epic(id="5", title="Epic 5", depends_on=["4"]),
            Epic(id="2", title="Epic 2 Updated", depends_on=["5"]),  # Creates cycle
        ]

        # Note: This test has duplicate Epic ID "2", which might not be realistic
        # Better test: Epic 5 depends on both 4 and 2
        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=["2"]),
            Epic(id="4", title="Epic 4", depends_on=["3"]),
            Epic(id="5", title="Epic 5", depends_on=["4", "2"]),  # No cycle here
        ]

        # This should NOT raise (no cycle)
        dag = analyzer.build_epic_dag(epics)
        assert dag.get_node_count() == 5

        # Create actual cycle: 2→3→4→2
        epics_with_cycle = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["4"]),  # Cycle!
            Epic(id="3", title="Epic 3", depends_on=["2"]),
            Epic(id="4", title="Epic 4", depends_on=["3"]),
        ]

        with pytest.raises(CircularDependencyError):
            analyzer.build_epic_dag(epics_with_cycle)


class TestInvalidDependencyDetection:
    """Test invalid dependency detection (AC3)."""

    def test_detect_missing_dependency(self, analyzer):
        """Test detecting dependency on non-existent Epic (AC3)."""
        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="5", title="Epic 5", depends_on=["99"]),  # Epic 99 doesn't exist
        ]

        with pytest.raises(InvalidDependencyError) as exc_info:
            analyzer.build_epic_dag(epics)

        assert exc_info.value.missing_epic_id == "99"
        assert exc_info.value.source_epic_id == "5"
        assert "Epic 5" in str(exc_info.value)
        assert "Epic 99" in str(exc_info.value)

    def test_detect_multiple_missing_dependencies(self, analyzer):
        """Test detecting first missing dependency when multiple are invalid."""
        epics = [
            Epic(id="1", title="Epic 1", depends_on=["99", "88"]),  # Both missing
        ]

        # Should raise for the first missing dependency encountered
        with pytest.raises(InvalidDependencyError) as exc_info:
            analyzer.build_epic_dag(epics)

        # Either 99 or 88 should be reported (depends on iteration order)
        assert exc_info.value.missing_epic_id in ["99", "88"]


class TestValidateDAG:
    """Test validate_dag method."""

    def test_validate_dag_success(self, analyzer):
        """Test validating a valid DAG."""
        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
        ]

        dag = analyzer.build_epic_dag(epics)
        is_valid, error_msg = analyzer.validate_dag(dag)

        assert is_valid is True
        assert error_msg is None

    def test_validate_dag_with_cycle(self, analyzer, mock_logger):
        """Test validating DAG with cycle returns error."""
        from aedt.domain.models.dag import DAG

        dag = DAG()
        dag.add_node("1", Epic(id="1", title="Epic 1"))
        dag.add_node("2", Epic(id="2", title="Epic 2"))
        dag.add_edge("1", "2")
        dag.add_edge("2", "1")  # Cycle

        is_valid, error_msg = analyzer.validate_dag(dag)

        assert is_valid is False
        assert error_msg is not None
        assert "Circular dependency" in error_msg


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""

    def test_large_dag_performance(self, analyzer):
        """Test building large DAG (100+ nodes)."""
        # Create 100 Epics with linear dependencies
        epics = [Epic(id="1", title="Epic 1", depends_on=[])]
        for i in range(2, 101):
            epics.append(Epic(id=str(i), title=f"Epic {i}", depends_on=[str(i - 1)]))

        dag = analyzer.build_epic_dag(epics)

        assert dag.get_node_count() == 100
        assert dag.get_edge_count() == 99

    def test_deep_dependency_chain(self, analyzer):
        """Test deep dependency chain (1→2→3→4→5)."""
        epics = []
        for i in range(1, 6):
            deps = [] if i == 1 else [str(i - 1)]
            epics.append(Epic(id=str(i), title=f"Epic {i}", depends_on=deps))

        dag = analyzer.build_epic_dag(epics)

        # Verify topological sort maintains order
        sorted_nodes = dag.topological_sort()
        sorted_ids = [epic.id for epic in sorted_nodes]
        assert sorted_ids == ["1", "2", "3", "4", "5"]

    def test_wide_dependencies(self, analyzer):
        """Test Epic with many dependencies (1-10)."""
        epics = [Epic(id=str(i), title=f"Epic {i}", depends_on=[]) for i in range(1, 11)]
        # Epic 11 depends on all previous Epics
        epics.append(
            Epic(
                id="11",
                title="Epic 11",
                depends_on=[str(i) for i in range(1, 11)],
            )
        )

        dag = analyzer.build_epic_dag(epics)

        assert dag.get_node_count() == 11
        assert dag.get_edge_count() == 10
        # Epic 11 should have 10 dependencies
        assert len(dag.edges["11"]) == 10


class TestBuildStoryDAG:
    """Test build_story_dag method."""

    def test_build_story_dag_simple_chain(self, analyzer):
        """Test building Story DAG with simple linear dependencies (AC1)."""
        from aedt.domain.models.story import Story

        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=[]),
            Story(id="3.2", title="Story 3.2", prerequisites=["3.1"]),
            Story(id="3.3", title="Story 3.3", prerequisites=["3.2"]),
        ]

        dag = analyzer.build_story_dag(stories, epic_id="3")

        assert dag.get_node_count() == 3
        assert dag.get_edge_count() == 2
        assert "3.1" in dag.edges["3.2"]
        assert "3.2" in dag.edges["3.3"]

    def test_build_story_dag_parallel_dependencies(self, analyzer):
        """Test building Story DAG with parallel dependencies (AC1)."""
        from aedt.domain.models.story import Story

        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=[]),
            Story(id="3.2", title="Story 3.2", prerequisites=["3.1"]),
            Story(id="3.3", title="Story 3.3", prerequisites=["3.1"]),
            Story(id="3.4", title="Story 3.4", prerequisites=["3.2", "3.3"]),
        ]

        dag = analyzer.build_story_dag(stories, epic_id="3")

        assert dag.get_node_count() == 4
        assert dag.get_edge_count() == 4
        # Story 3.1 has no prerequisites
        assert dag.edges["3.1"] == []
        # Stories 3.2 and 3.3 depend on 3.1
        assert "3.1" in dag.edges["3.2"]
        assert "3.1" in dag.edges["3.3"]
        # Story 3.4 depends on 3.2 and 3.3
        assert "3.2" in dag.edges["3.4"]
        assert "3.3" in dag.edges["3.4"]

    def test_build_story_dag_empty_list(self, analyzer):
        """Test building Story DAG from empty list."""
        dag = analyzer.build_story_dag([])

        assert dag.get_node_count() == 0
        assert dag.get_edge_count() == 0

    def test_build_story_dag_no_prerequisites(self, analyzer):
        """Test building Story DAG when all Stories have no prerequisites."""
        from aedt.domain.models.story import Story

        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=[]),
            Story(id="3.2", title="Story 3.2", prerequisites=[]),
            Story(id="3.3", title="Story 3.3", prerequisites=[]),
        ]

        dag = analyzer.build_story_dag(stories)

        assert dag.get_node_count() == 3
        assert dag.get_edge_count() == 0  # No dependencies


class TestStoryCircularDependencyDetection:
    """Test circular dependency detection for Stories (AC2)."""

    def test_detect_simple_story_cycle(self, analyzer):
        """Test detecting simple 2-Story cycle (AC2)."""
        from aedt.domain.models.story import Story
        from aedt.domain.exceptions import CircularDependencyError

        stories = [
            Story(id="3.2", title="Story 3.2", prerequisites=["3.3"]),
            Story(id="3.3", title="Story 3.3", prerequisites=["3.2"]),
        ]

        with pytest.raises(CircularDependencyError) as exc_info:
            analyzer.build_story_dag(stories)

        assert "3.2" in str(exc_info.value) or "3.3" in str(exc_info.value)

    def test_detect_self_reference_story_cycle(self, analyzer):
        """Test detecting self-referencing Story."""
        from aedt.domain.models.story import Story
        from aedt.domain.exceptions import CircularDependencyError

        stories = [Story(id="3.1", title="Story 3.1", prerequisites=["3.1"])]

        with pytest.raises(CircularDependencyError):
            analyzer.build_story_dag(stories)

    def test_detect_complex_story_cycle(self, analyzer):
        """Test detecting complex multi-Story cycle."""
        from aedt.domain.models.story import Story
        from aedt.domain.exceptions import CircularDependencyError

        # Create cycle: 3.2→3.3→3.4→3.2
        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=[]),
            Story(id="3.2", title="Story 3.2", prerequisites=["3.4"]),  # Cycle!
            Story(id="3.3", title="Story 3.3", prerequisites=["3.2"]),
            Story(id="3.4", title="Story 3.4", prerequisites=["3.3"]),
        ]

        with pytest.raises(CircularDependencyError):
            analyzer.build_story_dag(stories)


class TestInvalidPrerequisiteDetection:
    """Test invalid prerequisite detection for Stories (AC2)."""

    def test_detect_missing_prerequisite(self, analyzer):
        """Test detecting prerequisite on non-existent Story (AC2)."""
        from aedt.domain.models.story import Story
        from aedt.domain.exceptions import InvalidPrerequisiteError

        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=[]),
            Story(id="3.2", title="Story 3.2", prerequisites=["3.9"]),  # 3.9 doesn't exist
        ]

        with pytest.raises(InvalidPrerequisiteError) as exc_info:
            analyzer.build_story_dag(stories)

        assert exc_info.value.invalid_prereq_id == "3.9"
        assert exc_info.value.story_id == "3.2"
        assert "Story 3.2" in str(exc_info.value)
        assert "3.9" in str(exc_info.value)

    def test_detect_multiple_missing_prerequisites(self, analyzer):
        """Test detecting first missing prerequisite when multiple are invalid."""
        from aedt.domain.models.story import Story
        from aedt.domain.exceptions import InvalidPrerequisiteError

        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=["3.8", "3.9"]),  # Both missing
        ]

        # Should raise for the first missing prerequisite encountered
        with pytest.raises(InvalidPrerequisiteError) as exc_info:
            analyzer.build_story_dag(stories)

        # Either 3.8 or 3.9 should be reported
        assert exc_info.value.invalid_prereq_id in ["3.8", "3.9"]


class TestGetParallelStories:
    """Test get_parallel_stories method (AC3)."""

    def test_get_parallel_stories_empty_completed(self, analyzer):
        """Test get_parallel_stories with no completed Stories (AC3)."""
        from aedt.domain.models.story import Story

        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=[]),
            Story(id="3.2", title="Story 3.2", prerequisites=["3.1"]),
        ]

        dag = analyzer.build_story_dag(stories)
        parallel = analyzer.get_parallel_stories(dag, set())

        # Only Story 3.1 should be ready
        assert len(parallel) == 1
        assert parallel[0].id == "3.1"

    def test_get_parallel_stories_with_completed(self, analyzer):
        """Test get_parallel_stories after completing some Stories (AC3)."""
        from aedt.domain.models.story import Story

        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=[]),
            Story(id="3.2", title="Story 3.2", prerequisites=["3.1"]),
            Story(id="3.3", title="Story 3.3", prerequisites=["3.1"]),
            Story(id="3.4", title="Story 3.4", prerequisites=["3.2", "3.3"]),
        ]

        dag = analyzer.build_story_dag(stories)

        # After completing Story 3.1
        parallel = analyzer.get_parallel_stories(dag, {"3.1"})
        parallel_ids = {story.id for story in parallel}

        # Stories 3.2 and 3.3 should be ready
        assert parallel_ids == {"3.2", "3.3"}

        # After completing 3.1, 3.2, 3.3
        parallel = analyzer.get_parallel_stories(dag, {"3.1", "3.2", "3.3"})
        parallel_ids = {story.id for story in parallel}

        # Story 3.4 should be ready
        assert parallel_ids == {"3.4"}

    def test_get_parallel_stories_incremental(self, analyzer):
        """Test incremental Story completion scenario (AC3)."""
        from aedt.domain.models.story import Story

        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=[]),
            Story(id="3.2", title="Story 3.2", prerequisites=["3.1"]),
            Story(id="3.3", title="Story 3.3", prerequisites=["3.1", "3.2"]),
        ]

        dag = analyzer.build_story_dag(stories)

        # Initially, only 3.1 can run
        parallel = analyzer.get_parallel_stories(dag, set())
        assert [s.id for s in parallel] == ["3.1"]

        # After 3.1 completes, only 3.2 can run
        parallel = analyzer.get_parallel_stories(dag, {"3.1"})
        assert [s.id for s in parallel] == ["3.2"]

        # After 3.1 and 3.2 complete, 3.3 can run
        parallel = analyzer.get_parallel_stories(dag, {"3.1", "3.2"})
        assert [s.id for s in parallel] == ["3.3"]


class TestGetParallelEpics:
    """Test get_parallel_epics() method (Story 3.5)."""

    def test_get_parallel_epics_no_dependencies(self, analyzer):
        """Test identifying Epics with no dependencies (AC1)."""
        from aedt.domain.models.epic import Epic

        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=[]),
        ]

        dag = analyzer.build_epic_dag(epics)

        # No Epics completed
        parallel = analyzer.get_parallel_epics(dag, [])
        parallel_ids = {epic.id for epic in parallel}

        # Epics 1 and 3 have no dependencies
        assert parallel_ids == {"1", "3"}

    def test_get_parallel_epics_dependencies_satisfied(self, analyzer):
        """Test identifying Epics with satisfied dependencies (AC2)."""
        from aedt.domain.models.epic import Epic

        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=[]),
        ]

        dag = analyzer.build_epic_dag(epics)

        # Epic 1 completed
        parallel = analyzer.get_parallel_epics(dag, ["1"])
        parallel_ids = {epic.id for epic in parallel}

        # Epic 2's dependency satisfied, Epic 3 still available
        assert parallel_ids == {"2", "3"}

    def test_get_parallel_epics_exclude_completed(self, analyzer):
        """Test excluding completed Epics (AC3)."""
        from aedt.domain.models.epic import Epic

        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=[]),
        ]

        dag = analyzer.build_epic_dag(epics)

        # Epics 1 and 3 completed
        parallel = analyzer.get_parallel_epics(dag, ["1", "3"])
        parallel_ids = {epic.id for epic in parallel}

        # Only Epic 2 available
        assert parallel_ids == {"2"}

    def test_get_parallel_epics_empty_dag(self, analyzer):
        """Test with empty DAG."""
        from aedt.domain.models.dag import DAG

        dag = DAG()
        parallel = analyzer.get_parallel_epics(dag, [])

        assert parallel == []

    def test_get_parallel_epics_all_completed(self, analyzer):
        """Test when all Epics are completed."""
        from aedt.domain.models.epic import Epic

        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
        ]

        dag = analyzer.build_epic_dag(epics)

        # All completed
        parallel = analyzer.get_parallel_epics(dag, ["1", "2"])
        assert parallel == []

    def test_get_parallel_epics_complex_dependencies(self, analyzer):
        """Test complex dependency scenario."""
        from aedt.domain.models.epic import Epic

        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=["1"]),
            Epic(id="4", title="Epic 4", depends_on=["2", "3"]),
            Epic(id="5", title="Epic 5", depends_on=[]),
        ]

        dag = analyzer.build_epic_dag(epics)

        # Initially: only 1 and 5 available
        parallel = analyzer.get_parallel_epics(dag, [])
        parallel_ids = {epic.id for epic in parallel}
        assert parallel_ids == {"1", "5"}

        # After 1 completes: 2, 3, and 5 available
        parallel = analyzer.get_parallel_epics(dag, ["1"])
        parallel_ids = {epic.id for epic in parallel}
        assert parallel_ids == {"2", "3", "5"}

        # After 1, 2, 3 complete: 4 and 5 available
        parallel = analyzer.get_parallel_epics(dag, ["1", "2", "3"])
        parallel_ids = {epic.id for epic in parallel}
        assert parallel_ids == {"4", "5"}

    def test_get_parallel_epics_incremental(self, analyzer):
        """Test incremental Epic completion scenario."""
        from aedt.domain.models.epic import Epic

        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=["1", "2"]),
        ]

        dag = analyzer.build_epic_dag(epics)

        # Initially, only 1 can run
        parallel = analyzer.get_parallel_epics(dag, [])
        assert [e.id for e in parallel] == ["1"]

        # After 1 completes, only 2 can run
        parallel = analyzer.get_parallel_epics(dag, ["1"])
        assert [e.id for e in parallel] == ["2"]

        # After 1 and 2 complete, 3 can run
        parallel = analyzer.get_parallel_epics(dag, ["1", "2"])
        assert [e.id for e in parallel] == ["3"]


class TestGetQueuedEpics:
    """Test get_queued_epics() method (Story 3.6)."""

    def test_get_queued_epics_single_missing_dependency(self, analyzer):
        """Test identifying Epic with single missing dependency (AC1)."""
        from aedt.domain.models.epic import Epic

        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=["1"]),
            Epic(id="4", title="Epic 4", depends_on=["2", "3"]),
        ]

        dag = analyzer.build_epic_dag(epics)

        # Epic 1 and 2 completed, Epic 3 still running (not completed)
        queued = analyzer.get_queued_epics(dag, ["1", "2"])

        # Only Epic 4 should be queued (waiting for Epic 3)
        # Epic 3 is NOT queued because its dependency (Epic 1) is completed
        queued_dict = {epic.id: missing for epic, missing in queued}

        assert "4" in queued_dict
        assert queued_dict["4"] == ["3"]  # Epic 4 waiting for 3
        assert "3" not in queued_dict  # Epic 3 is parallel, not queued

    def test_get_queued_epics_multiple_missing_dependencies(self, analyzer):
        """Test identifying Epic with multiple missing dependencies (AC2)."""
        from aedt.domain.models.epic import Epic

        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=["1"]),
            Epic(id="4", title="Epic 4", depends_on=["1"]),
            Epic(id="5", title="Epic 5", depends_on=["2", "3", "4"]),
        ]

        dag = analyzer.build_epic_dag(epics)

        # Epics 1 and 2 completed
        queued = analyzer.get_queued_epics(dag, ["1", "2"])
        queued_dict = {epic.id: missing for epic, missing in queued}

        # Epic 5 should have 2 missing dependencies: 3 and 4
        assert "5" in queued_dict
        assert set(queued_dict["5"]) == {"3", "4"}

    def test_get_queued_epics_dependency_completion_removes_from_queue(self, analyzer):
        """Test Epic removed from queue when dependency completes (AC3)."""
        from aedt.domain.models.epic import Epic

        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=["1"]),
            Epic(id="4", title="Epic 4", depends_on=["2", "3"]),
        ]

        dag = analyzer.build_epic_dag(epics)

        # Before Epic 3 completes, Epic 4 is queued waiting for 3
        queued = analyzer.get_queued_epics(dag, ["1", "2"])
        queued_ids = {epic.id for epic, _ in queued}
        assert "4" in queued_ids

        # After Epic 3 completes, Epic 4 is no longer queued
        queued = analyzer.get_queued_epics(dag, ["1", "2", "3"])
        queued_ids = {epic.id for epic, _ in queued}
        assert "4" not in queued_ids  # Now parallel, not queued

    def test_get_queued_epics_empty_when_all_completed(self, analyzer):
        """Test empty queue when all Epics completed."""
        from aedt.domain.models.epic import Epic

        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
        ]

        dag = analyzer.build_epic_dag(epics)

        # All completed
        queued = analyzer.get_queued_epics(dag, ["1", "2"])
        assert queued == []

    def test_get_queued_epics_empty_when_all_parallel(self, analyzer):
        """Test empty queue when all Epics can run in parallel."""
        from aedt.domain.models.epic import Epic

        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=[]),
            Epic(id="3", title="Epic 3", depends_on=[]),
        ]

        dag = analyzer.build_epic_dag(epics)

        # No Epics completed, but all can run (no dependencies)
        queued = analyzer.get_queued_epics(dag, [])
        assert queued == []

    def test_parallel_and_queued_are_mutually_exclusive(self, analyzer):
        """Test that parallel and queued Epics don't overlap."""
        from aedt.domain.models.epic import Epic

        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=["1"]),
            Epic(id="4", title="Epic 4", depends_on=["2", "3"]),
        ]

        dag = analyzer.build_epic_dag(epics)

        # Epic 1 completed
        completed = ["1"]
        parallel = analyzer.get_parallel_epics(dag, completed)
        queued = analyzer.get_queued_epics(dag, completed)

        parallel_ids = {e.id for e in parallel}
        queued_ids = {e.id for e, _ in queued}

        # No overlap
        assert parallel_ids.isdisjoint(queued_ids)

        # Together they should cover all non-completed Epics
        all_epic_ids = {"1", "2", "3", "4"}
        completed_set = set(completed)
        assert parallel_ids | queued_ids == all_epic_ids - completed_set

    def test_get_queued_epics_progressive_completion(self, analyzer):
        """Test queued status changes as Epics complete."""
        from aedt.domain.models.epic import Epic

        epics = [
            Epic(id="1", title="Epic 1", depends_on=[]),
            Epic(id="2", title="Epic 2", depends_on=["1"]),
            Epic(id="3", title="Epic 3", depends_on=["1", "2"]),
        ]

        dag = analyzer.build_epic_dag(epics)

        # Initially: 2 and 3 are queued
        queued = analyzer.get_queued_epics(dag, [])
        queued_ids = {epic.id for epic, _ in queued}
        assert queued_ids == {"2", "3"}

        # After Epic 1: only 3 is queued
        queued = analyzer.get_queued_epics(dag, ["1"])
        queued_ids = {epic.id for epic, _ in queued}
        assert queued_ids == {"3"}

        # After Epic 1 and 2: nothing queued
        queued = analyzer.get_queued_epics(dag, ["1", "2"])
        assert queued == []


class TestStoryModelHelpers:
    """Test Story model helper methods."""

    def test_has_unmet_prerequisites_true(self):
        """Test has_unmet_prerequisites returns True when dependencies unmet."""
        from aedt.domain.models.story import Story

        story = Story(id="3.2", title="Story 3.2", prerequisites=["3.1"])
        assert story.has_unmet_prerequisites(set()) is True
        assert story.has_unmet_prerequisites({"3.0"}) is True

    def test_has_unmet_prerequisites_false(self):
        """Test has_unmet_prerequisites returns False when all met."""
        from aedt.domain.models.story import Story

        story = Story(id="3.2", title="Story 3.2", prerequisites=["3.1"])
        assert story.has_unmet_prerequisites({"3.1"}) is False
        assert story.has_unmet_prerequisites({"3.1", "3.0"}) is False

    def test_has_unmet_prerequisites_no_prerequisites(self):
        """Test has_unmet_prerequisites with no prerequisites."""
        from aedt.domain.models.story import Story

        story = Story(id="3.1", title="Story 3.1", prerequisites=[])
        assert story.has_unmet_prerequisites(set()) is False
