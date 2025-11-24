"""Unit tests for TUI Data Provider."""
import pytest

from aedt.core.logger import AEDTLogger
from aedt.domain.dependency_analyzer import DependencyAnalyzer
from aedt.domain.models.epic import Epic
from aedt.presentation.tui_data_provider import TUIDataProvider


@pytest.fixture
def logger(tmp_path):
    """Create test logger."""
    log_dir = tmp_path / ".aedt" / "logs"
    log_dir.mkdir(parents=True)
    return AEDTLogger(log_dir=log_dir, log_level="INFO")


@pytest.fixture
def analyzer(logger):
    """Create DependencyAnalyzer."""
    return DependencyAnalyzer(logger)


@pytest.fixture
def tui_provider(analyzer, logger):
    """Create TUI Data Provider."""
    from unittest.mock import Mock

    epic_parser = Mock()
    return TUIDataProvider(epic_parser, analyzer, logger)


class TestGetEpicDependencyView:
    """Test get_epic_dependency_view() method."""

    def test_epic_with_dependencies_all_completed(self, tui_provider):
        """Test Epic with all dependencies completed (AC1)."""
        epics = [
            Epic(id="1", title="Foundation", depends_on=[]),
            Epic(id="2", title="Parsing", depends_on=["1"]),
            Epic(id="3", title="Analysis", depends_on=["1"]),
        ]

        # Epic 1 completed
        view = tui_provider.get_epic_dependency_view(epics[1], epics, ["1"])

        assert view.epic_id == "2"
        assert view.epic_title == "Parsing"
        assert len(view.dependencies) == 1
        assert view.dependencies[0] == ("1", "Foundation", "completed")
        assert view.missing_dependencies == []
        assert view.is_parallel is True
        assert view.is_queued is False

    def test_epic_with_dependencies_some_incomplete(self, tui_provider):
        """Test Epic with some incomplete dependencies (AC1)."""
        epics = [
            Epic(id="1", title="Foundation", depends_on=[]),
            Epic(id="2", title="Parsing", depends_on=["1"]),
            Epic(id="3", title="Analysis", depends_on=["1"]),
            Epic(id="4", title="Execution", depends_on=["2", "3"]),
        ]

        # Only Epic 1 and 2 completed
        view = tui_provider.get_epic_dependency_view(epics[3], epics, ["1", "2"])

        assert view.epic_id == "4"
        assert len(view.dependencies) == 2
        assert ("2", "Parsing", "completed") in view.dependencies
        assert ("3", "Analysis", "developing") in view.dependencies
        assert view.missing_dependencies == ["3"]
        assert view.is_parallel is False
        assert view.is_queued is True

    def test_epic_with_no_dependencies(self, tui_provider):
        """Test Epic with no dependencies (AC2)."""
        epics = [
            Epic(id="1", title="Foundation", depends_on=[]),
        ]

        view = tui_provider.get_epic_dependency_view(epics[0], epics, [])

        assert view.epic_id == "1"
        assert view.dependencies == []
        assert view.missing_dependencies == []
        assert view.is_parallel is True
        assert view.is_queued is False

    def test_epic_with_unknown_dependency(self, tui_provider):
        """Test Epic with unknown dependency."""
        epics = [
            Epic(id="2", title="Parsing", depends_on=["99"]),
        ]

        view = tui_provider.get_epic_dependency_view(epics[0], epics, [])

        assert len(view.dependencies) == 1
        assert view.dependencies[0] == ("99", "Unknown", "unknown")
        assert view.missing_dependencies == ["99"]
        assert view.is_queued is True


class TestFormatDependencies:
    """Test format_dependencies() method."""

    def test_format_dependencies_with_mixed_status(self, tui_provider):
        """Test formatting dependencies with mixed status (AC3)."""
        from aedt.presentation.tui_data_provider import EpicDependencyView

        view = EpicDependencyView(
            epic_id="4",
            epic_title="Execution",
            dependencies=[
                ("2", "Parsing", "completed"),
                ("3", "Analysis", "developing"),
            ],
            missing_dependencies=["3"],
            is_parallel=False,
            is_queued=True,
        )

        formatted = tui_provider.format_dependencies(view)

        assert "Epic 2: Parsing (✓ Completed)" in formatted
        assert "Epic 3: Analysis (⚙ Developing)" in formatted
        assert formatted.count("\n") == 1  # 2 lines

    def test_format_dependencies_no_dependencies(self, tui_provider):
        """Test formatting Epic with no dependencies (AC2)."""
        from aedt.presentation.tui_data_provider import EpicDependencyView

        view = EpicDependencyView(
            epic_id="1",
            epic_title="Foundation",
            dependencies=[],
            missing_dependencies=[],
            is_parallel=True,
            is_queued=False,
        )

        formatted = tui_provider.format_dependencies(view)
        assert formatted == "None"

    def test_format_dependencies_unknown_status(self, tui_provider):
        """Test formatting with unknown dependency."""
        from aedt.presentation.tui_data_provider import EpicDependencyView

        view = EpicDependencyView(
            epic_id="2",
            epic_title="Parsing",
            dependencies=[("99", "Unknown", "unknown")],
            missing_dependencies=["99"],
            is_parallel=False,
            is_queued=True,
        )

        formatted = tui_provider.format_dependencies(view)
        assert "Epic 99: Unknown (? Unknown)" in formatted

    def test_status_icon_mapping(self, tui_provider):
        """Test all status icons are displayed correctly (AC3)."""
        from aedt.presentation.tui_data_provider import EpicDependencyView

        view = EpicDependencyView(
            epic_id="10",
            epic_title="Test",
            dependencies=[
                ("1", "Completed Epic", "completed"),
                ("2", "Developing Epic", "developing"),
                ("3", "Queued Epic", "queued"),
                ("4", "Failed Epic", "failed"),
                ("5", "Backlog Epic", "backlog"),
            ],
            missing_dependencies=["2", "3", "4", "5"],
            is_parallel=False,
            is_queued=True,
        )

        formatted = tui_provider.format_dependencies(view)

        assert "✓" in formatted  # completed
        assert "⚙" in formatted  # developing
        assert "⏳" in formatted  # queued
        assert "✗" in formatted  # failed
        assert "○" in formatted  # backlog


class TestGetAllEpicViews:
    """Test get_all_epic_views() method."""

    def test_get_all_epic_views(self, tui_provider):
        """Test getting views for all Epics."""
        epics = [
            Epic(id="1", title="Foundation", depends_on=[]),
            Epic(id="2", title="Parsing", depends_on=["1"]),
            Epic(id="3", title="Analysis", depends_on=["1"]),
            Epic(id="4", title="Execution", depends_on=["2", "3"]),
        ]

        views = tui_provider.get_all_epic_views(epics, ["1"])

        assert len(views) == 4
        assert "1" in views
        assert "2" in views
        assert "3" in views
        assert "4" in views

        # Verify Epic 1 view
        assert views["1"].is_parallel is False  # Already completed (in completed list)
        assert views["1"].dependencies == []

        # Verify Epic 2 view
        assert views["2"].is_parallel is True  # Dependency (1) completed
        assert views["2"].is_queued is False

        # Verify Epic 4 view
        assert views["4"].is_queued is True  # Waiting for 2 and 3
        assert set(views["4"].missing_dependencies) == {"2", "3"}
