"""Epic domain model."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .story import Story


@dataclass
class Epic:
    """Epic domain model representing a BMAD Epic document."""

    id: str
    title: str
    description: str = ""
    depends_on: List[str] = field(default_factory=list)
    priority: str = "MEDIUM"  # HIGH/MEDIUM/LOW
    execution_mode: str = "auto"  # single/multi/auto
    story_concurrency: int = 3
    stories: List['Story'] = field(default_factory=list)  # List of Story objects
    status: str = "backlog"  # backlog/contexted/developing/completed/failed
    progress: float = 0.0
    agent_id: Optional[str] = None
    worktree_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate Epic data integrity.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.id:
            return False, "Missing required field: id"
        if not self.title:
            return False, "Missing required field: title"

        # Validate priority
        if self.priority not in ['HIGH', 'MEDIUM', 'LOW']:
            return False, f"Invalid priority: {self.priority}. Must be HIGH/MEDIUM/LOW"

        # Validate execution_mode
        if self.execution_mode not in ['single', 'multi', 'auto']:
            return False, f"Invalid execution_mode: {self.execution_mode}. Must be single/multi/auto"

        # Validate story_concurrency
        if self.story_concurrency < 1:
            return False, f"Invalid story_concurrency: {self.story_concurrency}. Must be >= 1"

        return True, None
