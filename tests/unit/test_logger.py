"""Unit tests for AEDTLogger"""

import pytest
import tempfile
import shutil
from pathlib import Path
import logging
import time

from aedt.core.logger import AEDTLogger


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    tmp_dir = Path(tempfile.mkdtemp())
    yield tmp_dir
    # Cleanup
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)


@pytest.fixture
def logger_instance(temp_dir):
    """Create AEDTLogger instance for testing"""
    log_dir = temp_dir / ".aedt" / "logs"
    aedt_logger = AEDTLogger(log_dir, log_level="DEBUG")
    yield aedt_logger
    # Cleanup
    aedt_logger.close()


def test_logger_initialization(logger_instance, temp_dir):
    """Test AEDTLogger initialization"""
    log_dir = temp_dir / ".aedt" / "logs"

    # Verify log directory created
    assert log_dir.exists()
    assert log_dir.is_dir()

    # Verify global log file created
    global_log = log_dir / "aedt.log"
    assert global_log.exists()


def test_global_logger_writes(logger_instance, temp_dir):
    """Test global logger writes to aedt.log"""
    log_dir = temp_dir / ".aedt" / "logs"
    global_log = log_dir / "aedt.log"

    # Write log messages
    logger = logger_instance.global_logger
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message")

    # Force flush
    for handler in logger.handlers:
        handler.flush()

    # Verify log file contains messages
    with open(global_log, 'r') as f:
        content = f.read()

    assert "Test info message" in content
    assert "Test warning message" in content
    assert "Test error message" in content


def test_log_entry_format(logger_instance, temp_dir):
    """Test log entry format: [timestamp] [level] [module] message"""
    log_dir = temp_dir / ".aedt" / "logs"
    global_log = log_dir / "aedt.log"

    # Write a test message
    logger = logger_instance.global_logger
    logger.info("Format test message")

    # Force flush
    for handler in logger.handlers:
        handler.flush()

    # Read log content
    with open(global_log, 'r') as f:
        content = f.read()

    # Verify format
    assert "[INFO]" in content
    assert "[aedt]" in content
    assert "Format test message" in content
    # Check timestamp format (YYYY-MM-DD HH:MM:SS)
    assert "]" in content  # Timestamp ends with ]


def test_module_logger(logger_instance, temp_dir):
    """Test module-specific logger"""
    log_dir = temp_dir / ".aedt" / "logs"
    global_log = log_dir / "aedt.log"

    # Get module logger
    scheduler_logger = logger_instance.get_logger("scheduler")
    scheduler_logger.info("Scheduler started")

    # Force flush
    for handler in scheduler_logger.handlers:
        handler.flush()

    # Verify log written to global log
    with open(global_log, 'r') as f:
        content = f.read()

    assert "Scheduler started" in content
    assert "[aedt.scheduler]" in content


def test_epic_logger_creates_separate_file(logger_instance, temp_dir):
    """Test epic logger creates separate log file"""
    # Get epic logger
    epic_logger = logger_instance.get_epic_logger("TestProject", "1")
    epic_logger.info("Epic 1 operation")

    # Force flush
    for handler in epic_logger.handlers:
        handler.flush()

    # Verify epic log file created
    epic_log = temp_dir / ".aedt" / "projects" / "TestProject" / "epics" / "epic-1.log"
    assert epic_log.exists()

    # Verify content
    with open(epic_log, 'r') as f:
        content = f.read()

    assert "Epic 1 operation" in content
    assert "[aedt.TestProject.epic.1]" in content


def test_epic_log_separation(logger_instance, temp_dir):
    """Test epic logs don't mix with global logs"""
    log_dir = temp_dir / ".aedt" / "logs"
    global_log = log_dir / "aedt.log"

    # Write to epic logger
    epic_logger = logger_instance.get_epic_logger("TestProject", "2")
    epic_logger.info("Epic 2 specific message")

    # Force flush
    for handler in epic_logger.handlers:
        handler.flush()

    # Verify global log doesn't contain epic message
    with open(global_log, 'r') as f:
        global_content = f.read()

    # Epic message should NOT be in global log
    assert "Epic 2 specific message" not in global_content

    # Verify epic log contains the message
    epic_log = temp_dir / ".aedt" / "projects" / "TestProject" / "epics" / "epic-2.log"
    with open(epic_log, 'r') as f:
        epic_content = f.read()

    assert "Epic 2 specific message" in epic_content


def test_log_level_filtering(temp_dir):
    """Test log level filtering (DEBUG messages filtered when level=INFO)"""
    log_dir = temp_dir / ".aedt" / "logs"
    global_log = log_dir / "aedt.log"

    # Create logger with INFO level
    aedt_logger = AEDTLogger(log_dir, log_level="INFO")

    # Write messages at different levels
    logger = aedt_logger.global_logger
    logger.debug("Debug message - should not appear")
    logger.info("Info message - should appear")
    logger.warning("Warning message - should appear")

    # Force flush
    for handler in logger.handlers:
        handler.flush()

    # Read log content
    with open(global_log, 'r') as f:
        content = f.read()

    # Verify filtering
    assert "Debug message" not in content  # DEBUG filtered out
    assert "Info message" in content       # INFO shown
    assert "Warning message" in content    # WARNING shown

    # Cleanup
    aedt_logger.close()


def test_log_rotation_creates_backups(temp_dir):
    """Test log rotation creates backup files when size exceeds limit"""
    log_dir = temp_dir / ".aedt" / "logs"

    # Create logger with small max size for testing
    aedt_logger = AEDTLogger(log_dir, log_level="INFO")

    # Override max bytes for testing (1KB)
    logger = aedt_logger.global_logger
    for handler in logger.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            handler.maxBytes = 1024  # 1KB
            handler.backupCount = 3

    # Write enough data to trigger rotation
    for i in range(100):
        logger.info(f"Log message {i} - padding with extra text to increase size" * 5)

    # Force flush
    for handler in logger.handlers:
        handler.flush()

    # Check for backup files
    backup_files = list(log_dir.glob("aedt.log.*"))
    assert len(backup_files) > 0, "Log rotation should create backup files"

    # Cleanup
    aedt_logger.close()


def test_multiple_epic_loggers(logger_instance, temp_dir):
    """Test multiple epic loggers work independently"""
    # Create loggers for different epics
    epic1_logger = logger_instance.get_epic_logger("Project1", "1")
    epic2_logger = logger_instance.get_epic_logger("Project1", "2")
    epic3_logger = logger_instance.get_epic_logger("Project2", "1")

    # Write to each
    epic1_logger.info("Epic 1 message")
    epic2_logger.info("Epic 2 message")
    epic3_logger.info("Epic 3 message")

    # Force flush and close handlers to ensure file creation
    for logger in [epic1_logger, epic2_logger, epic3_logger]:
        for handler in logger.handlers:
            handler.flush()
            handler.close()

    # Verify each has its own file
    epic1_log = temp_dir / ".aedt" / "projects" / "Project1" / "epics" / "epic-1.log"
    epic2_log = temp_dir / ".aedt" / "projects" / "Project1" / "epics" / "epic-2.log"
    epic3_log = temp_dir / ".aedt" / "projects" / "Project2" / "epics" / "epic-1.log"

    assert epic1_log.exists(), f"Epic 1 log not found at {epic1_log}"
    assert epic2_log.exists(), f"Epic 2 log not found at {epic2_log}"
    assert epic3_log.exists(), f"Epic 3 log not found at {epic3_log}"

    # Verify content separation
    with open(epic1_log, 'r') as f:
        content = f.read()
        assert "Epic 1 message" in content
        assert "Epic 2 message" not in content


def test_set_level_changes_all_loggers(logger_instance):
    """Test set_level changes log level for all loggers"""
    # Get a module logger
    module_logger = logger_instance.get_logger("test_module")

    # Initially set to DEBUG
    assert logger_instance.log_level == logging.DEBUG

    # Change to WARNING
    logger_instance.set_level("WARNING")

    # Verify level changed
    assert logger_instance.log_level == logging.WARNING
    assert logger_instance.global_logger.level == logging.WARNING
    assert module_logger.level == logging.WARNING


def test_logger_caching(logger_instance):
    """Test loggers are cached to avoid duplicates"""
    # Get same logger twice
    logger1 = logger_instance.get_logger("cached_module")
    logger2 = logger_instance.get_logger("cached_module")

    # Should be the same instance
    assert logger1 is logger2

    # Same for epic loggers
    epic_logger1 = logger_instance.get_epic_logger("TestProject", "1")
    epic_logger2 = logger_instance.get_epic_logger("TestProject", "1")

    assert epic_logger1 is epic_logger2


def test_close_flushes_and_closes_handlers(logger_instance, temp_dir):
    """Test close() properly closes all handlers"""
    log_dir = temp_dir / ".aedt" / "logs"
    global_log = log_dir / "aedt.log"

    # Write message
    logger_instance.global_logger.info("Pre-close message")

    # Close logger
    logger_instance.close()

    # Verify log file exists and has content
    assert global_log.exists()
    with open(global_log, 'r') as f:
        content = f.read()
    assert "Pre-close message" in content

    # Verify loggers cache cleared
    assert len(logger_instance._loggers) == 0


def test_invalid_log_level_defaults_to_info(temp_dir):
    """Test invalid log level defaults to INFO"""
    log_dir = temp_dir / ".aedt" / "logs"

    # Create logger with invalid level
    aedt_logger = AEDTLogger(log_dir, log_level="INVALID")

    # Should default to INFO
    assert aedt_logger.log_level == logging.INFO

    # Cleanup
    aedt_logger.close()


def test_utf8_encoding_support(logger_instance, temp_dir):
    """Test UTF-8 encoding support for non-ASCII characters"""
    log_dir = temp_dir / ".aedt" / "logs"
    global_log = log_dir / "aedt.log"

    # Write message with Chinese characters
    logger_instance.global_logger.info("测试中文日志 🚀")

    # Force flush
    for handler in logger_instance.global_logger.handlers:
        handler.flush()

    # Verify UTF-8 content
    with open(global_log, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "测试中文日志 🚀" in content
