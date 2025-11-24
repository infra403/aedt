"""File watching infrastructure for Epic file change detection."""
import os
import time
from pathlib import Path
from threading import Timer
from typing import Callable, Dict, Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from aedt.core.logger import AEDTLogger


class EpicFileEventHandler(FileSystemEventHandler):
    """Event handler for Epic file changes."""

    def __init__(self, file_watcher: "FileWatcher"):
        """
        Initialize event handler.

        Args:
            file_watcher: Parent FileWatcher instance
        """
        super().__init__()
        self.file_watcher = file_watcher

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = event.src_path
        if self._should_process_file(file_path):
            self.file_watcher._handle_file_change(file_path, "modified")

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = event.src_path
        if self._should_process_file(file_path):
            self.file_watcher._handle_file_change(file_path, "created")

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if event.is_directory:
            return

        file_path = event.src_path
        if self._should_process_file(file_path):
            self.file_watcher._handle_file_change(file_path, "deleted")

    def _should_process_file(self, file_path: str) -> bool:
        """
        Check if file should be processed.

        Args:
            file_path: Path to the file

        Returns:
            True if file should be processed
        """
        # Only process .md files
        if not file_path.endswith('.md'):
            return False

        # Ignore temporary files
        filename = os.path.basename(file_path)
        if filename.startswith('.') or filename.startswith('~'):
            return False

        return True


class FileWatcher:
    """Watches for file changes and triggers callbacks with debouncing."""

    def __init__(
        self,
        watch_path: str,
        callback: Callable[[str, str], None],
        logger: AEDTLogger,
        debounce_seconds: float = 1.0,
    ):
        """
        Initialize FileWatcher.

        Args:
            watch_path: Directory path to monitor
            callback: Function to call on file changes, signature: callback(file_path, event_type)
            logger: AEDTLogger instance
            debounce_seconds: Debounce delay in seconds
        """
        self.watch_path = Path(watch_path).resolve()
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.aedt_logger = logger
        self.logger = logger.get_logger("file_watcher")

        self.observer: Optional[Observer] = None
        self.pending_events: Dict[str, Timer] = {}
        self._running = False

    def start(self) -> None:
        """Start file watching."""
        if self._running:
            self.logger.warning("FileWatcher already running")
            return

        try:
            self.observer = Observer()
            event_handler = EpicFileEventHandler(self)
            self.observer.schedule(event_handler, str(self.watch_path), recursive=True)
            self.observer.start()
            self._running = True

            self.logger.info(f"Started monitoring {self.watch_path} for changes")
        except Exception as e:
            self.logger.error(f"Failed to start file watching: {e}")
            raise

    def stop(self) -> None:
        """Stop file watching and cleanup."""
        if not self._running:
            return

        try:
            # Stop observer
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)

            # Cancel pending timers
            for timer in self.pending_events.values():
                timer.cancel()
            self.pending_events.clear()

            self._running = False
            self.logger.info("Stopped monitoring")
        except Exception as e:
            self.logger.error(f"Error stopping file watcher: {e}")

    def is_running(self) -> bool:
        """Check if file watcher is running."""
        return self._running

    def _handle_file_change(self, file_path: str, event_type: str) -> None:
        """
        Handle file change event with debouncing.

        Args:
            file_path: Path to the changed file
            event_type: Type of event (modified, created, deleted)
        """
        self.logger.debug(f"File event: {file_path} {event_type}")
        self._debounce(file_path, event_type)

    def _debounce(self, file_path: str, event_type: str) -> None:
        """
        Debounce file change events.

        Args:
            file_path: Path to the changed file
            event_type: Type of event
        """
        # Cancel previous timer for this file
        if file_path in self.pending_events:
            self.pending_events[file_path].cancel()
            self.logger.debug(f"Cancelled previous timer for {file_path}")

        # Create new timer
        timer = Timer(
            self.debounce_seconds,
            self._trigger_callback,
            args=[file_path, event_type]
        )
        self.pending_events[file_path] = timer
        timer.start()

        self.logger.debug(
            f"Debounce timer set for {file_path} ({self.debounce_seconds}s)"
        )

    def _trigger_callback(self, file_path: str, event_type: str) -> None:
        """
        Trigger the callback after debounce delay.

        Args:
            file_path: Path to the changed file
            event_type: Type of event
        """
        # Remove from pending
        if file_path in self.pending_events:
            del self.pending_events[file_path]

        try:
            self.logger.info(f"Detected {event_type} in {file_path}")
            self.callback(file_path, event_type)
        except Exception as e:
            self.logger.error(
                f"Error in file change callback for {file_path}: {e}",
                exc_info=True
            )

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
