"""AEDT Logging System

This module provides structured logging with rotation, level filtering, and
separation between global and epic-specific logs.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict


class AEDTLogger:
    """AEDT logging system

    Provides structured logging with:
    - Global logger for all system operations
    - Epic-specific loggers for individual epic tracking
    - Log rotation (10MB max, 5 backups)
    - Level-based filtering (DEBUG/INFO/WARNING/ERROR)
    """

    def __init__(self, log_dir: Path, log_level: str = "INFO"):
        """Initialize AEDT logger

        Args:
            log_dir: Directory for log files (.aedt/logs/)
            log_level: Default log level (DEBUG/INFO/WARNING/ERROR)
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Parse log level
        try:
            self.log_level = getattr(logging, log_level.upper())
        except AttributeError:
            self.log_level = logging.INFO
            print(f"Warning: Invalid log level '{log_level}', defaulting to INFO")

        # Cache for loggers to avoid duplicates
        self._loggers: Dict[str, logging.Logger] = {}

        # Setup global logger
        self.global_logger = self._setup_logger(
            "aedt",
            self.log_dir / "aedt.log"
        )

    def _setup_logger(
        self,
        name: str,
        log_file: Path,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> logging.Logger:
        """Setup a logger with file handler and rotation

        Args:
            name: Logger name (e.g., "aedt", "aedt.epic.1")
            log_file: Log file path
            max_bytes: Maximum bytes per log file (default: 10MB)
            backup_count: Number of backup files to keep (default: 5)

        Returns:
            Configured logger instance
        """
        # Return cached logger if exists
        if name in self._loggers:
            return self._loggers[name]

        # Get or create logger
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)

        # Avoid adding duplicate handlers
        if logger.handlers:
            self._loggers[name] = logger
            return logger

        # Prevent propagation to avoid duplicate logs
        logger.propagate = False

        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)

        # Setup formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(file_handler)

        # Cache logger
        self._loggers[name] = logger

        return logger

    def get_logger(self, name: str) -> logging.Logger:
        """Get module logger

        Creates a logger for a specific module (e.g., "scheduler", "git").
        Module loggers write to the global log file.

        Args:
            name: Module name

        Returns:
            Logger instance for the module
        """
        logger_name = f"aedt.{name}"

        # Check if already exists
        if logger_name in self._loggers:
            return self._loggers[logger_name]

        # Create logger (will write to parent's handlers)
        logger = logging.getLogger(logger_name)
        logger.setLevel(self.log_level)

        # Cache it
        self._loggers[logger_name] = logger

        return logger

    def get_epic_logger(self, project_name: str, epic_id: str) -> logging.Logger:
        """Get epic-specific logger

        Creates a logger that writes to a separate file for the epic.
        Epic logs are stored in: .aedt/projects/{project}/epics/epic-{id}.log

        Args:
            project_name: Project name
            epic_id: Epic identifier

        Returns:
            Logger instance for the epic
        """
        logger_name = f"aedt.{project_name}.epic.{epic_id}"

        # Check if already exists
        if logger_name in self._loggers:
            return self._loggers[logger_name]

        # Determine epic log directory
        epic_log_dir = self.log_dir.parent / "projects" / project_name / "epics"
        epic_log_dir.mkdir(parents=True, exist_ok=True)

        # Setup epic-specific logger
        log_file = epic_log_dir / f"epic-{epic_id}.log"
        return self._setup_logger(logger_name, log_file)

    def set_level(self, level: str):
        """Change log level for all loggers

        Args:
            level: New log level (DEBUG/INFO/WARNING/ERROR)
        """
        try:
            new_level = getattr(logging, level.upper())
        except AttributeError:
            print(f"Warning: Invalid log level '{level}'")
            return

        self.log_level = new_level

        # Update all existing loggers
        for logger in self._loggers.values():
            logger.setLevel(new_level)
            for handler in logger.handlers:
                handler.setLevel(new_level)

    def close(self):
        """Close all loggers and handlers

        Should be called on application shutdown to ensure all logs are flushed.
        """
        for logger in self._loggers.values():
            for handler in logger.handlers:
                handler.close()
                logger.removeHandler(handler)

        self._loggers.clear()
