"""Domain layer exceptions."""
from typing import List, Optional


class CircularDependencyError(Exception):
    """Raised when circular dependency is detected in DAG."""

    ERROR_CODE = "DA001"

    def __init__(self, message: str, cycle_path: Optional[List[str]] = None):
        """
        Initialize CircularDependencyError.

        Args:
            message: Error message
            cycle_path: List of IDs forming the cycle
        """
        super().__init__(message)
        self.cycle_path = cycle_path or []


class InvalidDependencyError(Exception):
    """Raised when a dependency references a non-existent node."""

    ERROR_CODE = "DA002"

    def __init__(
        self, message: str, missing_epic_id: str, source_epic_id: Optional[str] = None
    ):
        """
        Initialize InvalidDependencyError.

        Args:
            message: Error message
            missing_epic_id: ID of the missing dependency
            source_epic_id: ID of the Epic that references the missing dependency
        """
        super().__init__(message)
        self.missing_epic_id = missing_epic_id
        self.source_epic_id = source_epic_id


class InvalidPrerequisiteError(Exception):
    """Raised when a Story prerequisite references a non-existent Story."""

    ERROR_CODE = "DA003"

    def __init__(
        self, message: str, invalid_prereq_id: str, story_id: Optional[str] = None
    ):
        """
        Initialize InvalidPrerequisiteError.

        Args:
            message: Error message
            invalid_prereq_id: ID of the invalid prerequisite
            story_id: ID of the Story that references the invalid prerequisite
        """
        super().__init__(message)
        self.invalid_prereq_id = invalid_prereq_id
        self.story_id = story_id
