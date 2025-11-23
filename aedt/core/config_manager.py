"""Configuration Manager for AEDT

This module handles initialization, loading, and validation of AEDT configuration files.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


@dataclass
class SubagentConfig:
    """Subagent configuration"""
    max_concurrent: int = 5
    timeout: int = 3600
    model: str = "claude-sonnet-4"


@dataclass
class QualityGatesConfig:
    """Quality gates configuration"""
    pre_commit: List[str] = None
    epic_complete: List[str] = None
    pre_merge: List[str] = None

    def __post_init__(self):
        """Initialize empty lists if None"""
        if self.pre_commit is None:
            self.pre_commit = []
        if self.epic_complete is None:
            self.epic_complete = []
        if self.pre_merge is None:
            self.pre_merge = []


@dataclass
class GitConfig:
    """Git configuration"""
    worktree_base: str = ".aedt/worktrees"
    branch_prefix: str = "epic"
    auto_cleanup: bool = True


@dataclass
class AEDTConfig:
    """AEDT main configuration"""
    version: str
    subagent: SubagentConfig
    quality_gates: QualityGatesConfig
    git: GitConfig


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for config file changes"""

    def __init__(self, config_manager):
        """Initialize handler

        Args:
            config_manager: ConfigManager instance to notify on changes
        """
        self.config_manager = config_manager

    def on_modified(self, event):
        """Handle file modification event

        Args:
            event: File system event
        """
        if event.src_path.endswith('config.yaml'):
            self.config_manager.reload_config()


class ConfigManager:
    """Configuration Manager

    Manages AEDT configuration files including initialization, loading,
    and validation.
    """

    DEFAULT_CONFIG_TEMPLATE = """version: "1.0"

subagent:
  max_concurrent: 5
  timeout: 3600
  model: "claude-sonnet-4"

quality_gates:
  pre_commit:
    - "lint"
    - "format_check"
  epic_complete:
    - "unit_tests"
  pre_merge:
    - "integration_tests"

git:
  worktree_base: ".aedt/worktrees"
  branch_prefix: "epic"
  auto_cleanup: true
"""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize ConfigManager

        Args:
            config_path: Path to config file. If None, uses .aedt/config.yaml in cwd
        """
        self.config_path = config_path or Path.cwd() / ".aedt" / "config.yaml"
        self.config: Optional[AEDTConfig] = None
        self._observer: Optional[Observer] = None

    def initialize(self, force: bool = False, is_global: bool = False) -> bool:
        """Initialize configuration file and directory structure

        Args:
            force: Force overwrite existing configuration
            is_global: Initialize global configuration in ~/.aedt/

        Returns:
            True if initialization successful

        Raises:
            RuntimeError: If directory creation fails or config already exists
        """
        # Determine base directory
        if self.config_path.parent.name == ".aedt":
            # Config path already set (e.g., in tests), use its parent
            base_dir = self.config_path.parent
        else:
            # Derive from is_global parameter
            base_dir = Path.home() / ".aedt" if is_global else Path.cwd() / ".aedt"

        # Create directory structure
        directories = [
            base_dir,
            base_dir / "logs",
            base_dir / "projects",
            base_dir / "worktrees",
        ]

        for directory in directories:
            if not self._ensure_directory(directory):
                raise RuntimeError(f"无法创建目录: {directory}")

        # Create configuration file
        config_file = base_dir / "config.yaml"
        if config_file.exists() and not force:
            raise RuntimeError(
                "配置文件已存在。使用 --force 强制覆盖"
            )

        config_file.write_text(self.DEFAULT_CONFIG_TEMPLATE.strip(), encoding='utf-8')

        return True

    def load(self) -> AEDTConfig:
        """Load configuration file

        Returns:
            Loaded and validated configuration

        Raises:
            FileNotFoundError: If config file does not exist
            ValueError: If config file has invalid format or missing fields
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"配置文件不存在: {self.config_path}\n"
                "请先运行 'aedt init' 初始化配置"
            )

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(
                f"配置文件 YAML 格式错误:\n{e}\n"
                "请检查语法或运行 'aedt init --force' 重新生成"
            )

        self.config = self._validate_and_parse(data)
        return self.config

    def _validate_and_parse(self, data: dict) -> AEDTConfig:
        """Validate and parse configuration data

        Args:
            data: Raw configuration dictionary

        Returns:
            Validated configuration object

        Raises:
            ValueError: If required fields are missing or invalid
        """
        if data is None:
            raise ValueError("配置文件为空，请检查文件内容")

        # Check required fields
        required_fields = ['version', 'subagent', 'quality_gates', 'git']
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise ValueError(
                f"配置文件缺少必需字段: {', '.join(missing_fields)}\n"
                f"请检查 {self.config_path}"
            )

        # Validate version
        if not isinstance(data['version'], str):
            raise ValueError(
                f"version 必须是字符串类型，当前类型: {type(data['version']).__name__}"
            )

        # Validate subagent config
        subagent_data = data['subagent']
        if not isinstance(subagent_data, dict):
            raise ValueError(
                f"subagent 必须是对象类型，当前类型: {type(subagent_data).__name__}"
            )

        # Validate max_concurrent
        if 'max_concurrent' in subagent_data:
            max_concurrent = subagent_data['max_concurrent']
            if not isinstance(max_concurrent, int):
                raise ValueError(
                    f"subagent.max_concurrent 必须是整数类型，"
                    f"当前类型: {type(max_concurrent).__name__}"
                )
            if max_concurrent <= 0:
                raise ValueError(
                    f"subagent.max_concurrent 必须大于 0，"
                    f"当前值: {max_concurrent}"
                )

        # Validate timeout
        if 'timeout' in subagent_data:
            timeout = subagent_data['timeout']
            if not isinstance(timeout, int):
                raise ValueError(
                    f"subagent.timeout 必须是整数类型，"
                    f"当前类型: {type(timeout).__name__}"
                )
            if timeout <= 0:
                raise ValueError(
                    f"subagent.timeout 必须大于 0，"
                    f"当前值: {timeout}"
                )

        # Validate quality_gates config
        quality_gates_data = data['quality_gates']
        if not isinstance(quality_gates_data, dict):
            raise ValueError(
                f"quality_gates 必须是对象类型，当前类型: {type(quality_gates_data).__name__}"
            )

        # Validate quality gate lists
        for gate_name in ['pre_commit', 'epic_complete', 'pre_merge']:
            if gate_name in quality_gates_data:
                gate_value = quality_gates_data[gate_name]
                if gate_value is not None and not isinstance(gate_value, list):
                    raise ValueError(
                        f"quality_gates.{gate_name} 必须是列表类型，"
                        f"当前类型: {type(gate_value).__name__}"
                    )

        # Validate git config
        git_data = data['git']
        if not isinstance(git_data, dict):
            raise ValueError(
                f"git 必须是对象类型，当前类型: {type(git_data).__name__}"
            )

        try:
            return AEDTConfig(
                version=data['version'],
                subagent=SubagentConfig(**subagent_data),
                quality_gates=QualityGatesConfig(**quality_gates_data),
                git=GitConfig(**git_data)
            )
        except TypeError as e:
            raise ValueError(
                f"配置文件字段类型错误: {e}\n"
                f"请检查配置文件格式"
            )

    def _ensure_directory(self, path: Path) -> bool:
        """Ensure directory exists

        Args:
            path: Directory path to create

        Returns:
            True if directory exists or was created successfully
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path.is_dir()
        except PermissionError:
            return False
        except Exception:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation

        Supports nested key access like 'subagent.max_concurrent'

        Args:
            key: Configuration key (supports dot notation for nested access)
            default: Default value if key not found

        Returns:
            Configuration value or default if not found
        """
        if not self.config:
            self.load()

        # Split key by dots for nested access
        keys = key.split('.')
        value = self.config

        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default

        return value

    def save_config(self, config: Optional[AEDTConfig] = None):
        """Save configuration to config.yaml

        Args:
            config: Configuration to save. If None, saves current config.

        Raises:
            ValueError: If no config provided and no config loaded
        """
        if config is None:
            config = self.config

        if config is None:
            raise ValueError("没有配置可保存。请先加载或提供配置对象。")

        # Convert config objects to dict
        config_dict = {
            'version': config.version,
            'subagent': {
                'max_concurrent': config.subagent.max_concurrent,
                'timeout': config.subagent.timeout,
                'model': config.subagent.model,
            },
            'quality_gates': {
                'pre_commit': config.quality_gates.pre_commit or [],
                'epic_complete': config.quality_gates.epic_complete or [],
                'pre_merge': config.quality_gates.pre_merge or [],
            },
            'git': {
                'worktree_base': config.git.worktree_base,
                'branch_prefix': config.git.branch_prefix,
                'auto_cleanup': config.git.auto_cleanup,
            }
        }

        # Ensure parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False,
                          allow_unicode=True, sort_keys=False)

        logger.info(f"配置已保存到: {self.config_path}")

    def enable_hot_reload(self):
        """Enable hot reloading of config file on changes

        Watches the config file directory and reloads configuration
        automatically when config.yaml is modified.
        """
        if self._observer is not None:
            logger.warning("配置热加载已经启用")
            return

        event_handler = ConfigFileHandler(self)
        self._observer = Observer()
        self._observer.schedule(event_handler, str(self.config_path.parent),
                               recursive=False)
        self._observer.start()
        logger.info(f"已启用配置热加载，监听: {self.config_path}")

    def reload_config(self):
        """Reload configuration from file

        Called automatically by hot reload or can be called manually.
        On validation failure, preserves the old configuration.
        """
        old_config = self.config

        try:
            self.load()
            logger.info(f"配置已重新加载: {self.config_path}")
        except Exception as e:
            logger.error(f"配置重新加载失败，保留旧配置: {e}")
            self.config = old_config

    def stop_watching(self):
        """Stop watching config file for changes

        Disables hot reload functionality.
        """
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("已停止配置热加载")
