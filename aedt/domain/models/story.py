"""Story domain model."""
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple


@dataclass
class Story:
    """Story domain model representing a task within an Epic."""

    id: str
    title: str
    description: str = ""
    prerequisites: List[str] = field(default_factory=list)
    status: str = "pending"  # pending/in-progress/completed/failed
    commit_hash: Optional[str] = None
    agent_id: Optional[str] = None

    def validate(self, epic_stories: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate Story data integrity.

        Args:
            epic_stories: Optional list of valid Story IDs in this Epic for prerequisite validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.id:
            return False, "Missing required field: id"
        if not self.title:
            return False, "Missing required field: title"

        # Validate Story ID format (X.Y)
        if '.' not in self.id:
            return False, f"Invalid Story ID format: {self.id}. Expected format: X.Y"

        # Validate status
        valid_statuses = ['pending', 'in-progress', 'completed', 'failed']
        if self.status not in valid_statuses:
            return False, f"Invalid status: {self.status}. Must be one of {valid_statuses}"

        # Validate prerequisites if epic_stories provided
        if epic_stories is not None and self.prerequisites:
            for prereq in self.prerequisites:
                if prereq not in epic_stories:
                    return False, f"Invalid prerequisite: {prereq} not in Epic story list"

        return True, None

    def has_unmet_prerequisites(self, completed_ids: Set[str]) -> bool:
        """
        Check if this Story has any unmet prerequisites.

        Args:
            completed_ids: Set of completed Story IDs

        Returns:
            True if there are unmet prerequisites, False otherwise
        """
        return any(prereq not in completed_ids for prereq in self.prerequisites)
