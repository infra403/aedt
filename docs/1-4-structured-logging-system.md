# Story 1.4: 结构化日志系统

**状态:** review
**Epic:** Epic 1
**Story Key:** 1-4-structured-logging-system
**日期创建:** 2025-11-23

---

## User Story

**As a** 排查问题的开发者
**I want** AEDT 生成具有不同严重级别的结构化日志
**So that** 我可以调试问题并追踪操作

## Acceptance Criteria

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

## Tasks/Subtasks

### 1. 实现 AEDTLogger 核心类
- [x] 使用 Python logging 模块创建自定义日志器
- [x] 实现全局日志器（aedt.log）
- [x] 实现 Epic 专用日志器（epic-<id>.log）
- [x] 配置日志格式和级别

### 2. 实现日志轮转机制
- [x] 使用 RotatingFileHandler
- [x] 单文件最大 10MB
- [x] 保留 5 个历史文件
- [x] 自动清理旧日志

### 3. 实现日志分离逻辑
- [x] 全局日志：所有系统操作
- [x] Epic 日志：特定 Epic 的操作
- [x] 模块日志：按模块分类（可选）

### 4. 实现日志级别过滤
- [x] DEBUG：详细调试信息
- [x] INFO：关键操作记录
- [x] WARNING：潜在问题警告
- [x] ERROR：错误和异常

### 5. 编写单元测试
- [x] 测试日志格式正确性
- [x] 测试日志级别过滤
- [x] 测试日志轮转机制
- [x] 测试 Epic 专用日志创建

## Dev Notes

### 技术实现细节

**AEDTLogger 类：**
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

### 日志格式示例
```
[2025-11-23 10:23:45] [INFO] [aedt.scheduler] Epic 2 started with 5 stories
[2025-11-23 10:23:46] [DEBUG] [aedt.git] Creating worktree at .aedt/worktrees/epic-2
[2025-11-23 10:23:47] [WARNING] [aedt.quality] Linter warning in Story 2.1
[2025-11-23 10:23:48] [ERROR] [aedt.subagent] Subagent crashed: timeout exceeded
```

### 日志目录结构
```
.aedt/
├── logs/
│   ├── aedt.log             # 全局日志
│   ├── aedt.log.1           # 轮转日志备份
│   ├── aedt.log.2
│   └── ...
├── projects/
│   └── {project-name}/
│       └── epics/
│           ├── epic-1.log   # Epic 1 专用日志
│           ├── epic-2.log   # Epic 2 专用日志
│           └── ...
```

### 日志级别使用指南
- **DEBUG**：详细调试信息（如 Git 命令输出、配置加载详情）
- **INFO**：关键操作记录（如 Epic 启动、Story 完成、合并成功）
- **WARNING**：潜在问题警告（如质量检查警告、Worktree 路径不存在）
- **ERROR**：错误和异常（如 Subagent 崩溃、Git 操作失败）

### 覆盖的需求
- FR57（系统可以生成结构化日志）
- NFR20（日志完整性）
- NFR30（日志可追溯性）

### 受影响组件
- Logger (新建)
- 所有组件（都需要记录日志）

## Dependencies

- **Prerequisites:** Story 1.1 (日志目录必须存在)
- **Tech Spec Reference:** docs/tech-spec-epic-1.md
  - 章节：详细设计 → Logger 模块
  - 章节：非功能需求 → 可观测性

## File List

**新增文件:**
- `aedt/core/logger.py` - AEDTLogger 类实现（全局日志、Epic日志、日志轮转）
- `tests/unit/test_logger.py` - AEDTLogger 单元测试（14个测试）

## Dev Agent Record

- **Context Reference:** docs/1-4-structured-logging-system.context.xml
- **Status History:**
  - 2025-11-23: Created (backlog → drafted)
  - 2025-11-23: Context created (drafted → ready-for-dev)
  - 2025-11-23: Implementation completed (ready-for-dev → in-progress → review)

- **Completion Notes:**
  - 实现了完整的结构化日志系统，支持全局日志和Epic专用日志
  - 使用 RotatingFileHandler 实现日志轮转（10MB，保留5个备份）
  - 实现了日志级别过滤（DEBUG/INFO/WARNING/ERROR）
  - Epic 日志器使用唯一名称（包含项目名）避免缓存冲突：`aedt.{project_name}.epic.{epic_id}`
  - 日志分离通过 `propagate = False` 实现，Epic日志不会混入全局日志
  - 所有14个单元测试通过，覆盖日志格式、轮转、分离、级别过滤、UTF-8支持等
  - 日志格式：`[timestamp] [level] [module] message`
  - 支持模块日志器通过 `get_logger(name)` 获取，自动继承全局日志器配置
