"""State Manager for AEDT

This module manages project and epic states with crash recovery and validation.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

from aedt.core.data_store import DataStore

logger = logging.getLogger(__name__)


@dataclass
class EpicState:
    """Epic state data model

    Represents the runtime state of an epic including progress,
    agent assignment, and worktree information.
    """
    epic_id: str
    status: str  # queued/developing/paused/completed/failed/requires_cleanup
    progress: float  # 0-100
    agent_id: Optional[str] = None
    worktree_path: Optional[str] = None
    completed_stories: List[str] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self):
        """Initialize default values for mutable fields"""
        if self.completed_stories is None:
            self.completed_stories = []
        if self.last_updated is None:
            self.last_updated = datetime.utcnow().isoformat()


@dataclass
class ProjectState:
    """Project state data model

    Contains all epic states for a project with metadata.
    """
    project_id: str
    project_name: str
    epics: Dict[str, EpicState] = field(default_factory=dict)
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self):
        """Initialize default values for mutable fields"""
        if self.epics is None:
            self.epics = {}
        if self.last_updated is None:
            self.last_updated = datetime.utcnow().isoformat()


class StateManager:
    """State manager for AEDT projects

    Manages loading, saving, and validating project states with support for
    crash recovery and worktree validation.
    """

    def __init__(self, base_dir: Path, data_store: DataStore):
        """Initialize StateManager

        Args:
            base_dir: Base directory for AEDT data (.aedt/)
            data_store: DataStore instance for file operations
        """
        self.base_dir = base_dir
        self.data_store = data_store
        self.projects: Dict[str, ProjectState] = {}

    def load_all_states(self) -> Dict[str, ProjectState]:
        """Load all project states from disk

        Scans .aedt/projects/ directory and loads all status.yaml files.
        Validates each state and attempts recovery from backups if needed.

        Returns:
            Dictionary mapping project_id to ProjectState

        Side effects:
            - Populates self.projects with loaded states
            - May trigger crash recovery for 'developing' epics
            - May mark epics as 'requires_cleanup' if worktree invalid
        """
        projects_dir = self.base_dir / "projects"
        if not projects_dir.exists():
            logger.info("项目目录不存在，返回空状态")
            return {}

        loaded_count = 0
        error_count = 0

        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            state_file = project_dir / "status.yaml"
            if not state_file.exists():
                logger.debug(f"跳过无状态文件的项目目录: {project_dir}")
                continue

            try:
                # Try loading main state file
                data = self.data_store.read(state_file)
                project_state = self._parse_project_state(data)

                # Validate and possibly fix state
                validated_state = self._validate_state(project_state)
                self.projects[project_state.project_id] = validated_state
                loaded_count += 1

                logger.info(f"加载项目状态: {project_state.project_name} "
                           f"(ID: {project_state.project_id})")

            except Exception as e:
                error_count += 1
                logger.error(f"加载状态文件失败: {state_file}: {e}")

                # Try recovering from backup
                backup_files = sorted(
                    state_file.parent.glob(f"{state_file.stem}{state_file.suffix}.backup.*"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )

                if backup_files:
                    logger.info(f"尝试从备份恢复: {backup_files[0]}")
                    try:
                        data = self.data_store.read(backup_files[0])
                        project_state = self._parse_project_state(data)
                        self.projects[project_state.project_id] = project_state
                        logger.info(f"从备份恢复成功: {project_state.project_name}")
                        loaded_count += 1
                        error_count -= 1
                    except Exception as backup_error:
                        logger.error(f"备份恢复失败: {backup_error}")

        logger.info(f"状态加载完成: {loaded_count} 个项目成功, {error_count} 个失败")
        return self.projects

    def save_project_state(self, project_state: ProjectState) -> bool:
        """Save project state to disk

        Uses atomic write with automatic backup to ensure data integrity.

        Args:
            project_state: Project state to save

        Returns:
            True if save successful

        Raises:
            RuntimeError: If save fails
        """
        project_dir = self.base_dir / "projects" / project_state.project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        state_file = project_dir / "status.yaml"

        # Backup old state if exists
        if state_file.exists():
            self.data_store.backup(state_file)

        # Update timestamp
        project_state.last_updated = datetime.utcnow().isoformat()

        # Convert to dict (handle nested dataclasses)
        data = self._project_state_to_dict(project_state)

        # Atomic write
        try:
            self.data_store.atomic_write(state_file, data)
            # Update in-memory state
            self.projects[project_state.project_id] = project_state
            logger.info(f"保存项目状态: {project_state.project_name}")
            return True
        except Exception as e:
            logger.error(f"保存项目状态失败: {e}")
            raise

    def get_project_state(self, project_id: str) -> Optional[ProjectState]:
        """Get project state by ID

        Args:
            project_id: Project identifier

        Returns:
            ProjectState if found, None otherwise
        """
        return self.projects.get(project_id)

    def update_epic_state(
        self,
        project_id: str,
        epic_id: str,
        **kwargs
    ) -> bool:
        """Update epic state fields

        Args:
            project_id: Project identifier
            epic_id: Epic identifier
            **kwargs: Fields to update (e.g., status="completed", progress=100.0)

        Returns:
            True if update successful

        Raises:
            ValueError: If project or epic not found
        """
        project_state = self.projects.get(project_id)
        if not project_state:
            raise ValueError(f"项目不存在: {project_id}")

        epic_state = project_state.epics.get(epic_id)
        if not epic_state:
            raise ValueError(f"Epic 不存在: {epic_id} (项目: {project_id})")

        # Update fields
        for key, value in kwargs.items():
            if hasattr(epic_state, key):
                setattr(epic_state, key, value)
            else:
                logger.warning(f"忽略未知字段: {key}")

        # Update timestamps
        epic_state.last_updated = datetime.utcnow().isoformat()

        # Save
        return self.save_project_state(project_state)

    def _parse_project_state(self, data: dict) -> ProjectState:
        """Parse project state from dictionary

        Args:
            data: Raw project state data

        Returns:
            Parsed ProjectState object

        Raises:
            ValueError: If required fields are missing
        """
        if not data:
            raise ValueError("项目状态数据为空")

        required_fields = ['project_id', 'project_name']
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"缺少必需字段: {field_name}")

        # Parse epics
        epics = {}
        for epic_id, epic_data in data.get('epics', {}).items():
            epics[epic_id] = EpicState(**epic_data)

        return ProjectState(
            project_id=data['project_id'],
            project_name=data['project_name'],
            epics=epics,
            last_updated=data.get('last_updated')
        )

    def _validate_state(self, project_state: ProjectState) -> ProjectState:
        """Validate and fix project state

        Performs crash recovery and worktree validation:
        - 'developing' status → 'paused' (if worktree valid) or 'requires_cleanup' (if worktree invalid)
        - Invalid worktree paths → 'requires_cleanup' (only for non-terminal states)

        Args:
            project_state: Project state to validate

        Returns:
            Validated (possibly modified) project state
        """
        for epic_id, epic_state in project_state.epics.items():
            # Check crash recovery first
            crashed = epic_state.status == "developing"

            # Validate worktree path (skip for completed/failed epics)
            worktree_invalid = False
            if epic_state.worktree_path:
                worktree_path = Path(epic_state.worktree_path)
                if not worktree_path.exists():
                    logger.warning(
                        f"Worktree 不存在: {epic_state.worktree_path} "
                        f"(Epic: {epic_id})"
                    )
                    worktree_invalid = True
                    epic_state.worktree_path = None

            # Decide final status based on crash and worktree state
            if crashed:
                if worktree_invalid:
                    # Crashed AND worktree lost → needs cleanup before resume
                    epic_state.status = "requires_cleanup"
                    logger.info(
                        f"Epic {epic_id} 从崩溃中恢复，但 worktree 丢失，"
                        f"状态改为 'requires_cleanup'"
                    )
                else:
                    # Crashed but worktree OK → can resume
                    epic_state.status = "paused"
                    logger.info(
                        f"Epic {epic_id} 从崩溃中恢复，状态改为 'paused'"
                    )
            elif worktree_invalid and epic_state.status not in ["completed", "failed"]:
                # Not crashed, but worktree invalid (and not in terminal state)
                epic_state.status = "requires_cleanup"

        return project_state

    def _project_state_to_dict(self, project_state: ProjectState) -> dict:
        """Convert ProjectState to dictionary

        Handles nested EpicState dataclasses.

        Args:
            project_state: ProjectState to convert

        Returns:
            Dictionary representation
        """
        return {
            'project_id': project_state.project_id,
            'project_name': project_state.project_name,
            'last_updated': project_state.last_updated,
            'epics': {
                epic_id: asdict(epic_state)
                for epic_id, epic_state in project_state.epics.items()
            }
        }
