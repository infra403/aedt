"""Unit tests for DataStore"""

import pytest
import tempfile
import shutil
from pathlib import Path
import yaml
import time

from aedt.core.data_store import DataStore


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    tmp_dir = Path(tempfile.mkdtemp())
    yield tmp_dir
    # Cleanup
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)


@pytest.fixture
def data_store(temp_dir):
    """Create DataStore instance for testing"""
    return DataStore(temp_dir)


def test_atomic_write_success(data_store, temp_dir):
    """Test successful atomic write"""
    file_path = temp_dir / "test.yaml"
    test_data = {
        'version': '1.0',
        'status': 'active',
        'count': 42
    }

    # Write data
    result = data_store.atomic_write(file_path, test_data)

    # Verify
    assert result is True
    assert file_path.exists()

    # Verify content
    with open(file_path, 'r') as f:
        loaded_data = yaml.safe_load(f)
    assert loaded_data == test_data


def test_atomic_write_creates_parent_directory(data_store, temp_dir):
    """Test that atomic_write creates parent directories"""
    nested_path = temp_dir / "nested" / "dir" / "test.yaml"
    test_data = {'key': 'value'}

    # Write data
    result = data_store.atomic_write(nested_path, test_data)

    # Verify
    assert result is True
    assert nested_path.exists()
    assert nested_path.parent.exists()


def test_atomic_write_failure_cleanup(data_store, temp_dir):
    """Test that temporary files are cleaned up on write failure"""
    file_path = temp_dir / "test.yaml"

    # Force an error by providing invalid data (un-serializable)
    class UnserializableClass:
        pass

    invalid_data = {'obj': UnserializableClass()}

    # Attempt write (should fail)
    with pytest.raises(RuntimeError, match="写入失败"):
        data_store.atomic_write(file_path, invalid_data)

    # Verify no temporary files left behind
    tmp_files = list(temp_dir.glob("*.tmp"))
    assert len(tmp_files) == 0, f"Temporary files not cleaned up: {tmp_files}"


def test_atomic_write_preserves_old_file_on_failure(data_store, temp_dir):
    """Test that old file remains intact if write fails"""
    file_path = temp_dir / "test.yaml"
    original_data = {'version': '1.0', 'status': 'original'}

    # Write initial data
    data_store.atomic_write(file_path, original_data)

    # Verify original data
    assert file_path.exists()
    with open(file_path, 'r') as f:
        assert yaml.safe_load(f) == original_data

    # Attempt to overwrite with invalid data
    class UnserializableClass:
        pass

    invalid_data = {'obj': UnserializableClass()}

    with pytest.raises(RuntimeError):
        data_store.atomic_write(file_path, invalid_data)

    # Verify original file still intact
    assert file_path.exists()
    with open(file_path, 'r') as f:
        assert yaml.safe_load(f) == original_data


def test_read_existing_file(data_store, temp_dir):
    """Test reading existing YAML file"""
    file_path = temp_dir / "test.yaml"
    test_data = {
        'project_id': 'test-001',
        'status': 'active',
        'items': ['a', 'b', 'c']
    }

    # Write test data
    with open(file_path, 'w') as f:
        yaml.safe_dump(test_data, f)

    # Read using DataStore
    loaded_data = data_store.read(file_path)

    # Verify
    assert loaded_data == test_data


def test_read_nonexistent_file(data_store, temp_dir):
    """Test reading nonexistent file returns empty dict"""
    file_path = temp_dir / "nonexistent.yaml"

    # Read
    data = data_store.read(file_path)

    # Verify
    assert data == {}


def test_read_invalid_yaml(data_store, temp_dir):
    """Test reading invalid YAML raises ValueError"""
    file_path = temp_dir / "invalid.yaml"

    # Write invalid YAML
    with open(file_path, 'w') as f:
        f.write("invalid: yaml: syntax: error:\n  - unclosed: [bracket")

    # Attempt read
    with pytest.raises(ValueError, match="文件格式错误"):
        data_store.read(file_path)


def test_backup_creates_backup_file(data_store, temp_dir):
    """Test backup creates backup file with timestamp"""
    file_path = temp_dir / "test.yaml"
    test_data = {'version': '1.0'}

    # Write initial data
    with open(file_path, 'w') as f:
        yaml.safe_dump(test_data, f)

    # Create backup
    result = data_store.backup(file_path)

    # Verify
    assert result is True

    # Check backup file exists
    backup_files = list(temp_dir.glob("test.yaml.backup.*"))
    assert len(backup_files) == 1

    # Verify backup content matches original
    with open(backup_files[0], 'r') as f:
        backup_data = yaml.safe_load(f)
    assert backup_data == test_data


def test_backup_rotation(data_store, temp_dir):
    """Test backup rotation keeps only N most recent backups"""
    file_path = temp_dir / "test.yaml"

    # Create initial file
    with open(file_path, 'w') as f:
        yaml.safe_dump({'version': '1.0'}, f)

    # Create multiple backups
    for i in range(5):
        time.sleep(0.01)  # Ensure different timestamps
        with open(file_path, 'w') as f:
            yaml.safe_dump({'version': f'1.{i}'}, f)
        data_store.backup(file_path, keep_count=3)

    # Verify only 3 backups remain
    backup_files = list(temp_dir.glob("test.yaml.backup.*"))
    assert len(backup_files) == 3

    # Verify most recent backups are kept
    backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for i, backup_file in enumerate(backup_files):
        with open(backup_file, 'r') as f:
            data = yaml.safe_load(f)
        # Most recent backups should have higher version numbers
        assert data['version'] in [f'1.{j}' for j in range(2, 5)]


def test_backup_nonexistent_file(data_store, temp_dir):
    """Test backup returns False for nonexistent file"""
    file_path = temp_dir / "nonexistent.yaml"

    # Attempt backup
    result = data_store.backup(file_path)

    # Verify
    assert result is False

    # Verify no backup files created
    backup_files = list(temp_dir.glob("*.backup.*"))
    assert len(backup_files) == 0


def test_atomic_write_with_unicode(data_store, temp_dir):
    """Test atomic write with Unicode characters"""
    file_path = temp_dir / "unicode.yaml"
    test_data = {
        'title': '项目状态',
        'description': '测试中文字符 🚀',
        'items': ['测试', 'テスト', '测试']
    }

    # Write data
    result = data_store.atomic_write(file_path, test_data)

    # Verify
    assert result is True

    # Verify content
    loaded_data = data_store.read(file_path)
    assert loaded_data == test_data
