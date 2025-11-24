"""End-to-end integration tests for Epic parsing."""
import os
import tempfile
from pathlib import Path

import pytest

from aedt.core.config_manager import ConfigManager
from aedt.core.logger import AEDTLogger
from aedt.domain.epic_parser import EpicParser


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory with Epic files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create epics directory
        epics_dir = Path(tmpdir) / 'docs' / 'epics'
        epics_dir.mkdir(parents=True)

        # Create valid Epic file
        valid_epic = epics_dir / 'epic-001-foundation.md'
        valid_epic.write_text("""---
epic_id: 1
title: "Foundation"
depends_on: []
priority: HIGH
---

# Epic 1: Foundation
""")

        # Create another valid Epic with dependencies
        dependent_epic = epics_dir / 'epic-002-parsing.md'
        dependent_epic.write_text("""---
epic_id: 2
title: "Parsing"
depends_on: [1]
priority: MEDIUM
execution_mode: multi
story_concurrency: 3
---

# Epic 2: Parsing
""")

        # Create invalid Epic (missing epic_id)
        invalid_epic = epics_dir / 'epic-999-invalid.md'
        invalid_epic.write_text("""---
title: "Invalid Epic"
---

# Invalid
""")

        yield tmpdir


@pytest.fixture
def config_manager(temp_project_dir):
    """Create ConfigManager for testing."""
    config_dir = Path(temp_project_dir) / '.aedt'
    config_dir.mkdir()

    # Create a complete config file matching required schema
    config_file = config_dir / 'config.yaml'
    config_file.write_text("""
version: "1.0.0"
epic_docs_path: docs/epics/
epic_file_pattern: epic-*.md

subagent:
  max_concurrent: 5
  timeout: 3600
  model: claude-sonnet-4

quality_gates:
  pre_commit: []
  epic_complete: []
  pre_merge: []

git:
  worktree_base: ".aedt/worktrees"
  branch_prefix: "epic"
  auto_cleanup: true
""")

    config = ConfigManager(config_file)  # Pass config file path
    return config


@pytest.fixture
def logger(temp_project_dir):
    """Create AEDTLogger for testing."""
    log_dir = Path(temp_project_dir) / '.aedt' / 'logs'
    return AEDTLogger(log_dir=log_dir, log_level="INFO")


@pytest.fixture
def epic_parser(config_manager, logger):
    """Create EpicParser instance."""
    return EpicParser(config_manager, logger)


class TestEpicParsingE2E:
    """End-to-end tests for Epic parsing workflow."""

    def test_parse_project_with_multiple_epics(self, epic_parser, temp_project_dir):
        """Test parsing a project with multiple Epic files (AC1)."""
        epics = epic_parser.parse_epics(temp_project_dir)

        # Should parse 2 valid Epics (1 invalid will be skipped)
        assert len(epics) == 2

        # Verify Epic 1
        epic_1 = next((e for e in epics if e.id == "1"), None)
        assert epic_1 is not None
        assert epic_1.title == "Foundation"
        assert epic_1.depends_on == []
        assert epic_1.priority == "HIGH"

        # Verify Epic 2
        epic_2 = next((e for e in epics if e.id == "2"), None)
        assert epic_2 is not None
        assert epic_2.title == "Parsing"
        assert epic_2.depends_on == ["1"]
        assert epic_2.priority == "MEDIUM"
        assert epic_2.execution_mode == "multi"
        assert epic_2.story_concurrency == 3

    def test_invalid_epic_does_not_block_others(self, epic_parser, temp_project_dir):
        """Test that invalid Epic doesn't prevent parsing others (AC2)."""
        epics = epic_parser.parse_epics(temp_project_dir)

        # 2 valid Epics should still be parsed
        assert len(epics) == 2

        # Invalid Epic (999) should not be in results
        invalid_epic = next((e for e in epics if e.id == "999"), None)
        assert invalid_epic is None

    def test_epic_object_validation(self, epic_parser, temp_project_dir):
        """Test that parsed Epic objects are valid."""
        epics = epic_parser.parse_epics(temp_project_dir)

        for epic in epics:
            is_valid, error_msg = epic.validate()
            assert is_valid, f"Epic {epic.id} validation failed: {error_msg}"

    def test_empty_directory(self, epic_parser):
        """Test parsing an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            epics_dir = Path(tmpdir) / 'docs' / 'epics'
            epics_dir.mkdir(parents=True)

            epics = epic_parser.parse_epics(tmpdir)
            assert epics == []


class TestStoryParsingE2E:
    """End-to-end tests for Story parsing within Epics."""

    def test_parse_epic_with_numbered_stories_list(self, config_manager, logger, temp_project_dir):
        """Test parsing Epic with numbered Stories list (AC1)."""
        # Create Epic with numbered stories list
        epics_dir = Path(temp_project_dir) / 'docs' / 'epics'
        epic_file = epics_dir / 'epic-003-with-stories.md'
        epic_file.write_text("""---
epic_id: 3
title: "Epic with Stories"
depends_on: [1]
priority: HIGH
execution_mode: multi
story_concurrency: 3
---

# Epic 3: Epic with Stories

## Stories

1. Story 3.1: Parse Epic Documents and Extract Metadata
2. Story 3.2: Extract Story List from Epic Documents
3. Story 3.3: Build Epic Dependency DAG
""")

        parser = EpicParser(config_manager, logger)
        epics = parser.parse_epics(temp_project_dir)

        # Find Epic 3
        epic = next((e for e in epics if e.id == "3"), None)
        assert epic is not None
        assert len(epic.stories) == 3

        # Verify Story 3.1
        assert epic.stories[0].id == "3.1"
        assert epic.stories[0].title == "Parse Epic Documents and Extract Metadata"
        assert epic.stories[0].status == "pending"
        assert epic.stories[0].prerequisites == []

        # Verify Story 3.2
        assert epic.stories[1].id == "3.2"
        assert epic.stories[1].title == "Extract Story List from Epic Documents"

        # Verify Story 3.3
        assert epic.stories[2].id == "3.3"
        assert epic.stories[2].title == "Build Epic Dependency DAG"

    def test_parse_epic_with_story_headings_and_prerequisites(self, config_manager, logger, temp_project_dir):
        """Test parsing Epic with Story headings and prerequisites (AC2)."""
        epics_dir = Path(temp_project_dir) / 'docs' / 'epics'
        epic_file = epics_dir / 'epic-004-with-prereqs.md'
        epic_file.write_text("""---
epic_id: 4
title: "Epic with Prerequisites"
depends_on: [3]
priority: MEDIUM
---

# Epic 4: Epic with Prerequisites

### Story 4.1: Create Git Worktree

Create isolated git worktrees for Epic development.

### Story 4.2: Subagent Development in Worktree

Enable subagents to work in isolated worktrees.

Prerequisites: [4.1]

### Story 4.3: Auto-commit After Story Completion

Automatically commit changes after each story completes.

Requires Story 4.1 and Story 4.2
""")

        parser = EpicParser(config_manager, logger)
        epics = parser.parse_epics(temp_project_dir)

        # Find Epic 4
        epic = next((e for e in epics if e.id == "4"), None)
        assert epic is not None
        assert len(epic.stories) == 3

        # Verify Story 4.1
        assert epic.stories[0].id == "4.1"
        assert epic.stories[0].title == "Create Git Worktree"
        assert epic.stories[0].prerequisites == []

        # Verify Story 4.2 with YAML prerequisites
        assert epic.stories[1].id == "4.2"
        assert epic.stories[1].title == "Subagent Development in Worktree"
        assert "4.1" in epic.stories[1].prerequisites

        # Verify Story 4.3 with text reference prerequisites
        assert epic.stories[2].id == "4.3"
        assert epic.stories[2].title == "Auto-commit After Story Completion"
        assert "4.1" in epic.stories[2].prerequisites
        assert "4.2" in epic.stories[2].prerequisites

    def test_parse_epic_with_no_stories(self, config_manager, logger, temp_project_dir):
        """Test parsing Epic with no Stories section (AC3)."""
        epics_dir = Path(temp_project_dir) / 'docs' / 'epics'
        epic_file = epics_dir / 'epic-005-no-stories.md'
        epic_file.write_text("""---
epic_id: 5
title: "Epic without Stories"
depends_on: []
priority: LOW
---

# Epic 5: Epic without Stories

This Epic has no Stories defined yet.
""")

        parser = EpicParser(config_manager, logger)
        epics = parser.parse_epics(temp_project_dir)

        # Find Epic 5
        epic = next((e for e in epics if e.id == "5"), None)
        assert epic is not None
        assert len(epic.stories) == 0

    def test_story_validation_in_epic_context(self, config_manager, logger, temp_project_dir):
        """Test that Story validation works in Epic context."""
        epics_dir = Path(temp_project_dir) / 'docs' / 'epics'
        epic_file = epics_dir / 'epic-006-for-validation.md'
        epic_file.write_text("""---
epic_id: 6
title: "Epic for Story Validation"
depends_on: []
priority: HIGH
---

## Stories

1. Story 6.1: First Story
2. Story 6.2: Second Story
3. Story 6.3: Third Story
""")

        parser = EpicParser(config_manager, logger)
        epics = parser.parse_epics(temp_project_dir)

        epic = next((e for e in epics if e.id == "6"), None)
        assert epic is not None

        # Validate all stories
        epic_story_ids = [s.id for s in epic.stories]
        for story in epic.stories:
            is_valid, error_msg = story.validate(epic_story_ids)
            assert is_valid, f"Story {story.id} validation failed: {error_msg}"

    def test_mixed_story_formats_real_epic_file(self, epic_parser):
        """Test parsing real Epic fixture files with Stories."""
        # Use existing fixture files
        epic_list = epic_parser.parse_single_epic('tests/fixtures/epics/epic-with-stories-list.md')
        assert epic_list is not None
        assert len(epic_list.stories) == 3
        assert epic_list.stories[0].id == "3.1"
        assert epic_list.stories[1].id == "3.2"
        assert epic_list.stories[2].id == "3.3"

        epic_headings = epic_parser.parse_single_epic('tests/fixtures/epics/epic-with-stories-headings.md')
        assert epic_headings is not None
        assert len(epic_headings.stories) == 3
        assert epic_headings.stories[0].id == "4.1"
        assert epic_headings.stories[1].id == "4.2"
        assert epic_headings.stories[2].id == "4.3"

        # Verify prerequisites were extracted
        assert epic_headings.stories[1].prerequisites == ["4.1"]
        assert "4.1" in epic_headings.stories[2].prerequisites
        assert "4.2" in epic_headings.stories[2].prerequisites

        epic_no_stories = epic_parser.parse_single_epic('tests/fixtures/epics/epic-no-stories.md')
        assert epic_no_stories is not None
        assert len(epic_no_stories.stories) == 0
