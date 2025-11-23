# Story 1.1: 项目初始化与 CLI 框架

**状态:** review
**Epic:** Epic 1
**Story Key:** 1-1-project-initialization-and-cli-framework
**日期创建:** 2025-11-23

---

## User Story

**As a** 开发者
**I want** 运行 `aedt init` 来初始化 AEDT 配置
**So that** 我可以开始使用 AEDT 并拥有正确的设置

## Acceptance Criteria

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

## Tasks/Subtasks

### 1. 创建 CLI 框架和入口点
- [x] 使用 Click 框架创建主 CLI 命令组
- [x] 实现 `aedt init` 命令
- [x] 添加 `--force` 和 `--global` 选项
- [x] 实现友好的彩色输出（成功/失败提示）

### 2. 实现目录结构创建逻辑
- [x] 创建全局配置目录：`~/.aedt/`、`~/.aedt/logs/`
- [x] 创建项目配置目录：`{project-root}/.aedt/`
- [x] 创建子目录：`projects/`、`worktrees/`、`logs/`
- [x] 实现目录创建验证逻辑（检查每个目录是否创建成功）
- [x] 处理权限错误和磁盘空间不足等异常

### 3. 实现配置文件生成
- [x] 创建默认配置模板（包含所有必需字段）
- [x] 生成 `.aedt/config.yaml` 文件
- [x] 验证配置文件格式（YAML 语法正确性）
- [x] 实现覆盖保护逻辑（已初始化时提示确认）

### 4. 实现错误处理和用户提示
- [x] 权限问题 → "请检查目录权限：{path}"
- [x] 磁盘空间不足 → "磁盘空间不足，请清理后重试"
- [x] 其他错误 → 显示具体异常信息和建议操作
- [x] 使用友好的错误提示，而非技术堆栈跟踪

### 5. 编写单元测试和集成测试
- [x] 测试初始化流程（成功场景）
- [x] 测试覆盖保护逻辑
- [x] 测试错误处理（权限、磁盘空间等）
- [x] 测试配置文件生成和验证

## Dev Notes

### 技术实现细节

**CLI 框架实现：**
```python
# src/aedt/cli/main.py
import click
from aedt.core.config_manager import ConfigManager

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
```

**目录创建验证逻辑：**
```python
def ensure_directory(path: str) -> bool:
    """确保目录存在，失败时返回 False 并记录错误"""
    try:
        os.makedirs(path, exist_ok=True)
        if not os.path.isdir(path):
            logger.error(f"Failed to create directory: {path}")
            return False
        logger.info(f"Directory ready: {path}")
        return True
    except PermissionError:
        logger.error(f"Permission denied: {path}")
        return False
    except Exception as e:
        logger.error(f"Error creating {path}: {e}")
        return False
```

**默认配置模板：**
```yaml
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
```

### 目录结构
```
项目根目录/
├── .aedt/
│   ├── config.yaml              # 配置文件
│   ├── logs/                    # 项目日志目录
│   ├── projects/                # 项目状态目录
│   └── worktrees/               # Worktree 根目录

全局目录（可选）:
~/.aedt/
├── config.yaml                  # 全局配置
└── logs/                        # 全局日志目录
```

### 覆盖的需求
- FR53（系统可以初始化 AEDT 配置）
- NFR16（可靠性 - 友好错误提示）
- NFR13（可用性 - 学习曲线）

### 受影响组件
- CLI framework (新建)
- ConfigManager (新建)

## Dependencies

- **Prerequisites:** 无（Story 1.1 必须是第一个）
- **Tech Spec Reference:** docs/tech-spec-epic-1.md
  - 章节：详细设计 → CLI 框架模块
  - 章节：详细设计 → ConfigManager 模块

## Dev Agent Record

- **Context Reference:** docs/1-1-project-initialization-and-cli-framework.context.xml
- **Status History:**
  - 2025-11-23: Created (backlog → drafted)
  - 2025-11-23: Context created (drafted → ready-for-dev)
  - 2025-11-23: Development started (ready-for-dev → in-progress)
  - 2025-11-23: Implementation completed, tests pass with 92% coverage (in-progress → review)

## File List

### Created Files
- `aedt/__init__.py` - Package initialization
- `aedt/cli/__init__.py` - CLI package initialization
- `aedt/cli/main.py` - CLI entry point with Click framework
- `aedt/commands/__init__.py` - Commands package initialization
- `aedt/core/__init__.py` - Core package initialization
- `aedt/core/config_manager.py` - Configuration management module
- `tests/__init__.py` - Test package initialization
- `tests/unit/__init__.py` - Unit tests package
- `tests/unit/test_config_manager.py` - ConfigManager unit tests (11 tests)
- `tests/unit/test_cli.py` - CLI unit tests (9 tests)
- `tests/integration/__init__.py` - Integration tests package
- `tests/integration/test_init_flow.py` - Init workflow integration tests (7 tests)
- `setup.py` - Package setup configuration
- `requirements.txt` - Python dependencies
- `pytest.ini` - Pytest configuration

### Modified Files
- None (new story implementation)

## Implementation Notes

### What Was Built
1. **CLI Framework**: Implemented using Click 8.0+ with `aedt init` command
2. **ConfigManager**: Full-featured configuration management with validation
3. **Directory Structure**: Automated creation of `.aedt/`, `logs/`, `projects/`, `worktrees/`
4. **Error Handling**: Friendly error messages in Chinese with helpful suggestions
5. **Test Suite**: 27 tests (25 passed, 2 skipped) with 92% code coverage

### Key Features
- `aedt init` - Initialize project configuration
- `aedt init --force` - Force overwrite existing configuration
- `aedt init --global` - Initialize global configuration in ~/.aedt/
- `aedt --version` - Display version information
- Colored CLI output (green for success, red for errors)
- Overwrite protection (prevents accidental config deletion)
- Permission error handling
- YAML validation and friendly error messages

### Test Coverage
```
Name                          Stmts   Miss  Cover
-----------------------------------------------------------
aedt/__init__.py                  1      0   100%
aedt/cli/__init__.py              0      0   100%
aedt/cli/main.py                 33      4    88%
aedt/commands/__init__.py         0      0   100%
aedt/core/__init__.py             0      0   100%
aedt/core/config_manager.py      71      4    94%
-----------------------------------------------------------
TOTAL                           105      8    92%
```

### Acceptance Criteria Verification

✅ **AC1: Basic Initialization**
- Creates `.aedt/` directory
- Generates `config.yaml` with default settings
- Displays success message
- Configuration includes max_concurrent, quality_gates, git settings

✅ **AC2: Overwrite Protection**
- Prompts when config already exists
- Requires `--force` flag to overwrite
- Preserves existing config when declined

### Known Issues / Limitations
- Global `--global` tests skipped to avoid modifying real home directory
- Tests use temporary directories for isolation
- Shell environment warnings (gvm) appear but don't affect functionality

### Next Steps
- Story is ready for review by Scrum Master
- All acceptance criteria met
- Test coverage exceeds 80% requirement (92%)
- Manual testing verified CLI functionality
