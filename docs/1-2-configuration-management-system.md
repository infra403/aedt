# Story 1.2: 配置管理系统

**状态:** review
**Epic:** Epic 1
**Story Key:** 1-2-configuration-management-system
**日期创建:** 2025-11-23

---

## User Story

**As a** 用户
**I want** 通过配置文件自定义 AEDT 行为
**So that** 我可以调整最大并发数、质量门控和 Git 偏好等设置

## Acceptance Criteria

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

## Tasks/Subtasks

### 1. 实现 ConfigManager 核心类 ✅
- [x] 定义配置数据结构（使用 dataclass）
  - [x] `SubagentConfig` (max_concurrent, timeout, model)
  - [x] `QualityGatesConfig` (pre_commit, epic_complete, pre_merge)
  - [x] `GitConfig` (worktree_base, branch_prefix, auto_cleanup)
  - [x] `AEDTConfig` (主配置类)
- [x] 实现配置加载方法 `load()`
- [x] 实现配置访问方法 `get()` (支持嵌套键访问如 "subagent.max_concurrent")
- [x] 实现配置保存方法 `save_config()`

### 2. 实现配置验证逻辑 ✅
- [x] YAML 语法验证（使用 PyYAML safe_load）
- [x] 必需字段验证（version, subagent, quality_gates, git）
- [x] 数据类型验证（int、str、list 等）
- [x] 数值范围验证（max_concurrent > 0, timeout > 0）
- [x] 提供友好的验证错误提示（中文）

### 3. 实现配置热加载机制 ✅
- [x] 使用 watchdog 库监听配置文件变化
- [x] 实现 ConfigFileHandler 事件处理器
- [x] 自动重新加载配置（无需重启）
- [x] 验证失败时保留旧配置
- [x] 记录配置变更日志

### 4. 实现错误处理和用户提示 ✅
- [x] 配置文件不存在 → "请先运行 'aedt init' 初始化配置"
- [x] YAML 语法错误 → "配置文件 YAML 格式错误：{具体错误}"
- [x] 缺少必需字段 → "配置文件缺少必需字段：{field_name}"
- [x] 类型错误 → 说明预期类型和实际类型
- [x] 提供修复建议和期望格式

### 5. 编写单元测试 ✅
- [x] 测试配置加载（有效配置）
- [x] 测试 YAML 语法错误处理
- [x] 测试必需字段缺失处理
- [x] 测试配置热加载机制
- [x] 测试配置验证逻辑（类型、范围）
- [x] 测试 get() 方法（包括嵌套键访问）
- [x] 测试 save_config() 方法
- [x] 测试 reload_config() 方法
- [x] 编写集成测试（39个测试全部通过）

## Dev Notes

### 技术实现细节

**配置数据结构：**
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
```

**配置加载和验证：**
```python
class ConfigManager:
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
```

### 配置文件结构示例
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

### 覆盖的需求
- FR56（用户可以通过配置文件自定义 AEDT 行为）
- NFR14（错误提示友好性）
- NFR19（配置驱动）

### 受影响组件
- ConfigManager (核心实现)
- 所有读取配置的模块（CLI、StateManager、Scheduler 等）

## Dependencies

- **Prerequisites:** Story 1.1 (初始化必须先存在)
- **Tech Spec Reference:** docs/tech-spec-epic-1.md
  - 章节：详细设计 → ConfigManager 模块
  - 章节：数据模型与契约 → 配置文件结构

## File List

### Created/Modified Files
- `aedt/core/config_manager.py` - Enhanced ConfigManager with validation, hot reload, save_config
- `tests/unit/test_config_manager.py` - Comprehensive unit tests (33 tests)
- `tests/integration/test_config_hot_reload.py` - Integration tests for hot reload (6 tests)
- `requirements.txt` - Added watchdog>=3.0.0 dependency

### Test Results
- **Total Tests:** 39 (33 unit + 6 integration)
- **Pass Rate:** 100% (39/39 passed)
- **Coverage:** All functionality tested including:
  - Config loading and validation
  - Nested key access (dot notation)
  - save_config() method
  - Hot reload with watchdog
  - Error handling and Chinese error messages
  - Data class initialization

## Dev Agent Record

- **Context Reference:** docs/1-2-configuration-management-system.context.xml
- **Status History:**
  - 2025-11-23: Created (backlog → drafted)
  - 2025-11-23: Context created (drafted → ready-for-dev)
  - 2025-11-23: Implementation started (ready-for-dev → in-progress)
  - 2025-11-23: Implementation completed (in-progress → review)

- **Implementation Notes:**
  - Enhanced existing ConfigManager from Story 1.1 with new functionality
  - Implemented comprehensive validation with Chinese error messages
  - Added hot reload using watchdog library for automatic config updates
  - Implemented nested key access using dot notation (e.g., "subagent.max_concurrent")
  - Added save_config() method for programmatic config updates
  - QualityGatesConfig __post_init__ ensures empty lists instead of None
  - ConfigFileHandler monitors config.yaml for changes
  - reload_config() preserves old config on validation failure
  - All 39 tests passing (100% pass rate)

- **Acceptance Criteria Verification:**
  - ✅ AC1: ConfigManager successfully loads and validates config.yaml
  - ✅ AC2: Invalid YAML shows friendly error with suggestion to run 'aedt init'
  - ✅ AC3: Missing required fields show specific field names in error
  - ✅ AC4: Hot reload automatically updates config when file changes
  - ✅ AC5: All error messages in Chinese with helpful context
