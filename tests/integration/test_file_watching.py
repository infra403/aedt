"""Integration tests for file watching functionality."""
import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from aedt.core.logger import AEDTLogger
from aedt.infrastructure.file_watcher import FileWatcher


@pytest.fixture
def logger(tmp_path):
    """Create test logger."""
    log_dir = tmp_path / ".aedt" / "logs"
    log_dir.mkdir(parents=True)
    return AEDTLogger(log_dir=log_dir, log_level="INFO")


@pytest.fixture
def watch_dir(tmp_path):
    """Create temporary directory to watch."""
    epics_dir = tmp_path / "docs" / "epics"
    epics_dir.mkdir(parents=True)
    return epics_dir


class TestFileWatchingIntegration:
    """Test file watching end-to-end (AC1, AC2)."""

    def test_detect_file_modification(self, watch_dir, logger):
        """Test detecting file modification and triggering callback (AC1)."""
        callback_mock = Mock()

        watcher = FileWatcher(
            str(watch_dir),
            callback_mock,
            logger,
            debounce_seconds=0.2
        )
        watcher.start()

        try:
            # Create and modify a file
            epic_file = watch_dir / "epic-002.md"
            epic_file.write_text("# Epic 2\n\nInitial content")

            # Wait for file creation event to process
            time.sleep(0.5)

            # Modify the file
            epic_file.write_text("# Epic 2\n\nModified content with new story")

            # Wait for modification event to process
            time.sleep(0.5)

            # Callback should have been called for both create and modify
            assert callback_mock.call_count >= 1

            # Verify it was called for our file
            calls = [call[0][0] for call in callback_mock.call_args_list]
            assert any(str(epic_file) in call for call in calls)

        finally:
            watcher.stop()

    def test_detect_new_epic_file(self, watch_dir, logger):
        """Test detecting new Epic file creation (AC2)."""
        callback_mock = Mock()

        watcher = FileWatcher(
            str(watch_dir),
            callback_mock,
            logger,
            debounce_seconds=0.2
        )
        watcher.start()

        try:
            # Create a new Epic file
            new_epic = watch_dir / "epic-009-new.md"
            new_epic.write_text("""---
epic_id: 9
title: "New Epic"
---

# Epic 9: New Epic
""")

            # Wait for event to process
            time.sleep(0.5)

            # Callback should have been called
            assert callback_mock.call_count >= 1

            # Verify file path in callbacks
            calls = [call[0][0] for call in callback_mock.call_args_list]
            assert any(str(new_epic) in call for call in calls)

        finally:
            watcher.stop()

    def test_debounce_prevents_duplicate_processing(self, watch_dir, logger):
        """Test debounce prevents duplicate processing (AC3)."""
        callback_mock = Mock()

        watcher = FileWatcher(
            str(watch_dir),
            callback_mock,
            logger,
            debounce_seconds=0.3
        )
        watcher.start()

        try:
            epic_file = watch_dir / "epic-003.md"
            epic_file.write_text("# Epic 3")

            # Wait for initial creation
            time.sleep(0.5)
            callback_mock.reset_mock()

            # Rapidly modify the same file 3 times within debounce window
            epic_file.write_text("# Epic 3\n\nChange 1")
            time.sleep(0.05)
            epic_file.write_text("# Epic 3\n\nChange 2")
            time.sleep(0.05)
            epic_file.write_text("# Epic 3\n\nChange 3")

            # Wait for debounce to trigger
            time.sleep(0.5)

            # Should only be called once (after debounce)
            assert callback_mock.call_count == 1

        finally:
            watcher.stop()

    def test_ignore_non_md_files(self, watch_dir, logger):
        """Test that non-.md files are ignored."""
        callback_mock = Mock()

        watcher = FileWatcher(
            str(watch_dir),
            callback_mock,
            logger,
            debounce_seconds=0.2
        )
        watcher.start()

        try:
            # Create non-.md file
            txt_file = watch_dir / "notes.txt"
            txt_file.write_text("Some notes")

            yaml_file = watch_dir / "config.yaml"
            yaml_file.write_text("key: value")

            # Wait
            time.sleep(0.5)

            # Callback should NOT have been called
            assert callback_mock.call_count == 0

        finally:
            watcher.stop()

    def test_watch_subdirectories(self, watch_dir, logger):
        """Test watching subdirectories recursively."""
        callback_mock = Mock()

        watcher = FileWatcher(
            str(watch_dir),
            callback_mock,
            logger,
            debounce_seconds=0.2
        )
        watcher.start()

        try:
            # Create subdirectory
            subdir = watch_dir / "archived"
            subdir.mkdir()

            # Create file in subdirectory
            epic_file = subdir / "epic-old.md"
            epic_file.write_text("# Old Epic")

            # Wait for event
            time.sleep(0.5)

            # Callback should have been called
            assert callback_mock.call_count >= 1

            # Verify file path
            calls = [call[0][0] for call in callback_mock.call_args_list]
            assert any(str(epic_file) in call for call in calls)

        finally:
            watcher.stop()
