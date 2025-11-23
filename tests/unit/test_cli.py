"""Unit tests for CLI commands"""

import pytest
from click.testing import CliRunner
from pathlib import Path
from aedt.cli.main import cli


class TestCLI:
    """Test suite for CLI commands"""

    def test_cli_version(self):
        """Test CLI version display"""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ['--version'])

        # Assert
        assert result.exit_code == 0
        assert '0.1.0' in result.output

    def test_cli_help(self):
        """Test CLI help display"""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ['--help'])

        # Assert
        assert result.exit_code == 0
        assert 'AEDT' in result.output
        assert 'init' in result.output

    def test_init_success(self, tmp_path, monkeypatch):
        """Test successful initialization"""
        # Arrange
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)

        # Act
        result = runner.invoke(cli, ['init'])

        # Assert
        assert result.exit_code == 0
        assert '✓' in result.output or '初始化成功' in result.output
        assert (tmp_path / ".aedt").exists()
        assert (tmp_path / ".aedt" / "config.yaml").exists()

    def test_init_with_force(self, tmp_path, monkeypatch):
        """Test initialization with --force flag"""
        # Arrange
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)

        # Initialize once
        runner.invoke(cli, ['init'])

        # Modify config
        config_path = tmp_path / ".aedt" / "config.yaml"
        original_content = config_path.read_text()
        config_path.write_text("modified: true")

        # Act - Reinitialize with force
        result = runner.invoke(cli, ['init', '--force'])

        # Assert
        assert result.exit_code == 0
        assert '✓' in result.output or '初始化成功' in result.output
        content = config_path.read_text()
        assert "modified: true" not in content
        assert "version:" in content

    def test_init_without_force_fails(self, tmp_path, monkeypatch):
        """Test initialization fails without --force when config exists"""
        # Arrange
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)

        # Initialize once
        runner.invoke(cli, ['init'])

        # Act - Try to initialize again without force
        result = runner.invoke(cli, ['init'])

        # Assert
        assert result.exit_code != 0
        assert '✗' in result.output or '失败' in result.output

    def test_init_global(self):
        """Test global initialization with --global flag"""
        # Skip this test as it would modify the real home directory
        # This is tested in integration tests with proper mocking
        pytest.skip("Skipping global init test to avoid modifying real home directory")

    def test_init_creates_directory_structure(self, tmp_path, monkeypatch):
        """Test that init creates all required directories"""
        # Arrange
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)

        # Act
        result = runner.invoke(cli, ['init'])

        # Assert
        assert result.exit_code == 0
        assert (tmp_path / ".aedt").is_dir()
        assert (tmp_path / ".aedt" / "logs").is_dir()
        assert (tmp_path / ".aedt" / "projects").is_dir()
        assert (tmp_path / ".aedt" / "worktrees").is_dir()

    def test_init_displays_directory_structure(self, tmp_path, monkeypatch):
        """Test that init displays created directory structure"""
        # Arrange
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)

        # Act
        result = runner.invoke(cli, ['init'])

        # Assert
        assert result.exit_code == 0
        assert 'config.yaml' in result.output
        assert 'logs/' in result.output
        assert 'projects/' in result.output
        assert 'worktrees/' in result.output

    def test_init_permission_error(self, tmp_path, monkeypatch):
        """Test init handles permission errors gracefully"""
        # Arrange
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)

        # Create .aedt directory with no write permissions
        aedt_dir = tmp_path / ".aedt"
        aedt_dir.mkdir()
        aedt_dir.chmod(0o444)  # Read-only

        try:
            # Act
            result = runner.invoke(cli, ['init'])

            # Assert
            assert result.exit_code != 0
            assert '✗' in result.output or '失败' in result.output
        finally:
            # Cleanup - restore permissions
            aedt_dir.chmod(0o755)
