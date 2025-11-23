"""Unit tests for ConfigManager"""

import pytest
import tempfile
import yaml
import time
from pathlib import Path
from aedt.core.config_manager import (
    ConfigManager,
    AEDTConfig,
    SubagentConfig,
    QualityGatesConfig,
    GitConfig,
    ConfigFileHandler
)


class TestConfigManager:
    """Test suite for ConfigManager"""

    def test_initialize_creates_directories(self, tmp_path):
        """Test that initialize creates all required directories"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)

        # Act
        result = config_mgr.initialize(force=False, is_global=False)

        # Assert
        assert result is True
        assert (tmp_path / ".aedt").exists()
        assert (tmp_path / ".aedt" / "logs").exists()
        assert (tmp_path / ".aedt" / "projects").exists()
        assert (tmp_path / ".aedt" / "worktrees").exists()

    def test_initialize_creates_config_file(self, tmp_path):
        """Test that initialize creates config.yaml with default settings"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)

        # Act
        config_mgr.initialize(force=False, is_global=False)

        # Assert
        assert config_path.exists()

        # Verify config content
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        assert config_data['version'] == "1.0"
        assert config_data['subagent']['max_concurrent'] == 5
        assert config_data['quality_gates']['pre_commit'] == ["lint", "format_check"]
        assert config_data['git']['worktree_base'] == ".aedt/worktrees"

    def test_initialize_overwrite_protection(self, tmp_path):
        """Test that initialize raises error if config exists without --force"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)

        # Act & Assert
        with pytest.raises(RuntimeError, match="配置文件已存在"):
            config_mgr.initialize(force=False, is_global=False)

    def test_initialize_force_overwrite(self, tmp_path):
        """Test that initialize overwrites existing config with --force"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)

        # Modify config
        config_path.write_text("modified: true", encoding='utf-8')

        # Act
        config_mgr.initialize(force=True, is_global=False)

        # Assert
        content = config_path.read_text(encoding='utf-8')
        assert "modified: true" not in content
        assert "version:" in content

    def test_load_config(self, tmp_path):
        """Test loading valid configuration file"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)

        # Act
        config = config_mgr.load()

        # Assert
        assert isinstance(config, AEDTConfig)
        assert config.version == "1.0"
        assert config.subagent.max_concurrent == 5
        assert config.git.worktree_base == ".aedt/worktrees"

    def test_load_invalid_yaml(self, tmp_path):
        """Test loading config file with invalid YAML syntax"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("invalid: yaml: syntax:", encoding='utf-8')

        config_mgr = ConfigManager(config_path=config_path)

        # Act & Assert
        with pytest.raises(ValueError, match="YAML 格式错误"):
            config_mgr.load()

    def test_load_missing_fields(self, tmp_path):
        """Test loading config file with missing required fields"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("version: '1.0'\n", encoding='utf-8')

        config_mgr = ConfigManager(config_path=config_path)

        # Act & Assert
        with pytest.raises(ValueError, match="缺少必需字段"):
            config_mgr.load()

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading non-existent config file"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="配置文件不存在"):
            config_mgr.load()

    def test_ensure_directory_success(self, tmp_path):
        """Test _ensure_directory creates directory successfully"""
        # Arrange
        config_mgr = ConfigManager()
        test_dir = tmp_path / "test_dir"

        # Act
        result = config_mgr._ensure_directory(test_dir)

        # Assert
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_directory_permission_error(self, tmp_path, monkeypatch):
        """Test _ensure_directory handles permission errors"""
        # Arrange
        config_mgr = ConfigManager()
        test_dir = tmp_path / "test_dir"

        # Mock mkdir to raise PermissionError
        def mock_mkdir(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(Path, "mkdir", mock_mkdir)

        # Act
        result = config_mgr._ensure_directory(test_dir)

        # Assert
        assert result is False

    def test_get_config_value(self, tmp_path):
        """Test getting configuration values"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)
        config_mgr.load()

        # Act
        version = config_mgr.get('version')
        subagent = config_mgr.get('subagent')
        nonexistent = config_mgr.get('nonexistent', 'default')

        # Assert
        assert version == "1.0"
        assert subagent.max_concurrent == 5
        assert nonexistent == 'default'

    def test_get_nested_config_value(self, tmp_path):
        """Test getting nested configuration values using dot notation"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)
        config_mgr.load()

        # Act
        max_concurrent = config_mgr.get('subagent.max_concurrent')
        timeout = config_mgr.get('subagent.timeout')
        model = config_mgr.get('subagent.model')
        worktree_base = config_mgr.get('git.worktree_base')
        nonexistent = config_mgr.get('subagent.nonexistent', 99)

        # Assert
        assert max_concurrent == 5
        assert timeout == 3600
        assert model == "claude-sonnet-4"
        assert worktree_base == ".aedt/worktrees"
        assert nonexistent == 99

    def test_save_config(self, tmp_path):
        """Test saving configuration to file"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)
        config = config_mgr.load()

        # Modify config
        config.subagent.max_concurrent = 10
        config.git.auto_cleanup = False

        # Act
        config_mgr.save_config(config)

        # Assert
        config_mgr2 = ConfigManager(config_path=config_path)
        loaded_config = config_mgr2.load()
        assert loaded_config.subagent.max_concurrent == 10
        assert loaded_config.git.auto_cleanup is False

    def test_save_config_creates_directory(self, tmp_path):
        """Test that save_config creates parent directory if needed"""
        # Arrange
        config_path = tmp_path / "new" / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)

        config = AEDTConfig(
            version="1.0",
            subagent=SubagentConfig(),
            quality_gates=QualityGatesConfig(),
            git=GitConfig()
        )

        # Act
        config_mgr.save_config(config)

        # Assert
        assert config_path.exists()
        assert config_path.parent.exists()

    def test_save_config_without_loaded_config(self, tmp_path):
        """Test saving config raises error when no config loaded"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)

        # Act & Assert
        with pytest.raises(ValueError, match="没有配置可保存"):
            config_mgr.save_config()

    def test_validate_empty_config(self, tmp_path):
        """Test validation fails for empty config file"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("", encoding='utf-8')

        config_mgr = ConfigManager(config_path=config_path)

        # Act & Assert
        with pytest.raises(ValueError, match="配置文件为空"):
            config_mgr.load()

    def test_validate_invalid_version_type(self, tmp_path):
        """Test validation fails when version is not a string"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config_data = {
            'version': 1,  # Should be string
            'subagent': {'max_concurrent': 5},
            'quality_gates': {},
            'git': {}
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        config_mgr = ConfigManager(config_path=config_path)

        # Act & Assert
        with pytest.raises(ValueError, match="version 必须是字符串类型"):
            config_mgr.load()

    def test_validate_invalid_max_concurrent_type(self, tmp_path):
        """Test validation fails when max_concurrent is not an integer"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config_data = {
            'version': '1.0',
            'subagent': {'max_concurrent': '5'},  # Should be int
            'quality_gates': {},
            'git': {}
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        config_mgr = ConfigManager(config_path=config_path)

        # Act & Assert
        with pytest.raises(ValueError, match="max_concurrent 必须是整数类型"):
            config_mgr.load()

    def test_validate_invalid_max_concurrent_value(self, tmp_path):
        """Test validation fails when max_concurrent is <= 0"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config_data = {
            'version': '1.0',
            'subagent': {'max_concurrent': 0},  # Should be > 0
            'quality_gates': {},
            'git': {}
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        config_mgr = ConfigManager(config_path=config_path)

        # Act & Assert
        with pytest.raises(ValueError, match="max_concurrent 必须大于 0"):
            config_mgr.load()

    def test_validate_invalid_timeout_type(self, tmp_path):
        """Test validation fails when timeout is not an integer"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config_data = {
            'version': '1.0',
            'subagent': {'timeout': '3600'},  # Should be int
            'quality_gates': {},
            'git': {}
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        config_mgr = ConfigManager(config_path=config_path)

        # Act & Assert
        with pytest.raises(ValueError, match="timeout 必须是整数类型"):
            config_mgr.load()

    def test_validate_invalid_timeout_value(self, tmp_path):
        """Test validation fails when timeout is <= 0"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config_data = {
            'version': '1.0',
            'subagent': {'timeout': -1},  # Should be > 0
            'quality_gates': {},
            'git': {}
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        config_mgr = ConfigManager(config_path=config_path)

        # Act & Assert
        with pytest.raises(ValueError, match="timeout 必须大于 0"):
            config_mgr.load()

    def test_validate_invalid_quality_gates_type(self, tmp_path):
        """Test validation fails when quality_gates is not a dict"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config_data = {
            'version': '1.0',
            'subagent': {},
            'quality_gates': 'not-a-dict',  # Should be dict
            'git': {}
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        config_mgr = ConfigManager(config_path=config_path)

        # Act & Assert
        with pytest.raises(ValueError, match="quality_gates 必须是对象类型"):
            config_mgr.load()

    def test_validate_invalid_quality_gate_list_type(self, tmp_path):
        """Test validation fails when quality gate list is not a list"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config_data = {
            'version': '1.0',
            'subagent': {},
            'quality_gates': {'pre_commit': 'not-a-list'},  # Should be list
            'git': {}
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        config_mgr = ConfigManager(config_path=config_path)

        # Act & Assert
        with pytest.raises(ValueError, match="pre_commit 必须是列表类型"):
            config_mgr.load()

    def test_reload_config(self, tmp_path):
        """Test reloading configuration"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)
        config_mgr.load()

        # Modify config file
        config_data = {
            'version': '1.0',
            'subagent': {'max_concurrent': 10, 'timeout': 3600, 'model': 'claude-sonnet-4'},
            'quality_gates': {'pre_commit': [], 'epic_complete': [], 'pre_merge': []},
            'git': {'worktree_base': '.aedt/worktrees', 'branch_prefix': 'epic', 'auto_cleanup': True}
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        # Act
        config_mgr.reload_config()

        # Assert
        assert config_mgr.config.subagent.max_concurrent == 10

    def test_reload_config_preserves_old_on_error(self, tmp_path):
        """Test that reload_config preserves old config on validation error"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)
        config_mgr.load()
        old_max_concurrent = config_mgr.config.subagent.max_concurrent

        # Write invalid config
        config_path.write_text("invalid: yaml: syntax:", encoding='utf-8')

        # Act
        config_mgr.reload_config()

        # Assert - old config should be preserved
        assert config_mgr.config.subagent.max_concurrent == old_max_concurrent

    def test_hot_reload_enable(self, tmp_path):
        """Test enabling hot reload"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)

        # Act
        config_mgr.enable_hot_reload()

        # Assert
        assert config_mgr._observer is not None
        assert config_mgr._observer.is_alive()

        # Cleanup
        config_mgr.stop_watching()

    def test_hot_reload_stop(self, tmp_path):
        """Test stopping hot reload"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)
        config_mgr.enable_hot_reload()

        # Act
        config_mgr.stop_watching()

        # Assert
        assert config_mgr._observer is None

    def test_hot_reload_enable_twice(self, tmp_path):
        """Test that enabling hot reload twice does not create multiple observers"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)
        config_mgr.enable_hot_reload()
        first_observer = config_mgr._observer

        # Act
        config_mgr.enable_hot_reload()

        # Assert
        assert config_mgr._observer is first_observer

        # Cleanup
        config_mgr.stop_watching()


class TestDataClasses:
    """Test suite for configuration data classes"""

    def test_subagent_config_defaults(self):
        """Test SubagentConfig default values"""
        config = SubagentConfig()
        assert config.max_concurrent == 5
        assert config.timeout == 3600
        assert config.model == "claude-sonnet-4"

    def test_quality_gates_config_defaults(self):
        """Test QualityGatesConfig default values and initialization"""
        config = QualityGatesConfig()
        assert config.pre_commit == []
        assert config.epic_complete == []
        assert config.pre_merge == []

    def test_quality_gates_config_with_values(self):
        """Test QualityGatesConfig with provided values"""
        config = QualityGatesConfig(
            pre_commit=['lint'],
            epic_complete=['test'],
            pre_merge=['integration']
        )
        assert config.pre_commit == ['lint']
        assert config.epic_complete == ['test']
        assert config.pre_merge == ['integration']

    def test_git_config_defaults(self):
        """Test GitConfig default values"""
        config = GitConfig()
        assert config.worktree_base == ".aedt/worktrees"
        assert config.branch_prefix == "epic"
        assert config.auto_cleanup is True

    def test_aedt_config_creation(self):
        """Test AEDTConfig creation with all sub-configs"""
        config = AEDTConfig(
            version="1.0",
            subagent=SubagentConfig(),
            quality_gates=QualityGatesConfig(),
            git=GitConfig()
        )
        assert config.version == "1.0"
        assert isinstance(config.subagent, SubagentConfig)
        assert isinstance(config.quality_gates, QualityGatesConfig)
        assert isinstance(config.git, GitConfig)
