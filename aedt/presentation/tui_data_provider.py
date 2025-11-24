"""TUI Data Provider for Epic dependency visualization."""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from aedt.core.logger import AEDTLogger
from aedt.domain.dependency_analyzer import DependencyAnalyzer
from aedt.domain.epic_parser import EpicParser
from aedt.domain.models.dag import DAG
from aedt.domain.models.epic import Epic


# Status icon mapping for TUI display
STATUS_ICONS = {
    "completed": "✓",
    "developing": "⚙",
    "in-progress": "⚙",
    "queued": "⏳",
    "failed": "✗",
    "backlog": "○",
    "contexted": "◐",
    "drafted": "◔",
    "review": "◑",
}


@dataclass
class EpicDependencyView:
    """View model for Epic dependency display in TUI."""

    epic_id: str
    epic_title: str
    dependencies: List[Tuple[str, str, str]]  # (epic_id, title, status)
    missing_dependencies: List[str]  # Epic IDs of unmet dependencies
    is_parallel: bool  # Can this Epic run now?
    is_queued: bool  # Is this Epic waiting for dependencies?


class TUIDataProvider:
    """Provides formatted data for TUI Epic dependency visualization."""

    def __init__(
        self,
        epic_parser: EpicParser,
        dependency_analyzer: DependencyAnalyzer,
        logger: AEDTLogger,
    ):
        """
        Initialize TUI Data Provider.

        Args:
            epic_parser: EpicParser instance
            dependency_analyzer: DependencyAnalyzer instance
            logger: AEDTLogger instance
        """
        self.epic_parser = epic_parser
        self.analyzer = dependency_analyzer
        self.aedt_logger = logger
        self.logger = logger.get_logger("tui_data_provider")

    def get_epic_dependency_view(
        self,
        epic: Epic,
        all_epics: List[Epic],
        completed_epic_ids: List[str],
    ) -> EpicDependencyView:
        """
        Get dependency view data for an Epic.

        Args:
            epic: The Epic to get dependency view for
            all_epics: List of all Epics in the project
            completed_epic_ids: List of completed Epic IDs

        Returns:
            EpicDependencyView with formatted dependency information
        """
        # Build Epic lookup
        epic_lookup = {e.id: e for e in all_epics}

        # Get dependency details
        dependencies = []
        for dep_id in epic.depends_on:
            dep_epic = epic_lookup.get(dep_id)
            if dep_epic:
                # Determine status (would come from StateManager in real impl)
                status = self._infer_epic_status(dep_id, completed_epic_ids)
                dependencies.append((dep_id, dep_epic.title, status))
            else:
                # Missing dependency
                dependencies.append((dep_id, "Unknown", "unknown"))

        # Determine missing dependencies
        completed_set = set(completed_epic_ids)
        missing_deps = [
            dep_id for dep_id in epic.depends_on if dep_id not in completed_set
        ]

        # Check if Epic is parallel or queued
        is_parallel = len(missing_deps) == 0 and epic.id not in completed_set
        is_queued = len(missing_deps) > 0

        return EpicDependencyView(
            epic_id=epic.id,
            epic_title=epic.title,
            dependencies=dependencies,
            missing_dependencies=missing_deps,
            is_parallel=is_parallel,
            is_queued=is_queued,
        )

    def format_dependencies(
        self, dependency_view: EpicDependencyView
    ) -> str:
        """
        Format Epic dependencies for TUI display.

        Args:
            dependency_view: EpicDependencyView instance

        Returns:
            Formatted string ready for TUI display
        """
        if not dependency_view.dependencies:
            return "None"

        lines = []
        for dep_id, title, status in dependency_view.dependencies:
            icon = STATUS_ICONS.get(status, "?")
            status_display = status.capitalize() if status != "unknown" else "Unknown"
            lines.append(f"  - Epic {dep_id}: {title} ({icon} {status_display})")

        return "\n".join(lines)

    def get_all_epic_views(
        self,
        all_epics: List[Epic],
        completed_epic_ids: List[str],
    ) -> Dict[str, EpicDependencyView]:
        """
        Get dependency views for all Epics.

        Args:
            all_epics: List of all Epics
            completed_epic_ids: List of completed Epic IDs

        Returns:
            Dictionary mapping Epic ID to EpicDependencyView
        """
        views = {}
        for epic in all_epics:
            view = self.get_epic_dependency_view(epic, all_epics, completed_epic_ids)
            views[epic.id] = view

        self.logger.debug(f"Generated dependency views for {len(views)} Epics")
        return views

    def _infer_epic_status(
        self, epic_id: str, completed_epic_ids: List[str]
    ) -> str:
        """
        Infer Epic status based on completed list.

        In real implementation, this would query StateManager.
        For now, we infer: completed if in list, otherwise developing.

        Args:
            epic_id: Epic ID to check
            completed_epic_ids: List of completed Epic IDs

        Returns:
            Status string
        """
        if epic_id in completed_epic_ids:
            return "completed"
        return "developing"
