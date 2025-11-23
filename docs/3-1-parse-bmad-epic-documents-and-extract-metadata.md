# Story 3.1: Parse BMAD Epic Documents and Extract Metadata

Status: drafted
Epic: 3 - Epic Parsing and Dependency Analysis
Created: 2025-11-23

## Story

As a **user**,
I want **AEDT to read Epic files from `docs/epics/*.md` and extract their metadata**,
so that **the system knows what Epics exist and their properties**.

## Acceptance Criteria

### AC1: 成功解析有效 Epic 文档
**Given** 项目目录下存在 `docs/epics/epic-001-foundation.md` 文件
**And** 文件包含有效的 YAML frontmatter，定义了 `epic_id`, `title`, `depends_on`, `priority`
**When** AEDT 解析项目
**Then** 创建一个 Epic 对象，包含：id="1", title="Foundation", depends_on=[], priority="HIGH"

### AC2: 处理无效 YAML frontmatter
**Given** Epic 文件包含无效的 YAML frontmatter 语法
**When** AEDT 解析该文件
**Then** 记录警告日志："Epic file <path> has invalid frontmatter. Skipping."
**And** 该 Epic 不被添加到项目中

### AC3: 处理缺失必填字段
**Given** Epic 文件缺少必填字段（`epic_id` 或 `title`）
**When** AEDT 解析该文件
**Then** 记录警告日志："Epic file <path> missing required field: <field>"
**And** 该 Epic 不被添加

## Tasks / Subtasks

### Task 1: 实现 EpicParser 核心类和解析逻辑 (AC: 1, 2, 3)
- [ ] 1.1 创建 `aedt/domain/epic_parser.py` 模块
  - [ ] 定义 `EpicParser` 类
  - [ ] 实现 `__init__(self, config_manager, logger)` 构造函数
- [ ] 1.2 实现 `parse_epics(project_path: str) -> List[Epic]` 方法
  - [ ] 使用 glob 模式匹配 `docs/epics/*.md` 文件
  - [ ] 遍历所有匹配的文件
  - [ ] 对每个文件调用 `parse_single_epic()`
  - [ ] 收集成功解析的 Epic 对象
  - [ ] 记录解析统计（成功/失败数量）
- [ ] 1.3 实现 `parse_single_epic(file_path: str) -> Optional[Epic]` 方法
  - [ ] 读取文件内容
  - [ ] 提取 YAML frontmatter（使用 `python-frontmatter` 库）
  - [ ] 验证元数据（调用 `_validate_metadata()`）
  - [ ] 创建并返回 Epic 对象
  - [ ] 错误处理：文件读取失败、YAML 解析失败

### Task 2: 实现 YAML 元数据提取和验证 (AC: 1, 2, 3)
- [ ] 2.1 实现 `_extract_yaml_frontmatter(content: str) -> dict` 方法
  - [ ] 使用 `frontmatter.loads()` 解析内容
  - [ ] 使用 `yaml.safe_load()` 确保安全解析
  - [ ] 捕获 YAML 语法错误并返回 None
- [ ] 2.2 实现 `_validate_metadata(metadata: dict) -> Tuple[bool, Optional[str]]` 方法
  - [ ] 检查必填字段：`epic_id` (int), `title` (str)
  - [ ] 验证可选字段类型：`depends_on` (List[int]), `priority` (str), `execution_mode` (str)
  - [ ] 返回验证结果和错误消息

### Task 3: 实现 Epic 领域模型 (AC: 1)
- [ ] 3.1 创建 `aedt/domain/models/epic.py` 模块
  - [ ] 定义 `Epic` dataclass，包含所有必需字段
  - [ ] 字段：id, title, description, depends_on, priority, execution_mode, story_concurrency, stories, status, progress, agent_id, worktree_path, created_at, updated_at
- [ ] 3.2 实现 `Epic.validate()` 方法
  - [ ] 验证 id 和 title 非空
  - [ ] 返回 (bool, Optional[str]) 元组

### Task 4: 集成 ConfigManager 和 Logger (AC: 1, 2, 3)
- [ ] 4.1 从 ConfigManager 读取 Epic 文档路径配置
  - [ ] 读取 `epic_docs_path` 配置项（默认：`docs/epics/`）
  - [ ] 读取 `epic_file_pattern` 配置项（默认：`epic-*.md`）
- [ ] 4.2 实现完整的日志记录
  - [ ] INFO：开始解析、成功解析 Epic、解析完成统计
  - [ ] WARNING：无效 YAML、缺失字段、文件读取失败
  - [ ] ERROR：严重错误（如权限问题）
  - [ ] DEBUG：每个文件的详细解析过程

### Task 5: 错误处理和容错 (AC: 2, 3)
- [ ] 5.1 实现文件读取错误处理
  - [ ] 捕获 FileNotFoundError、PermissionError
  - [ ] 记录警告但继续解析其他文件
- [ ] 5.2 实现 YAML 解析错误处理
  - [ ] 捕获 yaml.YAMLError
  - [ ] 记录无效格式的文件路径
  - [ ] 跳过该文件继续处理
- [ ] 5.3 实现字段验证错误处理
  - [ ] 缺失必填字段时记录详细错误
  - [ ] 类型错误时记录字段名和期望类型

### Task 6: 单元测试 (AC: 1, 2, 3)
- [ ] 6.1 创建 `tests/unit/domain/test_epic_parser.py`
  - [ ] 测试 parse_epics() 成功场景
  - [ ] 测试 parse_single_epic() 有效文档
  - [ ] 测试无效 YAML 处理
  - [ ] 测试缺失必填字段
  - [ ] Mock ConfigManager 和 Logger
- [ ] 6.2 创建测试 fixtures
  - [ ] `tests/fixtures/epics/valid-epic-001.md`
  - [ ] `tests/fixtures/epics/invalid-yaml.md`
  - [ ] `tests/fixtures/epics/missing-epic-id.md`
- [ ] 6.3 测试覆盖率目标：>= 90%

### Task 7: 集成测试 (AC: 1, 2, 3)
- [ ] 7.1 创建 `tests/integration/test_epic_parsing_e2e.py`
  - [ ] 端到端测试：创建真实 Epic 文件 → 解析 → 验证结果
  - [ ] 测试多个 Epic 文件的批量解析
  - [ ] 验证与 StateManager 的集成
- [ ] 7.2 测试混合场景
  - [ ] 部分有效、部分无效的 Epic 文件
  - [ ] 验证系统继续运行且报告正确

## Dev Notes

### 架构和设计模式

**模块位置和职责：**
- `aedt/domain/epic_parser.py` - Epic 解析器（领域层）
- `aedt/domain/models/epic.py` - Epic 领域模型
- 依赖 Epic 1 的 ConfigManager 和 Logger（基础设施层）

**关键设计决策：**
1. **容错解析策略**：单个 Epic 解析失败不阻塞其他 Epic，确保系统健壮性
2. **安全的 YAML 解析**：使用 `yaml.safe_load()` 防止反序列化漏洞
3. **清晰的错误消息**：为用户提供可操作的错误提示，包括文件路径和缺失字段

**依赖库：**
- `python-frontmatter>=1.0.0` - YAML frontmatter 提取（需添加到 requirements.txt）
- `PyYAML>=6.0` - YAML 解析（已存在）

### 技术约束和 NFRs

**性能要求 (NFR6)：**
- 单个 Epic 文档解析 < 50ms
- 支持 50+ Epic 文件，总解析时间 < 3 秒

**可靠性 (NFR16)：**
- Epic 解析失败不导致系统崩溃
- 提供降级处理：格式错误时跳过该文件

**日志完整性 (NFR20)：**
- DEBUG: 每个文件的详细解析过程
- INFO: Epic 解析成功
- WARNING: 格式错误、缺失字段
- ERROR: 文件读取失败

**安全 (NFR - Security)：**
- 使用 `safe_load()` 防止 YAML 反序列化攻击
- 验证文件路径在允许的目录内（防止路径遍历）

### Project Structure Notes

**新文件创建：**
```
aedt/
  domain/
    epic_parser.py          # 新建：Epic 解析器
    models/
      epic.py               # 新建：Epic 领域模型
tests/
  unit/
    domain/
      test_epic_parser.py   # 新建：单元测试
  integration/
    test_epic_parsing_e2e.py # 新建：集成测试
  fixtures/
    epics/
      valid-epic-001.md     # 新建：测试 fixture
      invalid-yaml.md       # 新建：测试 fixture
```

**依赖关系：**
- 读取：`ConfigManager` (Epic 1)
- 读取：`Logger` (Epic 1)
- 后续集成：`StateManager` (Epic 1) - 用于持久化解析结果

### References

**Tech Spec:**
- [Source: docs/tech-spec-epic-3.md#EpicParser-模块]
- [Source: docs/tech-spec-epic-3.md#Epic-领域模型]
- [Source: docs/tech-spec-epic-3.md#Acceptance-Criteria-AC1-AC3]

**Epic Definition:**
- [Source: docs/epics.md#Story-3.1]

**Architecture:**
- [Source: docs/architecture.md#Domain-Layer]
- [Source: docs/architecture.md#Data-Models]

**PRD:**
- [Source: docs/prd.md#FR6-Epic-文档读取和解析]

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent during implementation_

### Completion Notes List

_To be filled by dev agent after completion:_
- New patterns/services created
- Architectural deviations or decisions
- Technical debt deferred
- Warnings or recommendations for next story
- Interfaces/methods created for reuse

### File List

_To be filled by dev agent:_
- **NEW**: Files created
- **MODIFIED**: Files modified
- **DELETED**: Files deleted
