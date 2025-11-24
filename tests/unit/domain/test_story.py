"""Unit tests for Story model."""
import pytest

from aedt.domain.models.story import Story


class TestStoryModel:
    """Test Story domain model."""

    def test_story_creation_minimal(self):
        """Test creating a Story with minimal required fields."""
        story = Story(
            id="3.1",
            title="Parse Epic Documents"
        )

        assert story.id == "3.1"
        assert story.title == "Parse Epic Documents"
        assert story.description == ""
        assert story.prerequisites == []
        assert story.status == "pending"
        assert story.commit_hash is None
        assert story.agent_id is None

    def test_story_creation_complete(self):
        """Test creating a Story with all fields."""
        story = Story(
            id="3.2",
            title="Extract Stories",
            description="Extract story list from Epic content",
            prerequisites=["3.1"],
            status="in-progress",
            commit_hash="abc123",
            agent_id="agent-1"
        )

        assert story.id == "3.2"
        assert story.title == "Extract Stories"
        assert story.description == "Extract story list from Epic content"
        assert story.prerequisites == ["3.1"]
        assert story.status == "in-progress"
        assert story.commit_hash == "abc123"
        assert story.agent_id == "agent-1"


class TestStoryValidation:
    """Test Story validation method."""

    def test_validate_complete_story(self):
        """Test validating a complete valid Story."""
        story = Story(
            id="3.1",
            title="Parse Epic Documents"
        )
        is_valid, error_msg = story.validate()

        assert is_valid is True
        assert error_msg is None

    def test_validate_missing_id(self):
        """Test validation fails when id is missing."""
        story = Story(
            id="",
            title="Test Story"
        )
        is_valid, error_msg = story.validate()

        assert is_valid is False
        assert "id" in error_msg.lower()

    def test_validate_missing_title(self):
        """Test validation fails when title is missing."""
        story = Story(
            id="3.1",
            title=""
        )
        is_valid, error_msg = story.validate()

        assert is_valid is False
        assert "title" in error_msg.lower()

    def test_validate_invalid_id_format(self):
        """Test validation fails with invalid Story ID format."""
        story = Story(
            id="invalid",  # Missing the X.Y format
            title="Test Story"
        )
        is_valid, error_msg = story.validate()

        assert is_valid is False
        assert "format" in error_msg.lower()

    def test_validate_invalid_status(self):
        """Test validation fails with invalid status."""
        story = Story(
            id="3.1",
            title="Test Story",
            status="invalid_status"
        )
        is_valid, error_msg = story.validate()

        assert is_valid is False
        assert "status" in error_msg.lower()

    def test_validate_prerequisites_valid(self):
        """Test validation succeeds with valid prerequisites."""
        story = Story(
            id="3.3",
            title="Test Story",
            prerequisites=["3.1", "3.2"]
        )
        epic_stories = ["3.1", "3.2", "3.3"]
        is_valid, error_msg = story.validate(epic_stories)

        assert is_valid is True
        assert error_msg is None

    def test_validate_prerequisites_invalid(self):
        """Test validation fails when prerequisite doesn't exist in Epic."""
        story = Story(
            id="3.3",
            title="Test Story",
            prerequisites=["3.1", "3.9"]  # 3.9 doesn't exist
        )
        epic_stories = ["3.1", "3.2", "3.3"]
        is_valid, error_msg = story.validate(epic_stories)

        assert is_valid is False
        assert "prerequisite" in error_msg.lower()
        assert "3.9" in error_msg

    def test_validate_prerequisites_without_epic_list(self):
        """Test validation skips prerequisite check when epic_stories not provided."""
        story = Story(
            id="3.3",
            title="Test Story",
            prerequisites=["3.9"]  # Would be invalid if checked
        )
        is_valid, error_msg = story.validate()  # No epic_stories provided

        # Should still pass since we're not validating prerequisites
        assert is_valid is True
        assert error_msg is None

    def test_validate_all_statuses(self):
        """Test all valid status values."""
        valid_statuses = ['pending', 'in-progress', 'completed', 'failed']

        for status in valid_statuses:
            story = Story(
                id="3.1",
                title="Test Story",
                status=status
            )
            is_valid, error_msg = story.validate()

            assert is_valid is True, f"Status '{status}' should be valid"
            assert error_msg is None
