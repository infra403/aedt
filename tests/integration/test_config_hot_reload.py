"""Integration tests for ConfigManager hot reload functionality"""

import pytest
import time
import yaml
from pathlib import Path
from aedt.core.config_manager import ConfigManager


class TestConfigHotReload:
    """Integration tests for configuration hot reload"""

    def test_hot_reload_config_update(self, tmp_path):
        """Test that config is automatically reloaded when file changes"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)
        config_mgr.load()

        # Enable hot reload
        config_mgr.enable_hot_reload()

        # Verify initial value
        assert config_mgr.config.subagent.max_concurrent == 5

        # Act - Modify config file
        config_data = {
            'version': '1.0',
            'subagent': {
                'max_concurrent': 10,
                'timeout': 3600,
                'model': 'claude-sonnet-4'
            },
            'quality_gates': {
                'pre_commit': [],
                'epic_complete': [],
                'pre_merge': []
            },
            'git': {
                'worktree_base': '.aedt/worktrees',
                'branch_prefix': 'epic',
                'auto_cleanup': True
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        # Wait for file system event to trigger
        time.sleep(0.5)

        # Assert - Config should be reloaded
        assert config_mgr.config.subagent.max_concurrent == 10

        # Cleanup
        config_mgr.stop_watching()

    def test_hot_reload_preserves_on_invalid_update(self, tmp_path):
        """Test that invalid config update preserves old config"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)
        config_mgr.load()

        # Enable hot reload
        config_mgr.enable_hot_reload()

        # Store initial value
        initial_max_concurrent = config_mgr.config.subagent.max_concurrent

        # Act - Write invalid config
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: syntax:")

        # Wait for file system event to trigger
        time.sleep(0.5)

        # Assert - Old config should be preserved
        assert config_mgr.config.subagent.max_concurrent == initial_max_concurrent

        # Cleanup
        config_mgr.stop_watching()

    def test_full_config_lifecycle(self, tmp_path):
        """Test complete configuration lifecycle: init -> load -> modify -> save -> reload"""
        # Step 1: Initialize
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)

        # Step 2: Load
        config = config_mgr.load()
        assert config.subagent.max_concurrent == 5

        # Step 3: Modify
        config.subagent.max_concurrent = 8
        config.git.branch_prefix = "feature"

        # Step 4: Save
        config_mgr.save_config(config)

        # Step 5: Reload with new manager
        config_mgr2 = ConfigManager(config_path=config_path)
        config2 = config_mgr2.load()

        # Assert - Changes persisted
        assert config2.subagent.max_concurrent == 8
        assert config2.git.branch_prefix == "feature"

    def test_nested_key_access_integration(self, tmp_path):
        """Test nested key access in realistic scenario"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)

        # Act - Access various nested keys
        max_concurrent = config_mgr.get('subagent.max_concurrent')
        timeout = config_mgr.get('subagent.timeout')
        model = config_mgr.get('subagent.model')
        worktree_base = config_mgr.get('git.worktree_base')
        branch_prefix = config_mgr.get('git.branch_prefix')
        auto_cleanup = config_mgr.get('git.auto_cleanup')

        # Assert
        assert max_concurrent == 5
        assert timeout == 3600
        assert model == "claude-sonnet-4"
        assert worktree_base == ".aedt/worktrees"
        assert branch_prefix == "epic"
        assert auto_cleanup is True

    def test_config_validation_comprehensive(self, tmp_path):
        """Test comprehensive configuration validation"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Test Case 1: Missing required field
        config_data = {
            'version': '1.0',
            'subagent': {'max_concurrent': 5}
            # Missing quality_gates and git
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        config_mgr = ConfigManager(config_path=config_path)
        with pytest.raises(ValueError, match="缺少必需字段"):
            config_mgr.load()

        # Test Case 2: Invalid type for max_concurrent
        config_data = {
            'version': '1.0',
            'subagent': {'max_concurrent': '5'},  # String instead of int
            'quality_gates': {},
            'git': {}
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        with pytest.raises(ValueError, match="max_concurrent 必须是整数类型"):
            config_mgr.load()

        # Test Case 3: Invalid value (max_concurrent <= 0)
        config_data = {
            'version': '1.0',
            'subagent': {'max_concurrent': 0},
            'quality_gates': {},
            'git': {}
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        with pytest.raises(ValueError, match="max_concurrent 必须大于 0"):
            config_mgr.load()

        # Test Case 4: Valid config should load successfully
        config_data = {
            'version': '1.0',
            'subagent': {
                'max_concurrent': 5,
                'timeout': 3600,
                'model': 'claude-sonnet-4'
            },
            'quality_gates': {
                'pre_commit': ['lint'],
                'epic_complete': ['test'],
                'pre_merge': ['integration']
            },
            'git': {
                'worktree_base': '.aedt/worktrees',
                'branch_prefix': 'epic',
                'auto_cleanup': True
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        config = config_mgr.load()
        assert config.subagent.max_concurrent == 5
        assert config.quality_gates.pre_commit == ['lint']

    def test_concurrent_access_safe(self, tmp_path):
        """Test that config manager is safe for concurrent access"""
        # Arrange
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config_mgr.initialize(force=False, is_global=False)
        config_mgr.load()

        # Act - Multiple get calls
        values = []
        for _ in range(10):
            values.append(config_mgr.get('subagent.max_concurrent'))

        # Assert - All values should be consistent
        assert all(v == 5 for v in values)
