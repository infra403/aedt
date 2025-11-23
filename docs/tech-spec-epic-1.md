# Epic 技术规格说明书：项目初始化与基础设施

日期：2025-11-23
作者：Architect Agent
Epic ID：1
状态：Draft

---

## 概览

Epic 1 "项目初始化与基础设施" 是 AEDT (AI-Enhanced Delivery Toolkit) 的基础模块，为整个系统提供核心基础设施支持。本 Epic 实现了 CLI 框架、配置管理系统、文件状态持久化、结构化日志系统以及崩溃恢复机制。

作为第一个 Epic，它不依赖其他任何模块，是所有后续 Epic 的基石。完成后，用户可以通过 `aedt init` 命令初始化 AEDT，系统将具备可靠的配置管理、自动状态保存和崩溃后恢复能力。这些能力确保了 AEDT 作为长时间运行的编排工具的可靠性和用户体验。

Epic 1 包含 5 个 Story，覆盖从项目初始化到崩溃恢复的完整生命周期，预计开发周期为 2-3 天。

---

## 目标与范围

### 目标

1. **用户可以快速初始化 AEDT**：通过 `aedt init` 命令生成配置文件和目录结构
2. **系统具备可靠的配置管理**：支持配置文件热加载、验证和友好的错误提示
3. **状态持久化零丢失**：使用原子写入机制确保状态文件不会因崩溃而损坏
4. **日志完整可追溯**：生成结构化日志，支持问题排查和操作审计
5. **自动崩溃恢复**：系统重启后自动加载状态，恢复用户工作进度

### In-Scope（包含）

- CLI 框架搭建（使用 Click 库）
- `aedt init` 命令实现
- 配置文件模板生成（YAML 格式）
- ConfigManager 模块（配置加载、验证、热加载）
- DataStore 模块（原子写入、文件状态持久化）
- Logger 模块（结构化日志、日志轮转）
- StateManager 模块（状态加载、验证、崩溃恢复）
- 目录结构创建与验证
- 单元测试和集成测试

### Out-of-Scope（不包含）

- TUI 界面（Epic 8）
- 项目管理功能（Epic 2）
- Epic 解析功能（Epic 3）
- Git Worktree 操作（Epic 4）
- Subagent 编排（Epic 6）
- 质量门控（Epic 7）
- 多语言支持（Phase 2）
- Web UI（Phase 2+）

---

## 系统架构对齐

### 架构分层

Epic 1 实现了架构文档中定义的以下层次：

**基础设施层 (Infrastructure Layer)：**
- **配置管理 (ConfigMgr)**：加载、验证、热加载配置文件
- **数据持久化 (DataStore)**：原子写入状态文件，确保数据完整性
- **日志系统 (Logger)**：结构化日志、日志轮转、按模块和 Epic 分离日志

**应用逻辑层 (Application Layer)：**
- **状态管理 (StateManager)**：管理项目和 Epic 状态，提供崩溃恢复能力

**用户交互层 (User Interface Layer)：**
- **CLI 命令 (aedt init)**：提供初始化命令入口

### 9 大核心模块映射

根据架构文档，AEDT 包含 9 个核心模块。Epic 1 涉及以下模块：

| 模块名称 | Epic 1 实现范围 | 完整实现 Epic |
|---------|---------------|-------------|
| **ConfigManager** | ✅ 完整实现 | Epic 1 |
| **StateManager** | ✅ 完整实现 | Epic 1 |
| **DataStore** | ✅ 完整实现 | Epic 1 |
| **Logger** | ✅ 完整实现 | Epic 1 |
| **ProjectManager** | ⏳ 接口定义，完整实现在 Epic 2 | Epic 2 |
| **EpicParser** | ❌ 不涉及 | Epic 3 |
| **Scheduler** | ❌ 不涉及 | Epic 5 |
| **SubagentOrchestrator** | ❌ 不涉及 | Epic 6 |
| **WorktreeManager** | ❌ 不涉及 | Epic 4 |
| **QualityGate** | ❌ 不涉及 | Epic 7 |
| **TUIApp** | ❌ 不涉及 | Epic 8 |
| **FileWatcher** | ❌ 不涉及 | Epic 3 |

### 技术栈选择

- **编程语言**：Python 3.10+
- **CLI 框架**：Click 8.0+（轻量级、易用、文档完善）
- **配置解析**：PyYAML 6.0+（标准 YAML 解析库）
- **日志系统**：Python 标准库 `logging` + `RotatingFileHandler`
- **文件操作**：Python 标准库 `os`, `pathlib`, `shutil`
- **测试框架**：pytest 7.0+

---

## 详细设计

### 服务与模块

#### 1. CLI 框架模块

**职责：**
- 提供 AEDT 命令行入口点
- 实现 `aedt init` 命令
- 处理命令行参数解析
- 提供友好的错误提示

**类/接口定义：**

```python
# src/aedt/cli/main.py
import click
from aedt.core.config_manager import ConfigManager
from aedt.core.state_manager import StateManager

@click.group()
@click.version_option(version='0.1.0')
def cli():
    """AEDT - AI-Enhanced Delivery Toolkit"""
    pass

@cli.command()
@click.option('--force', is_flag=True, help='覆盖已存在的配置')
@click.option('--global', 'is_global', is_flag=True, help='初始化全局配置')
def init(force: bool, is_global: bool):
    """初始化 AEDT 配置"""
    try:
        config_mgr = ConfigManager()
        config_mgr.initialize(force=force, is_global=is_global)
        click.echo(click.style('✓ AEDT 初始化成功', fg='green'))
    except Exception as e:
        click.echo(click.style(f'✗ 初始化失败: {e}', fg='red'), err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli()
```

**关键特性：**
- 使用 Click 的 `@click.group()` 实现命令组
- 支持 `--force` 参数强制覆盖已存在配置
- 支持 `--global` 参数初始化全局配置（`~/.aedt/`）
- 友好的成功/失败提示（彩色输出）

---

#### 2. ConfigManager 模块

**职责：**
- 初始化配置文件和目录结构
- 加载、验证配置文件
- 提供配置访问接口
- 支持热加载（检测配置变化）

**类/接口定义：**

```python
# src/aedt/core/config_manager.py
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import yaml

@dataclass
class SubagentConfig:
    """Subagent 配置"""
    max_concurrent: int = 5
    timeout: int = 3600
    model: str = "claude-sonnet-4"

@dataclass
class QualityGatesConfig:
    """质量门控配置"""
    pre_commit: List[str]
    epic_complete: List[str]
    pre_merge: List[str]

@dataclass
class GitConfig:
    """Git 配置"""
    worktree_base: str = ".aedt/worktrees"
    branch_prefix: str = "epic"
    auto_cleanup: bool = True

@dataclass
class AEDTConfig:
    """AEDT 主配置"""
    version: str
    subagent: SubagentConfig
    quality_gates: QualityGatesConfig
    git: GitConfig

class ConfigManager:
    """配置管理器"""

    DEFAULT_CONFIG_TEMPLATE = """
version: "1.0"

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
        self.config_path = config_path or Path.cwd() / ".aedt" / "config.yaml"
        self.config: Optional[AEDTConfig] = None

    def initialize(self, force: bool = False, is_global: bool = False) -> bool:
        """初始化配置文件和目录结构"""
        base_dir = Path.home() / ".aedt" if is_global else Path.cwd() / ".aedt"

        # 创建目录结构
        directories = [
            base_dir,
            base_dir / "logs",
            base_dir / "projects",
            base_dir / "worktrees",
        ]

        for directory in directories:
            if not self._ensure_directory(directory):
                raise RuntimeError(f"无法创建目录: {directory}")

        # 创建配置文件
        config_file = base_dir / "config.yaml"
        if config_file.exists() and not force:
            raise RuntimeError("配置文件已存在。使用 --force 强制覆盖")

        config_file.write_text(self.DEFAULT_CONFIG_TEMPLATE.strip())

        return True

    def load(self) -> AEDTConfig:
        """加载配置文件"""
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
        """验证并解析配置"""
        required_fields = ['version', 'subagent', 'quality_gates', 'git']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"配置文件缺少必需字段: {field}")

        return AEDTConfig(
            version=data['version'],
            subagent=SubagentConfig(**data['subagent']),
            quality_gates=QualityGatesConfig(**data['quality_gates']),
            git=GitConfig(**data['git'])
        )

    def _ensure_directory(self, path: Path) -> bool:
        """确保目录存在"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path.is_dir()
        except PermissionError:
            return False
        except Exception:
            return False

    def get(self, key: str, default=None):
        """获取配置值"""
        if not self.config:
            self.load()
        return getattr(self.config, key, default)
```

**关键特性：**
- 使用 `dataclass` 定义强类型配置结构
- 验证必需字段，提供友好错误提示
- 目录创建失败时立即返回错误
- 配置模板包含所有默认值

---

#### 3. DataStore 模块

**职责：**
- 提供原子写入接口，确保状态文件完整性
- 管理状态文件的读写
- 支持 YAML 格式的状态持久化

**类/接口定义：**

```python
# src/aedt/core/data_store.py
from pathlib import Path
from typing import Any, Dict
import yaml
import tempfile
import shutil

class DataStore:
    """数据存储层（原子写入）"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def atomic_write(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """原子写入 YAML 文件"""
        try:
            # 1. 写入临时文件
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=file_path.parent,
                delete=False,
                suffix='.tmp'
            ) as tmp_file:
                yaml.safe_dump(data, tmp_file, default_flow_style=False)
                tmp_path = Path(tmp_file.name)

            # 2. 原子重命名（POSIX 保证原子性）
            shutil.move(str(tmp_path), str(file_path))

            return True
        except Exception as e:
            # 清理临时文件
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()
            raise RuntimeError(f"写入失败: {e}")

    def read(self, file_path: Path) -> Dict[str, Any]:
        """读取 YAML 文件"""
        if not file_path.exists():
            return {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"文件格式错误: {file_path}\n{e}")

    def backup(self, file_path: Path, keep_count: int = 3) -> bool:
        """备份文件（保留最近 N 个）"""
        if not file_path.exists():
            return False

        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        shutil.copy2(file_path, backup_path)

        # 清理旧备份（保留最近 keep_count 个）
        backup_pattern = f"{file_path.stem}*.backup*"
        backups = sorted(
            file_path.parent.glob(backup_pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for old_backup in backups[keep_count:]:
            old_backup.unlink()

        return True
```

**关键特性：**
- **原子写入**：写入临时文件 → 重命名到目标文件（利用 POSIX rename 原子性）
- **备份机制**：写入前自动备份，保留最近 3 个版本
- **错误处理**：写入失败时清理临时文件，不留垃圾

---

#### 4. Logger 模块

**职责：**
- 提供结构化日志记录
- 支持按模块和 Epic 分离日志
- 实现日志轮转（避免日志文件过大）

**类/接口定义：**

```python
# src/aedt/core/logger.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

class AEDTLogger:
    """AEDT 日志系统"""

    def __init__(self, log_dir: Path, log_level: str = "INFO"):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_level = getattr(logging, log_level.upper())

        # 全局日志
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
        """设置日志器"""
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)

        # 避免重复添加 handler
        if logger.handlers:
            return logger

        # 文件 handler（带轮转）
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )

        # 格式化
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        return logger

    def get_logger(self, name: str) -> logging.Logger:
        """获取模块日志器"""
        return logging.getLogger(f"aedt.{name}")

    def get_epic_logger(self, project_name: str, epic_id: str) -> logging.Logger:
        """获取 Epic 专用日志器"""
        epic_log_dir = self.log_dir.parent / "projects" / project_name / "epics"
        epic_log_dir.mkdir(parents=True, exist_ok=True)

        log_file = epic_log_dir / f"epic-{epic_id}.log"
        return self._setup_logger(f"aedt.epic.{epic_id}", log_file)
```

**关键特性：**
- **分级日志**：DEBUG、INFO、WARNING、ERROR
- **日志轮转**：单文件最大 10MB，保留 5 个历史文件
- **分离日志**：全局日志 + Epic 专用日志
- **格式统一**：时间戳 + 级别 + 模块名 + 消息

---

#### 5. StateManager 模块

**职责：**
- 管理项目和 Epic 状态
- 提供状态加载、保存、验证接口
- 实现崩溃恢复逻辑

**类/接口定义：**

```python
# src/aedt/core/state_manager.py
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from aedt.core.data_store import DataStore

@dataclass
class EpicState:
    """Epic 状态"""
    epic_id: str
    status: str  # queued/developing/paused/completed/failed
    progress: float  # 0-100
    agent_id: Optional[str] = None
    worktree_path: Optional[str] = None
    completed_stories: List[str] = None
    last_updated: str = None

    def __post_init__(self):
        if self.completed_stories is None:
            self.completed_stories = []
        if self.last_updated is None:
            self.last_updated = datetime.utcnow().isoformat()

@dataclass
class ProjectState:
    """项目状态"""
    project_id: str
    project_name: str
    epics: Dict[str, EpicState]
    last_updated: str = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow().isoformat()

class StateManager:
    """状态管理器"""

    def __init__(self, base_dir: Path, data_store: DataStore):
        self.base_dir = base_dir
        self.data_store = data_store
        self.projects: Dict[str, ProjectState] = {}

    def load_all_states(self) -> Dict[str, ProjectState]:
        """加载所有项目状态"""
        projects_dir = self.base_dir / "projects"
        if not projects_dir.exists():
            return {}

        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            state_file = project_dir / "status.yaml"
            if state_file.exists():
                try:
                    data = self.data_store.read(state_file)
                    project_state = self._parse_project_state(data)

                    # 验证状态
                    validated_state = self._validate_state(project_state)
                    self.projects[project_state.project_id] = validated_state
                except Exception as e:
                    # 损坏的状态文件，尝试恢复备份
                    backup_file = state_file.with_suffix('.yaml.backup')
                    if backup_file.exists():
                        print(f"状态文件损坏，尝试恢复备份: {state_file}")
                        data = self.data_store.read(backup_file)
                        project_state = self._parse_project_state(data)
                        self.projects[project_state.project_id] = project_state

        return self.projects

    def save_project_state(self, project_state: ProjectState) -> bool:
        """保存项目状态"""
        project_dir = self.base_dir / "projects" / project_state.project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        state_file = project_dir / "status.yaml"

        # 备份旧状态
        if state_file.exists():
            self.data_store.backup(state_file)

        # 更新时间戳
        project_state.last_updated = datetime.utcnow().isoformat()

        # 原子写入
        data = asdict(project_state)
        return self.data_store.atomic_write(state_file, data)

    def _parse_project_state(self, data: dict) -> ProjectState:
        """解析项目状态"""
        epics = {
            epic_id: EpicState(**epic_data)
            for epic_id, epic_data in data.get('epics', {}).items()
        }

        return ProjectState(
            project_id=data['project_id'],
            project_name=data['project_name'],
            epics=epics,
            last_updated=data.get('last_updated')
        )

    def _validate_state(self, project_state: ProjectState) -> ProjectState:
        """验证并修正状态"""
        for epic_id, epic_state in project_state.epics.items():
            # 验证 Worktree 路径
            if epic_state.worktree_path:
                worktree_path = Path(epic_state.worktree_path)
                if not worktree_path.exists():
                    print(f"警告: Worktree 不存在: {epic_state.worktree_path}")
                    epic_state.status = "requires_cleanup"
                    epic_state.worktree_path = None

            # 崩溃恢复：将 developing 状态改为 paused
            if epic_state.status == "developing":
                epic_state.status = "paused"
                print(f"Epic {epic_id} 从崩溃中恢复，状态改为 'paused'")

        return project_state

    def get_project_state(self, project_id: str) -> Optional[ProjectState]:
        """获取项目状态"""
        return self.projects.get(project_id)

    def update_epic_state(
        self,
        project_id: str,
        epic_id: str,
        **kwargs
    ) -> bool:
        """更新 Epic 状态"""
        project_state = self.projects.get(project_id)
        if not project_state:
            return False

        epic_state = project_state.epics.get(epic_id)
        if not epic_state:
            return False

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(epic_state, key):
                setattr(epic_state, key, value)

        epic_state.last_updated = datetime.utcnow().isoformat()

        # 保存
        return self.save_project_state(project_state)
```

**关键特性：**
- **崩溃恢复**：加载时检测 `developing` 状态，自动改为 `paused`
- **Worktree 验证**：检查 Worktree 路径是否存在，无效时标记 `requires_cleanup`
- **备份恢复**：状态文件损坏时尝试从备份恢复
- **原子更新**：所有状态变更通过 DataStore 原子写入

---

### 数据模型与契约

#### 配置文件结构 (config.yaml)

```yaml
version: "1.0"

subagent:
  max_concurrent: 5        # 最大并发 Subagent 数量
  timeout: 3600            # 单个 Epic 超时时间（秒）
  model: "claude-sonnet-4" # Claude 模型

quality_gates:
  pre_commit:              # Story 提交前检查
    - "lint"
    - "format_check"
  epic_complete:           # Epic 完成检查
    - "unit_tests"
  pre_merge:               # 合并前检查
    - "integration_tests"

git:
  worktree_base: ".aedt/worktrees"  # Worktree 根目录
  branch_prefix: "epic"              # 分支前缀
  auto_cleanup: true                 # 自动清理 Worktree
```

#### 状态文件结构 (status.yaml)

```yaml
project_id: "aedt-001"
project_name: "AEDT"
last_updated: "2025-11-23T10:30:00Z"

epics:
  epic-1:
    epic_id: "1"
    status: "completed"           # queued/developing/paused/completed/failed
    progress: 100.0               # 0-100
    agent_id: "agent-abc123"
    worktree_path: ".aedt/worktrees/epic-1"
    completed_stories:
      - "1-1"
      - "1-2"
      - "1-3"
      - "1-4"
      - "1-5"
    last_updated: "2025-11-23T10:30:00Z"

  epic-2:
    epic_id: "2"
    status: "developing"
    progress: 40.0
    agent_id: "agent-def456"
    worktree_path: ".aedt/worktrees/epic-2"
    completed_stories:
      - "2-1"
      - "2-2"
    last_updated: "2025-11-23T10:25:00Z"
```

#### 目录结构

```
项目根目录/
├── .aedt/
│   ├── config.yaml              # 配置文件
│   ├── logs/
│   │   ├── aedt.log             # 全局日志
│   │   └── aedt.log.1           # 轮转日志备份
│   ├── projects/
│   │   └── {project-name}/
│   │       ├── status.yaml      # 项目状态
│   │       ├── status.yaml.backup
│   │       └── epics/
│   │           ├── epic-1.log
│   │           └── epic-2.log
│   └── worktrees/
│       ├── epic-1/              # Epic 1 Worktree（Epic 4 创建）
│       └── epic-2/              # Epic 2 Worktree

全局目录（可选）:
~/.aedt/
├── config.yaml                  # 全局配置
└── logs/
    └── aedt.log                 # 全局日志
```

---

### APIs 与接口

#### ConfigManager 接口

```python
class ConfigManager:
    def initialize(self, force: bool = False, is_global: bool = False) -> bool:
        """初始化配置文件和目录结构"""

    def load(self) -> AEDTConfig:
        """加载配置文件"""

    def get(self, key: str, default=None) -> Any:
        """获取配置值"""
```

#### DataStore 接口

```python
class DataStore:
    def atomic_write(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """原子写入 YAML 文件"""

    def read(self, file_path: Path) -> Dict[str, Any]:
        """读取 YAML 文件"""

    def backup(self, file_path: Path, keep_count: int = 3) -> bool:
        """备份文件"""
```

#### StateManager 接口

```python
class StateManager:
    def load_all_states(self) -> Dict[str, ProjectState]:
        """加载所有项目状态"""

    def save_project_state(self, project_state: ProjectState) -> bool:
        """保存项目状态"""

    def get_project_state(self, project_id: str) -> Optional[ProjectState]:
        """获取项目状态"""

    def update_epic_state(self, project_id: str, epic_id: str, **kwargs) -> bool:
        """更新 Epic 状态"""
```

#### AEDTLogger 接口

```python
class AEDTLogger:
    def get_logger(self, name: str) -> logging.Logger:
        """获取模块日志器"""

    def get_epic_logger(self, project_name: str, epic_id: str) -> logging.Logger:
        """获取 Epic 专用日志器"""
```

---

### 工作流与流程

#### 初始化流程

```
用户执行: aedt init
    ↓
CLI 命令解析（Click）
    ↓
ConfigManager.initialize()
    ↓
创建目录结构:
  - .aedt/
  - .aedt/logs/
  - .aedt/projects/
  - .aedt/worktrees/
    ↓
生成配置文件: .aedt/config.yaml
    ↓
验证目录和文件
    ↓
成功: 显示 "✓ AEDT 初始化成功"
失败: 显示错误信息和建议
```

#### 配置加载流程

```
任意 AEDT 命令启动
    ↓
ConfigManager.load()
    ↓
检查配置文件是否存在
    ↓ 不存在
    抛出 FileNotFoundError
    提示: "请先运行 'aedt init' 初始化配置"
    ↓ 存在
    读取 YAML 文件
    ↓
    验证 YAML 语法
    ↓ 语法错误
    抛出 ValueError
    提示: "配置文件 YAML 格式错误"
    ↓ 语法正确
    验证必需字段（version, subagent, quality_gates, git）
    ↓ 缺少字段
    抛出 ValueError
    提示: "配置文件缺少必需字段: {field}"
    ↓ 完整
    解析为 AEDTConfig 对象
    ↓
    返回配置对象
```

#### 状态持久化流程

```
Epic 状态变更（Story 完成、进度更新等）
    ↓
StateManager.update_epic_state(project_id, epic_id, status="...", progress=...)
    ↓
更新内存中的 EpicState 对象
    ↓
更新 last_updated 时间戳
    ↓
StateManager.save_project_state(project_state)
    ↓
DataStore.backup(state_file)  # 备份旧状态
    ↓
DataStore.atomic_write(state_file, data)
    ↓
写入临时文件: status.yaml.tmp
    ↓
原子重命名: status.yaml.tmp → status.yaml
    ↓
成功: 返回 True
失败: 清理临时文件，抛出异常
```

#### 崩溃恢复流程

```
AEDT 启动
    ↓
StateManager.load_all_states()
    ↓
遍历 .aedt/projects/*/status.yaml
    ↓
读取每个项目状态
    ↓ 文件损坏
    尝试从 status.yaml.backup 恢复
    ↓ 成功/跳过
    解析状态文件
    ↓
StateManager._validate_state(project_state)
    ↓
验证 Worktree 路径是否存在
    ↓ 不存在
    标记 epic.status = "requires_cleanup"
    打印警告: "Worktree 不存在: {path}"
    ↓ 存在
    检查 Epic 状态
    ↓ status == "developing"
    改为 status = "paused"
    打印: "Epic {id} 从崩溃中恢复，状态改为 'paused'"
    ↓
返回所有项目状态
    ↓
用户看到:
  "恢复自崩溃。2 个 Epic 已暂停。使用 'aedt resume epic-{id}' 恢复"
```

---

## 非功能需求

### 性能

**NFR1 - 目录创建性能**
- 目标：初始化命令（`aedt init`）完成时间 < 1 秒
- 实现：使用 `Path.mkdir(parents=True, exist_ok=True)` 批量创建目录

**NFR2 - 配置加载性能**
- 目标：配置文件加载时间 < 100ms
- 实现：使用 PyYAML `safe_load`，避免复杂对象反序列化

**NFR3 - 状态文件读写性能**
- 目标：单个状态文件原子写入 < 50ms（10 个 Epic 状态）
- 实现：临时文件写入 + 原子重命名（避免锁等待）

**NFR4 - 崩溃恢复性能**
- 目标：加载 10 个项目状态 < 1 秒
- 实现：并行读取状态文件（如果需要），当前串行读取足够快

### 安全

**NFR22 - 凭证安全**
- API 密钥从环境变量读取（`ANTHROPIC_API_KEY`），不存储在配置文件
- 配置文件中不包含任何敏感信息
- `.aedt/` 目录自动添加到 `.gitignore`（Story 1.1 实现）

**NFR23 - 文件系统权限**
- 只在用户主目录（`~/.aedt/`）和项目根目录（`.aedt/`）创建文件
- 不修改项目根目录外的任何文件
- 所有文件操作前检查权限，失败时提供清晰错误提示

**NFR24 - 配置文件权限**
- 配置文件使用默认权限（644），不存储敏感信息
- 日志文件使用默认权限（644），不记录敏感信息（如 API 密钥）

### 可靠性/可用性

**NFR8 - 崩溃恢复**
- AEDT 主进程崩溃后，重启时自动恢复所有项目状态
- Epic 进度、Worktree 路径不丢失
- `developing` 状态自动改为 `paused`，提示用户手动恢复

**NFR11 - 数据持久化可靠性**
- 状态文件每次更新时原子写入（写入临时文件 → 重命名）
- 避免部分写入导致的数据损坏
- 状态文件格式使用 YAML（人类可读，便于手动修复）
- 自动备份最近 3 个版本，支持手动恢复

**NFR10 - 容错设计**
- 配置文件格式错误时，提供友好提示和修复建议
- 状态文件损坏时，自动尝试从备份恢复
- 目录创建失败时，明确告知用户原因（权限、磁盘空间等）

### 可观测性

**NFR20 - 日志完整性**
- 所有关键操作都有日志记录（INFO 级别）：
  - 配置加载：`"Config loaded: {config_path}"`
  - 状态保存：`"State saved: {project_id}"`
  - 崩溃恢复：`"Epic {id} recovered from crash, status changed to 'paused'"`
- 错误操作记录详细堆栈（ERROR 级别）
- 日志格式统一：`[时间戳] [级别] [模块] 消息`

**NFR30 - 日志可追溯性**
- 每个操作包含项目 ID 和 Epic ID（如适用）
- 日志文件按日期轮转，保留 5 个历史文件
- Epic 专用日志独立存储：`.aedt/projects/{project}/epics/epic-{id}.log`

**NFR32 - 错误追踪**
- 所有异常都记录到日志文件（DEBUG 模式包含完整堆栈）
- 生产模式仅显示友好错误，堆栈写入日志
- 错误提示包含建议操作（如 "请运行 'aedt init' 初始化"）

---

## 依赖与集成

### 外部依赖

**Python 包依赖：**

```python
# requirements.txt
click>=8.0.0           # CLI 框架
PyYAML>=6.0            # YAML 配置解析
pytest>=7.0.0          # 测试框架
pytest-cov>=4.0.0      # 测试覆盖率
```

**Python 版本：**
- 最低版本：Python 3.10+
- 推荐版本：Python 3.11+

**操作系统：**
- MVP 支持：macOS、Linux
- Phase 2：Windows

### 内部模块依赖

```
CLI (main.py)
  └── ConfigManager

ConfigManager
  └── 无依赖（标准库）

DataStore
  └── 无依赖（标准库）

AEDTLogger
  └── 无依赖（标准库）

StateManager
  ├── DataStore
  └── AEDTLogger（可选）
```

### Epic 依赖

Epic 1 无依赖，是其他所有 Epic 的基础：

```
Epic 1 (本 Epic)
  ├── Epic 2 (项目管理) - 依赖 Epic 1 的 StateManager、ConfigManager
  ├── Epic 3 (Epic 解析) - 依赖 Epic 1 的 Logger、StateManager
  ├── Epic 4 (Git Worktree) - 依赖 Epic 1 的 Logger、StateManager
  └── ... (所有后续 Epic 都依赖 Epic 1)
```

---

## 验收标准（权威）

以下验收标准直接从 Epic 1 的 5 个 Story 提取，是判断 Epic 完成的唯一标准：

### Story 1.1: 项目初始化与 CLI 框架

```gherkin
Given 我在一个想要使用 AEDT 的目录
When 我运行 `aedt init`
Then 创建 `.aedt/` 目录
And 生成 `config.yaml` 文件并包含默认设置
And CLI 显示 "AEDT initialized successfully"
And 配置包含 max_concurrent、quality_gates、git 设置

Given AEDT 已初始化
When 我再次运行 `aedt init`
Then CLI 提示 "AEDT already initialized. Overwrite? [y/N]"
And 如果选择 'N'，保留现有配置
```

### Story 1.2: 配置管理系统

```gherkin
Given AEDT 已初始化
When 我编辑 `.aedt/config.yaml` 并将 max_concurrent 改为 3
And 我运行任意 AEDT 命令
Then 系统读取更新后的配置
And 应用 max_concurrent 限制为 3

Given 配置文件有无效的 YAML 语法
When 我运行任意 AEDT 命令
Then CLI 显示友好错误："Config file has invalid YAML syntax"
And 建议运行 `aedt init` 重新生成

Given 配置缺少必需字段
When 我运行任意 AEDT 命令
Then CLI 显示："Missing required config field: <field_name>"
And 提供期望格式
```

### Story 1.3: 文件状态持久化与原子写入

```gherkin
Given Epic 状态为 "developing"
When 状态更新（如 Story 完成）
Then 状态文件 `.aedt/projects/<project>/status.yaml` 原子写入
And 文件包含更新后的 Epic 状态和进度
And 如果写入时崩溃，旧状态保持完整

Given AEDT 崩溃后重启
When 系统初始化
Then 从 `.aedt/projects/*/status.yaml` 加载所有项目状态
And Epic 状态反映最后保存的状态
And Worktree 路径被验证（无效时清理）
```

### Story 1.4: 结构化日志系统

```gherkin
Given AEDT 正在运行
When 任意操作发生（Epic 启动、Git 操作、质量检查等）
Then 日志条目写入 `.aedt/logs/aedt.log`
And 条目包含：时间戳、级别（DEBUG/INFO/WARNING/ERROR）、模块、消息

Given Epic 启动
When Epic 级别操作发生
Then 创建独立日志文件 `.aedt/projects/<project>/epics/epic-<id>.log`
And 包含所有 Epic 特定操作

Given 日志级别设为 INFO
When 记录 DEBUG 消息
Then 该消息不写入文件（被级别过滤）
```

### Story 1.5: 崩溃恢复与状态验证

```gherkin
Given AEDT 在 Epic 开发中崩溃
When 我重启 AEDT
Then 系统从磁盘加载所有项目状态
And 将崩溃的 Epic 标记为 "paused"（非 "running"）
And 显示："Recovered from crash. 2 Epics were paused. Resume with `aedt resume epic-<id>`"

Given 状态文件中的 Worktree 路径不存在
When AEDT 加载状态
Then Worktree 引用标记为 "invalid"
And Epic 状态设为 "requires_cleanup"
And 提示用户运行 `aedt clean` 或手动修复

Given 状态文件损坏（无效 YAML）
When AEDT 启动
Then CLI 显示："State file corrupted: <path>. Backup exists at <path>.backup"
And 提供恢复备份或重新初始化的选项
```

---

## 可追溯性映射

### AC → 组件 → 测试

| 验收标准 | 涉及组件 | 单元测试 | 集成测试 |
|---------|---------|---------|---------|
| **Story 1.1 AC** | | | |
| 创建 `.aedt/` 目录 | ConfigManager | `test_config_manager.py::test_initialize_creates_directories` | `test_integration.py::test_init_command` |
| 生成 `config.yaml` | ConfigManager | `test_config_manager.py::test_initialize_creates_config_file` | 同上 |
| 显示成功消息 | CLI (main.py) | `test_cli.py::test_init_success_message` | 同上 |
| 覆盖保护提示 | CLI, ConfigManager | `test_cli.py::test_init_overwrite_prompt` | 同上 |
| **Story 1.2 AC** | | | |
| 加载更新后的配置 | ConfigManager | `test_config_manager.py::test_load_config` | `test_integration.py::test_config_hot_reload` |
| 验证 YAML 语法 | ConfigManager | `test_config_manager.py::test_load_invalid_yaml` | 同上 |
| 验证必需字段 | ConfigManager | `test_config_manager.py::test_load_missing_fields` | 同上 |
| **Story 1.3 AC** | | | |
| 原子写入状态文件 | DataStore | `test_data_store.py::test_atomic_write` | `test_integration.py::test_state_persistence` |
| 崩溃时保护旧状态 | DataStore | `test_data_store.py::test_atomic_write_failure` | 同上 |
| 重启后加载状态 | StateManager | `test_state_manager.py::test_load_all_states` | `test_integration.py::test_crash_recovery` |
| 验证 Worktree 路径 | StateManager | `test_state_manager.py::test_validate_worktree_paths` | 同上 |
| **Story 1.4 AC** | | | |
| 记录结构化日志 | AEDTLogger | `test_logger.py::test_log_entry_format` | `test_integration.py::test_logging` |
| Epic 专用日志 | AEDTLogger | `test_logger.py::test_epic_logger` | 同上 |
| 日志级别过滤 | AEDTLogger | `test_logger.py::test_log_level_filtering` | 同上 |
| **Story 1.5 AC** | | | |
| 崩溃后标记 Epic 为 paused | StateManager | `test_state_manager.py::test_crash_recovery` | `test_integration.py::test_crash_recovery` |
| 无效 Worktree 清理提示 | StateManager | `test_state_manager.py::test_invalid_worktree` | 同上 |
| 损坏状态文件恢复 | StateManager, DataStore | `test_state_manager.py::test_corrupted_state_recovery` | 同上 |

### FR 覆盖映射

| 功能需求 (FR) | Story | 组件 |
|--------------|-------|------|
| FR53 - 系统可以初始化 AEDT 配置 | 1.1, 1.2 | ConfigManager, CLI |
| FR54 - 系统可以持久化项目和 Epic 状态 | 1.3 | StateManager, DataStore |
| FR55 - 系统可以在重启后恢复所有项目状态 | 1.5 | StateManager |
| FR56 - 用户可以通过配置文件自定义 AEDT 行为 | 1.2 | ConfigManager |
| FR57 - 系统可以生成结构化日志 | 1.4 | AEDTLogger |

---

## 风险、假设与未决问题

### 风险

**风险 1：原子写入在不同操作系统上的行为差异**
- **描述**：`shutil.move()` 的原子性依赖操作系统。在 Windows 上可能不是原子操作
- **影响**：崩溃时可能导致状态文件损坏
- **缓解**：
  - MVP 阶段专注 macOS 和 Linux（POSIX 保证原子性）
  - Phase 2 支持 Windows 时，使用平台特定的原子写入实现
  - 备份机制提供额外保护
- **严重性**：中等
- **状态**：已缓解（MVP 范围内）

**风险 2：配置文件手动编辑错误**
- **描述**：用户手动编辑 YAML 时可能引入语法错误或删除必需字段
- **影响**：系统无法启动
- **缓解**：
  - 提供友好的错误提示和修复建议
  - 支持 `aedt init --force` 重新生成配置
  - 配置文件包含注释说明各字段含义
- **严重性**：低
- **状态**：已缓解

**风险 3：日志文件无限增长**
- **描述**：长时间运行可能导致日志文件占用大量磁盘空间
- **影响**：磁盘空间耗尽
- **缓解**：
  - 使用 `RotatingFileHandler`，单文件最大 10MB
  - 保留 5 个历史文件，总计最多 50MB
  - 用户可在配置中调整日志级别（减少日志量）
- **严重性**：低
- **状态**：已缓解

### 假设

**假设 1：用户具备基本的命令行使用能力**
- 用户能够运行 `aedt init` 命令并理解终端输出
- 验证：目标用户是资深开发者，假设成立

**假设 2：Python 3.10+ 环境可用**
- 用户已安装 Python 3.10 或更高版本
- 验证：在安装文档中明确说明要求

**假设 3：YAML 格式足够直观，用户可手动编辑**
- 用户能够理解和编辑 YAML 配置文件
- 验证：提供配置示例和注释，降低门槛

**假设 4：文件系统支持原子重命名（POSIX）**
- macOS 和 Linux 文件系统支持原子 `rename()` 操作
- 验证：POSIX 标准保证，假设成立

### 未决问题

**问题 1：是否需要支持全局配置 (`~/.aedt/config.yaml`)?**
- **当前决策**：Story 1.1 支持 `--global` 参数，但 MVP 暂不强制使用
- **待解决**：全局配置和项目配置的优先级关系
- **截止日期**：Epic 2 开始前
- **负责人**：Architect

**问题 2：日志格式是否需要支持 JSON（便于日志聚合工具解析）?**
- **当前决策**：MVP 使用人类可读的文本格式
- **待解决**：Phase 2 是否添加 JSON 格式选项
- **截止日期**：Phase 2 规划时
- **负责人**：Architect

**问题 3：是否需要提供 `aedt doctor` 命令检测环境问题？**
- **当前决策**：暂不实现，错误提示中提供诊断建议
- **待解决**：用户反馈后决定优先级
- **截止日期**：用户反馈收集后
- **负责人**：PM

---

## 测试策略总结

### 单元测试

**覆盖目标：80%+**

**测试文件结构：**
```
tests/unit/
├── test_config_manager.py
├── test_data_store.py
├── test_logger.py
├── test_state_manager.py
└── test_cli.py
```

**关键测试用例：**

**ConfigManager:**
- `test_initialize_creates_directories` - 验证目录创建
- `test_initialize_creates_config_file` - 验证配置文件生成
- `test_load_config` - 验证配置加载
- `test_load_invalid_yaml` - 验证 YAML 语法错误处理
- `test_load_missing_fields` - 验证必需字段缺失处理
- `test_initialize_overwrite_protection` - 验证覆盖保护

**DataStore:**
- `test_atomic_write` - 验证原子写入成功
- `test_atomic_write_failure` - 验证写入失败时的清理
- `test_read_yaml` - 验证 YAML 读取
- `test_backup_creation` - 验证备份文件创建
- `test_backup_rotation` - 验证旧备份清理（保留最近 3 个）

**AEDTLogger:**
- `test_log_entry_format` - 验证日志格式
- `test_log_level_filtering` - 验证日志级别过滤
- `test_epic_logger` - 验证 Epic 专用日志创建
- `test_log_rotation` - 验证日志轮转

**StateManager:**
- `test_load_all_states` - 验证加载所有项目状态
- `test_save_project_state` - 验证保存项目状态
- `test_atomic_state_write` - 验证状态原子写入
- `test_crash_recovery` - 验证崩溃恢复逻辑
- `test_validate_worktree_paths` - 验证 Worktree 路径验证
- `test_corrupted_state_recovery` - 验证损坏状态文件恢复

### 集成测试

**测试场景：**

**场景 1：完整初始化流程**
```python
def test_init_command():
    """测试 aedt init 命令完整流程"""
    # 1. 执行 aedt init
    # 2. 验证目录结构创建
    # 3. 验证配置文件生成
    # 4. 验证配置可加载
```

**场景 2：配置热加载**
```python
def test_config_hot_reload():
    """测试配置文件热加载"""
    # 1. 初始化 AEDT
    # 2. 修改配置文件
    # 3. 重新加载配置
    # 4. 验证新配置生效
```

**场景 3：状态持久化与恢复**
```python
def test_state_persistence():
    """测试状态持久化"""
    # 1. 创建项目状态
    # 2. 保存状态
    # 3. 重新加载状态
    # 4. 验证状态一致
```

**场景 4：崩溃恢复**
```python
def test_crash_recovery():
    """测试崩溃恢复流程"""
    # 1. 创建 developing 状态的 Epic
    # 2. 模拟崩溃（不调用 cleanup）
    # 3. 重新加载状态
    # 4. 验证 Epic 状态改为 paused
    # 5. 验证 Worktree 路径验证
```

### 测试数据

**测试配置文件：**
```yaml
# tests/fixtures/valid_config.yaml
version: "1.0"
subagent:
  max_concurrent: 3
  timeout: 1800
  model: "claude-sonnet-4"
quality_gates:
  pre_commit: ["lint"]
  epic_complete: ["unit_tests"]
  pre_merge: ["integration_tests"]
git:
  worktree_base: ".aedt/worktrees"
  branch_prefix: "epic"
  auto_cleanup: true
```

**测试状态文件：**
```yaml
# tests/fixtures/valid_state.yaml
project_id: "test-001"
project_name: "TestProject"
last_updated: "2025-11-23T10:00:00Z"
epics:
  epic-1:
    epic_id: "1"
    status: "completed"
    progress: 100.0
    agent_id: "agent-test-123"
    worktree_path: ".aedt/worktrees/epic-1"
    completed_stories: ["1-1", "1-2"]
    last_updated: "2025-11-23T10:00:00Z"
```

### 测试工具

- **pytest** - 测试框架
- **pytest-cov** - 测试覆盖率
- **pytest-mock** - Mock 支持
- **tempfile** - 临时文件和目录（避免污染文件系统）

### 测试执行

```bash
# 运行所有测试
pytest tests/

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=src/aedt --cov-report=html tests/
```

### 验收测试

**手动测试清单：**

- [ ] 在全新目录运行 `aedt init`，验证成功
- [ ] 在已初始化目录运行 `aedt init`，验证覆盖保护
- [ ] 手动编辑配置文件，引入语法错误，验证错误提示
- [ ] 删除配置文件必需字段，验证错误提示
- [ ] 创建项目状态并保存，验证状态文件生成
- [ ] 删除 Worktree 路径，重启 AEDT，验证清理提示
- [ ] 模拟崩溃（kill 进程），重启，验证恢复提示
- [ ] 检查日志文件格式和内容
- [ ] 验证日志轮转（创建大量日志触发轮转）

---

## 总结

Epic 1 "项目初始化与基础设施" 为 AEDT 奠定了坚实的基础，实现了可靠的配置管理、状态持久化、日志系统和崩溃恢复能力。通过 5 个 Story 的有序开发，系统将具备以下能力：

1. **快速初始化**：用户运行 `aedt init` 即可开始使用
2. **可靠持久化**：原子写入保证状态永不丢失
3. **自动恢复**：崩溃后自动恢复工作进度
4. **完整日志**：结构化日志支持问题排查
5. **友好体验**：清晰的错误提示和修复建议

作为所有后续 Epic 的依赖，Epic 1 的高质量完成对整个项目至关重要。本技术规格说明书提供了完整的设计细节、验收标准和测试策略，确保开发团队能够高效实现并验证所有功能。

---

**下一步行动：**
1. 开发团队 Review 本技术规格说明书
2. Scrum Master 基于本文档创建 Story 1.1 的详细开发上下文
3. 开发 Agent 开始实现 Story 1.1
4. 完成后依次实现 Story 1.2 - 1.5
5. 执行完整测试套件，确保所有验收标准通过
