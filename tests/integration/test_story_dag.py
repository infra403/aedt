"""Integration tests for Story DAG construction."""
from pathlib import Path

import pytest

from aedt.core.config_manager import ConfigManager
from aedt.core.logger import AEDTLogger
from aedt.domain.dependency_analyzer import DependencyAnalyzer
from aedt.domain.epic_parser import EpicParser
from aedt.domain.exceptions import CircularDependencyError, InvalidPrerequisiteError


@pytest.fixture
def logger():
    """Create AEDTLogger for testing."""
    log_dir = Path(".").resolve() / '.aedt' / 'logs'
    return AEDTLogger(log_dir=log_dir, log_level="INFO")


@pytest.fixture
def dependency_analyzer(logger):
    """Create DependencyAnalyzer instance."""
    return DependencyAnalyzer(logger)


@pytest.fixture
def epic_parser(logger):
    """Create EpicParser with mocked config."""
    from unittest.mock import Mock

    config = Mock()
    config.get = Mock(side_effect=lambda k, d=None: {
        'epic_docs_path': 'tests/fixtures/epics/',
        'epic_file_pattern': '*.md',
    }.get(k, d))

    return EpicParser(config, logger)


class TestStoryDAGFromRealEpics:
    """Test Story DAG construction from real Epic files."""

    def test_parse_epic_and_build_story_dag(self, epic_parser, dependency_analyzer):
        """Test full flow: parse Epic → extract Stories → build Story DAG (AC1)."""
        # Use real Epic fixture with Stories
        epic = epic_parser.parse_single_epic('tests/fixtures/epics/epic-with-stories-headings.md')

        assert epic is not None
        assert len(epic.stories) == 3  # 4.1, 4.2, 4.3

        # Build Story DAG
        story_dag = dependency_analyzer.build_story_dag(epic.stories, epic_id=epic.id)

        # Verify DAG structure
        assert story_dag.get_node_count() == 3
        # Story 4.2 depends on 4.1, Story 4.3 depends on 4.1 and 4.2
        assert story_dag.get_edge_count() >= 2

    def test_parallel_story_execution_simulation(self, epic_parser, dependency_analyzer):
        """Test simulating parallel Story execution (AC3)."""
        epic = epic_parser.parse_single_epic('tests/fixtures/epics/epic-with-stories-headings.md')
        story_dag = dependency_analyzer.build_story_dag(epic.stories)

        # Initially, only Story 4.1 can run (no prerequisites)
        parallel = dependency_analyzer.get_parallel_stories(story_dag, set())
        parallel_ids = {s.id for s in parallel}
        assert "4.1" in parallel_ids

        # After Story 4.1 completes, Story 4.2 can run
        parallel = dependency_analyzer.get_parallel_stories(story_dag, {"4.1"})
        parallel_ids = {s.id for s in parallel}
        assert "4.2" in parallel_ids

        # After both 4.1 and 4.2 complete, Story 4.3 can run
        parallel = dependency_analyzer.get_parallel_stories(story_dag, {"4.1", "4.2"})
        parallel_ids = {s.id for s in parallel}
        assert "4.3" in parallel_ids

    def test_numbered_list_stories_dag(self, epic_parser, dependency_analyzer):
        """Test Story DAG from numbered list format Epic."""
        epic = epic_parser.parse_single_epic('tests/fixtures/epics/epic-with-stories-list.md')

        assert epic is not None
        assert len(epic.stories) == 3  # 3.1, 3.2, 3.3

        # Build Story DAG
        story_dag = dependency_analyzer.build_story_dag(epic.stories)

        # These Stories have no prerequisites (numbered list doesn't include prereqs)
        assert story_dag.get_node_count() == 3


class TestStoryDAGValidation:
    """Test Story DAG validation scenarios."""

    def test_story_prerequisite_validation(self, dependency_analyzer):
        """Test prerequisite validation (AC2)."""
        from aedt.domain.models.story import Story

        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=[]),
            Story(id="3.2", title="Story 3.2", prerequisites=["3.1"]),
            Story(id="3.3", title="Story 3.3", prerequisites=["3.1", "3.2"]),
        ]

        # Should succeed
        story_dag = dependency_analyzer.build_story_dag(stories, epic_id="3")
        assert story_dag.get_node_count() == 3

    def test_invalid_prerequisite_detection(self, dependency_analyzer):
        """Test detecting invalid prerequisite (AC2)."""
        from aedt.domain.models.story import Story

        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=[]),
            Story(id="3.2", title="Story 3.2", prerequisites=["3.9"]),  # Invalid
        ]

        with pytest.raises(InvalidPrerequisiteError) as exc_info:
            dependency_analyzer.build_story_dag(stories)

        assert exc_info.value.invalid_prereq_id == "3.9"
        assert exc_info.value.story_id == "3.2"

    def test_story_circular_dependency_detection(self, dependency_analyzer):
        """Test detecting circular dependencies in Stories (AC2)."""
        from aedt.domain.models.story import Story

        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=["3.2"]),
            Story(id="3.2", title="Story 3.2", prerequisites=["3.1"]),
        ]

        with pytest.raises(CircularDependencyError):
            dependency_analyzer.build_story_dag(stories)


class TestMultiModeScenarios:
    """Test scenarios for multi-mode Epic execution."""

    def test_multi_mode_story_scheduling(self, dependency_analyzer):
        """Test multi-mode Story scheduling scenario (AC1, AC3)."""
        from aedt.domain.models.story import Story

        # Simulate an Epic with 5 Stories (multi-mode threshold)
        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=[]),
            Story(id="3.2", title="Story 3.2", prerequisites=["3.1"]),
            Story(id="3.3", title="Story 3.3", prerequisites=["3.1"]),
            Story(id="3.4", title="Story 3.4", prerequisites=["3.2"]),
            Story(id="3.5", title="Story 3.5", prerequisites=["3.3"]),
        ]

        story_dag = dependency_analyzer.build_story_dag(stories, epic_id="3")

        # Verify topological sort for execution order
        sorted_stories = story_dag.topological_sort()
        sorted_ids = [s.id for s in sorted_stories]

        # Story 3.1 should come first
        assert sorted_ids[0] == "3.1"

        # Simulate progressive completion
        completed = set()

        # Round 1: Start with 3.1
        parallel = dependency_analyzer.get_parallel_stories(story_dag, completed)
        assert len(parallel) == 1
        assert parallel[0].id == "3.1"
        completed.add("3.1")

        # Round 2: After 3.1, both 3.2 and 3.3 can run in parallel
        parallel = dependency_analyzer.get_parallel_stories(story_dag, completed)
        parallel_ids = {s.id for s in parallel}
        assert parallel_ids == {"3.2", "3.3"}
        completed.update(["3.2", "3.3"])

        # Round 3: After 3.2 and 3.3, both 3.4 and 3.5 can run
        parallel = dependency_analyzer.get_parallel_stories(story_dag, completed)
        parallel_ids = {s.id for s in parallel}
        assert parallel_ids == {"3.4", "3.5"}

    def test_story_model_helper_in_context(self, dependency_analyzer):
        """Test Story.has_unmet_prerequisites in scheduling context."""
        from aedt.domain.models.story import Story

        stories = [
            Story(id="3.1", title="Story 3.1", prerequisites=[]),
            Story(id="3.2", title="Story 3.2", prerequisites=["3.1"]),
        ]

        completed = set()

        # Story 3.2 has unmet prerequisites initially
        assert stories[1].has_unmet_prerequisites(completed) is True

        # After completing 3.1
        completed.add("3.1")
        assert stories[1].has_unmet_prerequisites(completed) is False
