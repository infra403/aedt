"""Data Store for AEDT

This module provides atomic write operations and backup management for state files.
"""

from pathlib import Path
from typing import Any, Dict
import yaml
import tempfile
import shutil
import logging

logger = logging.getLogger(__name__)


class DataStore:
    """Data storage layer with atomic write operations

    Provides reliable file operations with atomic writes to prevent data corruption
    during crashes or failures.
    """

    def __init__(self, base_path: Path):
        """Initialize DataStore

        Args:
            base_path: Base directory for data storage
        """
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def atomic_write(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """Atomically write data to YAML file

        Uses temporary file + atomic rename to ensure file integrity.
        If write fails midway, the original file remains intact.

        Args:
            file_path: Target file path
            data: Data to write (will be serialized to YAML)

        Returns:
            True if write successful

        Raises:
            RuntimeError: If write fails
        """
        tmp_file_handle = None
        tmp_path = None

        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 1. Write to temporary file in same directory
            tmp_file_handle = tempfile.NamedTemporaryFile(
                mode='w',
                dir=file_path.parent,
                delete=False,
                suffix='.tmp',
                encoding='utf-8'
            )
            tmp_path = Path(tmp_file_handle.name)

            try:
                yaml.safe_dump(data, tmp_file_handle, default_flow_style=False,
                              allow_unicode=True, sort_keys=False)
            finally:
                tmp_file_handle.close()

            # 2. Atomic rename (POSIX guarantees atomicity)
            shutil.move(str(tmp_path), str(file_path))

            logger.debug(f"原子写入成功: {file_path}")
            return True

        except Exception as e:
            # Clean up temporary file on failure
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                    logger.debug(f"清理临时文件: {tmp_path}")
                except Exception as cleanup_error:
                    logger.warning(f"无法清理临时文件 {tmp_path}: {cleanup_error}")

            raise RuntimeError(f"写入失败 {file_path}: {e}")

    def read(self, file_path: Path) -> Dict[str, Any]:
        """Read data from YAML file

        Args:
            file_path: File path to read

        Returns:
            Parsed YAML data as dictionary

        Raises:
            ValueError: If file format is invalid
        """
        if not file_path.exists():
            logger.debug(f"文件不存在，返回空字典: {file_path}")
            return {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data if data is not None else {}
        except yaml.YAMLError as e:
            raise ValueError(f"文件格式错误: {file_path}\n{e}")

    def backup(self, file_path: Path, keep_count: int = 3) -> bool:
        """Create backup of file

        Creates a backup copy with .backup extension and rotates old backups.
        Keeps only the N most recent backups.

        Args:
            file_path: File to backup
            keep_count: Number of backups to keep (default: 3)

        Returns:
            True if backup created successfully, False if file doesn't exist
        """
        if not file_path.exists():
            logger.debug(f"文件不存在，跳过备份: {file_path}")
            return False

        try:
            # Create backup with high-precision timestamp
            import time
            timestamp = time.time()
            # Use microsecond precision to avoid collisions
            timestamp_str = f"{int(timestamp)}.{int((timestamp % 1) * 1000000)}"
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup.{timestamp_str}")
            shutil.copy2(file_path, backup_path)
            logger.debug(f"创建备份: {backup_path}")

            # Rotate old backups (keep only N most recent)
            backup_pattern = f"{file_path.stem}{file_path.suffix}.backup.*"
            backups = sorted(
                file_path.parent.glob(backup_pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True  # Most recent first
            )

            # Remove old backups beyond keep_count
            for old_backup in backups[keep_count:]:
                try:
                    old_backup.unlink()
                    logger.debug(f"删除旧备份: {old_backup}")
                except Exception as e:
                    logger.warning(f"无法删除旧备份 {old_backup}: {e}")

            return True

        except Exception as e:
            logger.error(f"备份失败 {file_path}: {e}")
            return False
