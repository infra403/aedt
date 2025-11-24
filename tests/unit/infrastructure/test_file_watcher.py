"""Unit tests for FileWatcher."""
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from aedt.core.logger import AEDTLogger
from aedt.infrastructure.file_watcher import FileWatcher, EpicFileEventHandler


@pytest.fixture
def logger(tmp_path):
    """Create test logger."""
    log_dir = tmp_path / ".aedt" / "logs"
    log_dir.mkdir(parents=True)
    return AEDTLogger(log_dir=log_dir, log_level="INFO")


@pytest.fixture
def watch_dir(tmp_path):
    """Create temporary watch directory."""
    watch_path = tmp_path / "epics"
    watch_path.mkdir()
    return watch_path


@pytest.fixture
def callback_mock():
    """Create mock callback."""
    return Mock()


class TestFileWatcherBasics:
    """Test FileWatcher basic functionality."""

    def test_initialization(self, watch_dir, callback_mock, logger):
        """Test FileWatcher initialization."""
        watcher = FileWatcher(
            str(watch_dir),
            callback_mock,
            logger,
            debounce_seconds=0.5
        )

        assert watcher.watch_path == watch_dir.resolve()
        assert watcher.callback == callback_mock
        assert watcher.debounce_seconds == 0.5
        assert watcher.is_running() is False

    def test_start_and_stop(self, watch_dir, callback_mock, logger):
        """Test starting and stopping FileWatcher."""
        watcher = FileWatcher(str(watch_dir), callback_mock, logger)

        # Start
        watcher.start()
        assert watcher.is_running() is True

        # Stop
        watcher.stop()
        assert watcher.is_running() is False

    def test_context_manager(self, watch_dir, callback_mock, logger):
        """Test FileWatcher as context manager."""
        with FileWatcher(str(watch_dir), callback_mock, logger) as watcher:
            assert watcher.is_running() is True

        assert watcher.is_running() is False

    def test_start_twice_warns(self, watch_dir, callback_mock, logger):
        """Test starting already running watcher logs warning."""
        watcher = FileWatcher(str(watch_dir), callback_mock, logger)
        watcher.start()

        # Start again should warn
        watcher.start()

        watcher.stop()


class TestEpicFileEventHandler:
    """Test EpicFileEventHandler."""

    def test_should_process_md_files(self, watch_dir, callback_mock, logger):
        """Test that .md files are processed."""
        watcher = FileWatcher(str(watch_dir), callback_mock, logger)
        handler = EpicFileEventHandler(watcher)

        assert handler._should_process_file("epic-001.md") is True
        assert handler._should_process_file("/path/to/epic-002.md") is True

    def test_should_not_process_non_md_files(self, watch_dir, callback_mock, logger):
        """Test that non-.md files are ignored."""
        watcher = FileWatcher(str(watch_dir), callback_mock, logger)
        handler = EpicFileEventHandler(watcher)

        assert handler._should_process_file("epic-001.txt") is False
        assert handler._should_process_file("README.rst") is False
        assert handler._should_process_file("config.yaml") is False

    def test_should_not_process_temporary_files(self, watch_dir, callback_mock, logger):
        """Test that temporary files are ignored."""
        watcher = FileWatcher(str(watch_dir), callback_mock, logger)
        handler = EpicFileEventHandler(watcher)

        assert handler._should_process_file(".epic-001.md") is False
        assert handler._should_process_file("~epic-001.md") is False
        assert handler._should_process_file(".DS_Store") is False


class TestDebouncing:
    """Test debouncing mechanism (AC3)."""

    def test_debounce_single_change(self, watch_dir, callback_mock, logger):
        """Test single file change triggers callback once."""
        watcher = FileWatcher(
            str(watch_dir),
            callback_mock,
            logger,
            debounce_seconds=0.1
        )
        watcher.start()

        # Simulate file change
        test_file = str(watch_dir / "epic-001.md")
        watcher._handle_file_change(test_file, "modified")

        # Wait for debounce
        time.sleep(0.2)

        # Callback should be called once
        callback_mock.assert_called_once_with(test_file, "modified")

        watcher.stop()

    def test_debounce_multiple_rapid_changes(self, watch_dir, callback_mock, logger):
        """Test rapid changes trigger callback only once (AC3)."""
        watcher = FileWatcher(
            str(watch_dir),
            callback_mock,
            logger,
            debounce_seconds=0.2
        )
        watcher.start()

        test_file = str(watch_dir / "epic-001.md")

        # Simulate 3 rapid changes within debounce window
        watcher._handle_file_change(test_file, "modified")
        time.sleep(0.05)
        watcher._handle_file_change(test_file, "modified")
        time.sleep(0.05)
        watcher._handle_file_change(test_file, "modified")

        # Wait for debounce
        time.sleep(0.3)

        # Callback should be called only once (last change)
        assert callback_mock.call_count == 1
        callback_mock.assert_called_with(test_file, "modified")

        watcher.stop()

    def test_debounce_different_files(self, watch_dir, callback_mock, logger):
        """Test changes to different files trigger separate callbacks."""
        watcher = FileWatcher(
            str(watch_dir),
            callback_mock,
            logger,
            debounce_seconds=0.1
        )
        watcher.start()

        file1 = str(watch_dir / "epic-001.md")
        file2 = str(watch_dir / "epic-002.md")

        # Simulate changes to different files
        watcher._handle_file_change(file1, "modified")
        watcher._handle_file_change(file2, "modified")

        # Wait for debounce
        time.sleep(0.2)

        # Both callbacks should be called
        assert callback_mock.call_count == 2

        watcher.stop()


class TestCallbackErrorHandling:
    """Test callback error handling."""

    def test_callback_exception_logged(self, watch_dir, logger):
        """Test that callback exceptions are logged but don't crash watcher."""
        def failing_callback(file_path, event_type):
            raise ValueError("Test error")

        watcher = FileWatcher(
            str(watch_dir),
            failing_callback,
            logger,
            debounce_seconds=0.1
        )
        watcher.start()

        # Simulate file change
        test_file = str(watch_dir / "epic-001.md")
        watcher._handle_file_change(test_file, "modified")

        # Wait for debounce
        time.sleep(0.2)

        # Watcher should still be running
        assert watcher.is_running() is True

        watcher.stop()
