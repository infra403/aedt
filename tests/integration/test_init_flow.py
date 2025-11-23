"""Integration tests for init command workflow"""

import pytest
import yaml
from click.testing import CliRunner
from pathlib import Path
from aedt.cli.main import cli
from aedt.core.config_manager import ConfigManager


class TestInitFlow:
    """Integration tests for complete init workflow"""

    def test_complete_init_workflow(self, tmp_path, monkeypatch):
        """Test complete initialization workflow from CLI to config loading"""
        # Arrange
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)

        # Act 1: Initialize via CLI
        result = runner.invoke(cli, ['init'])

        # Assert 1: CLI command succeeds
        assert result.exit_code == 0
        assert '✓' in result.output or '初始化成功' in result.output

        # Assert 2: Directory structure exists
        assert (tmp_path / ".aedt").exists()
        assert (tmp_path / ".aedt" / "config.yaml").exists()
        assert (tmp_path / ".aedt" / "logs").exists()
        assert (tmp_path / ".aedt" / "projects").exists()
        assert (tmp_path / ".aedt" / "worktrees").exists()

        # Act 2: Load configuration using ConfigManager
        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)
        config = config_mgr.load()

        # Assert 3: Configuration is valid and complete
        assert config.version == "1.0"
        assert config.subagent.max_concurrent == 5
        assert config.subagent.timeout == 3600
        assert config.subagent.model == "claude-sonnet-4"
        assert "lint" in config.quality_gates.pre_commit
        assert "unit_tests" in config.quality_gates.epic_complete
        assert config.git.worktree_base == ".aedt/worktrees"
        assert config.git.branch_prefix == "epic"
        assert config.git.auto_cleanup is True

    def test_init_then_reinit_without_force(self, tmp_path, monkeypatch):
        """Test initialization followed by re-initialization without --force"""
        # Arrange
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)

        # Act 1: Initial initialization
        result1 = runner.invoke(cli, ['init'])
        assert result1.exit_code == 0

        # Act 2: Try to re-initialize without force
        result2 = runner.invoke(cli, ['init'])

        # Assert: Second initialization fails
        assert result2.exit_code != 0
        assert '✗' in result2.output or '失败' in result2.output
        assert '配置文件已存在' in result2.output or 'force' in result2.output.lower()

    def test_init_with_force_preserves_nothing(self, tmp_path, monkeypatch):
        """Test that --force completely overwrites existing configuration"""
        # Arrange
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)

        # Act 1: Initial initialization
        runner.invoke(cli, ['init'])

        # Modify configuration
        config_path = tmp_path / ".aedt" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        config_data['subagent']['max_concurrent'] = 10  # Change value
        config_data['custom_field'] = 'custom_value'  # Add custom field

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        # Act 2: Re-initialize with force
        result = runner.invoke(cli, ['init', '--force'])

        # Assert: Configuration is reset to defaults
        assert result.exit_code == 0
        with open(config_path, 'r', encoding='utf-8') as f:
            new_config = yaml.safe_load(f)

        assert new_config['subagent']['max_concurrent'] == 5  # Back to default
        assert 'custom_field' not in new_config  # Custom field removed

    def test_global_and_local_init(self):
        """Test both global and local initialization"""
        # Skip this test as it would modify the real home directory
        # The --global functionality is tested manually
        pytest.skip("Skipping global init test to avoid modifying real home directory")

    def test_config_yaml_is_valid_yaml(self, tmp_path, monkeypatch):
        """Test that generated config.yaml is valid YAML"""
        # Arrange
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)

        # Act
        result = runner.invoke(cli, ['init'])
        assert result.exit_code == 0

        config_path = tmp_path / ".aedt" / "config.yaml"

        # Assert: YAML can be parsed without errors
        with open(config_path, 'r', encoding='utf-8') as f:
            try:
                config_data = yaml.safe_load(f)
                assert config_data is not None
                assert isinstance(config_data, dict)
            except yaml.YAMLError as e:
                pytest.fail(f"Generated config.yaml is not valid YAML: {e}")

    def test_init_creates_empty_subdirectories(self, tmp_path, monkeypatch):
        """Test that init creates empty subdirectories that can be used"""
        # Arrange
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)

        # Act
        result = runner.invoke(cli, ['init'])
        assert result.exit_code == 0

        # Assert: Subdirectories are writable
        logs_dir = tmp_path / ".aedt" / "logs"
        projects_dir = tmp_path / ".aedt" / "projects"
        worktrees_dir = tmp_path / ".aedt" / "worktrees"

        # Test writing to each subdirectory
        test_file = logs_dir / "test.log"
        test_file.write_text("test")
        assert test_file.exists()

        test_file = projects_dir / "test.yaml"
        test_file.write_text("test")
        assert test_file.exists()

        test_file = worktrees_dir / "test.txt"
        test_file.write_text("test")
        assert test_file.exists()

    def test_config_manager_can_reload_config(self, tmp_path, monkeypatch):
        """Test that ConfigManager can reload modified configuration"""
        # Arrange
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)

        # Act 1: Initialize
        runner.invoke(cli, ['init'])

        config_path = tmp_path / ".aedt" / "config.yaml"
        config_mgr = ConfigManager(config_path=config_path)

        # Act 2: Load initial config
        config1 = config_mgr.load()
        assert config1.subagent.max_concurrent == 5

        # Act 3: Modify config file
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        config_data['subagent']['max_concurrent'] = 10
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)

        # Act 4: Reload config
        config2 = config_mgr.load()

        # Assert: Config reflects changes
        assert config2.subagent.max_concurrent == 10
