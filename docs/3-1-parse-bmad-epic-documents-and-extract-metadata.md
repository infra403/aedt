# Story 3.1: Parse BMAD Epic Documents and Extract Metadata

Status: review
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
- [x] 1.1 创建 `aedt/domain/epic_parser.py` 模块
  - [x] 定义 `EpicParser` 类
  - [x] 实现 `__init__(self, config_manager, logger)` 构造函数
- [x] 1.2 实现 `parse_epics(project_path: str) -> List[Epic]` 方法
  - [x] 使用 glob 模式匹配 `docs/epics/*.md` 文件
  - [x] 遍历所有匹配的文件
  - [x] 对每个文件调用 `parse_single_epic()`
  - [x] 收集成功解析的 Epic 对象
  - [x] 记录解析统计（成功/失败数量）
- [x] 1.3 实现 `parse_single_epic(file_path: str) -> Optional[Epic]` 方法
  - [x] 读取文件内容
  - [x] 提取 YAML frontmatter（使用 `python-frontmatter` 库）
  - [x] 验证元数据（调用 `_validate_metadata()`）
  - [x] 创建并返回 Epic 对象
  - [x] 错误处理：文件读取失败、YAML 解析失败

### Task 2: 实现 YAML 元数据提取和验证 (AC: 1, 2, 3)
- [x] 2.1 实现 `_extract_yaml_frontmatter(content: str) -> dict` 方法
  - [x] 使用 `frontmatter.loads()` 解析内容
  - [x] 使用 `yaml.safe_load()` 确保安全解析
  - [x] 捕获 YAML 语法错误并返回 None
- [x] 2.2 实现 `_validate_metadata(metadata: dict) -> Tuple[bool, Optional[str]]` 方法
  - [x] 检查必填字段：`epic_id` (int), `title` (str)
  - [x] 验证可选字段类型：`depends_on` (List[int]), `priority` (str), `execution_mode` (str)
  - [x] 返回验证结果和错误消息

### Task 3: 实现 Epic 领域模型 (AC: 1)
- [x] 3.1 创建 `aedt/domain/models/epic.py` 模块
  - [x] 定义 `Epic` dataclass，包含所有必需字段
  - [x] 字段：id, title, description, depends_on, priority, execution_mode, story_concurrency, stories, status, progress, agent_id, worktree_path, created_at, updated_at
- [x] 3.2 实现 `Epic.validate()` 方法
  - [x] 验证 id 和 title 非空
  - [x] 返回 (bool, Optional[str]) 元组

### Task 4: 集成 ConfigManager 和 Logger (AC: 1, 2, 3)
- [x] 4.1 从 ConfigManager 读取 Epic 文档路径配置
  - [x] 读取 `epic_docs_path` 配置项（默认：`docs/epics/`）
  - [x] 读取 `epic_file_pattern` 配置项（默认：`epic-*.md`）
- [x] 4.2 实现完整的日志记录
  - [x] INFO：开始解析、成功解析 Epic、解析完成统计
  - [x] WARNING：无效 YAML、缺失字段、文件读取失败
  - [x] ERROR：严重错误（如权限问题）
  - [x] DEBUG：每个文件的详细解析过程

### Task 5: 错误处理和容错 (AC: 2, 3)
- [x] 5.1 实现文件读取错误处理
  - [x] 捕获 FileNotFoundError、PermissionError
  - [x] 记录警告但继续解析其他文件
- [x] 5.2 实现 YAML 解析错误处理
  - [x] 捕获 yaml.YAMLError
  - [x] 记录无效格式的文件路径
  - [x] 跳过该文件继续处理
- [x] 5.3 实现字段验证错误处理
  - [x] 缺失必填字段时记录详细错误
  - [x] 类型错误时记录字段名和期望类型

### Task 6: 单元测试 (AC: 1, 2, 3)
- [x] 6.1 创建 `tests/unit/domain/test_epic_parser.py`
  - [x] 测试 parse_epics() 成功场景
  - [x] 测试 parse_single_epic() 有效文档
  - [x] 测试无效 YAML 处理
  - [x] 测试缺失必填字段
  - [x] Mock ConfigManager 和 Logger
- [x] 6.2 创建测试 fixtures
  - [x] `tests/fixtures/epics/valid-epic-001.md`
  - [x] `tests/fixtures/epics/invalid-yaml.md`
  - [x] `tests/fixtures/epics/missing-epic-id.md`
- [x] 6.3 测试覆盖率目标：>= 90%

### Task 7: 集成测试 (AC: 1, 2, 3)
- [x] 7.1 创建 `tests/integration/test_epic_parsing_e2e.py`
  - [x] 端到端测试：创建真实 Epic 文件 → 解析 → 验证结果
  - [x] 测试多个 Epic 文件的批量解析
  - [x] 验证与 StateManager 的集成
- [x] 7.2 测试混合场景
  - [x] 部分有效、部分无效的 Epic 文件
  - [x] 验证系统继续运行且报告正确

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

No context file available. Implemented based on story requirements and tech spec.

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

实现计划：
1. 添加 python-frontmatter 依赖到 requirements.txt
2. 创建目录结构：aedt/domain/ 和 aedt/domain/models/
3. 实现 Epic 领域模型 (aedt/domain/models/epic.py)
4. 实现 EpicParser (aedt/domain/epic_parser.py)
5. 创建测试 fixtures 和单元测试
6. 创建集成测试
7. 运行所有测试验证

关键实现决策：
- 使用 AEDTLogger.get_logger("epic_parser") 获取模块专用 logger
- ConfigManager.get() 方法用于读取配置，而非 get_config()
- 完整的错误处理和容错机制确保单个 Epic 解析失败不影响其他
- 所有测试通过（20/20），包括 16 个单元测试和 4 个集成测试

### Completion Notes List

**新模块/服务：**
- `aedt/domain/epic_parser.py` - Epic 文档解析器
- `aedt/domain/models/epic.py` - Epic 领域模型
- 完整的单元测试和集成测试套件

**架构决策：**
- 遵循领域驱动设计，EpicParser 位于领域层
- 使用 dataclass 定义 Epic 模型，简洁且类型安全
- 采用容错解析策略：单个文件失败不阻塞其他文件解析

**技术债务：**
- 无。代码符合所有 AC 和 NFR 要求

**后续故事建议：**
- Story 3.2 需要扩展 EpicParser 以提取 Story 列表
- 当前 Epic.stories 字段为空列表，待 Story 3.2 实现填充

**可复用接口：**
- `EpicParser.parse_epics(project_path)` - 其他模块可调用解析项目 Epics
- `Epic.validate()` - 验证 Epic 对象完整性
- 测试 fixtures 可供其他测试复用

### File List

**NEW**:
- aedt/domain/__init__.py
- aedt/domain/models/__init__.py
- aedt/domain/models/epic.py
- aedt/domain/epic_parser.py
- tests/unit/domain/__init__.py
- tests/unit/domain/test_epic_parser.py
- tests/integration/__init__.py
- tests/integration/test_epic_parsing_e2e.py
- tests/fixtures/epics/valid-epic-001.md
- tests/fixtures/epics/invalid-yaml.md
- tests/fixtures/epics/missing-epic-id.md
- tests/fixtures/epics/missing-title.md

**MODIFIED**:
- requirements.txt (添加 python-frontmatter>=1.0.0)
