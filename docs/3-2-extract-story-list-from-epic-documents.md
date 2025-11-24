# Story 3.2: Extract Story List from Epic Documents

Status: review
Epic: 3 - Epic Parsing and Dependency Analysis
Created: 2025-11-23

## Story

As a **user**,
I want **AEDT to parse the Story list within each Epic document**,
so that **Subagents know what tasks to complete**.

## Acceptance Criteria

### AC1: 提取 Story 列表
**Given** Epic 文档包含 "Stories" 章节，有编号的项目：
```
1. Story 1.1: Initialize CLI
2. Story 1.2: Config Management
```
**When** AEDT 解析该 Epic
**Then** Epic.stories 数组包含 2 个 Story 对象
**And** Story 1 包含：id="1.1", title="Initialize CLI", status="pending"

### AC2: 提取 Story Prerequisites
**Given** Story 有 "Prerequisites" 子章节列出依赖关系
**When** AEDT 解析该 Story
**Then** Story.prerequisites 字段被正确填充
**And** 可用于 Story 级别 DAG 构建（multi 模式）

### AC3: 处理无 Stories 的 Epic
**Given** Epic 没有 Stories 章节
**When** AEDT 解析该 Epic
**Then** Epic.stories 数组为空
**And** 记录警告日志："Epic <id> has no Stories defined"

## Tasks / Subtasks

### Task 1: 实现 Markdown Story 解析逻辑 (AC: 1, 3)
- [x] 1.1 在 `aedt/domain/epic_parser.py` 中实现 `parse_stories(epic_content: str) -> List[Story]` 方法
  - [x] 使用 Markdown 解析库（`markdown-it-py` 或 `mistune`）
  - [x] 定位 "Stories" 或 "## Stories" 章节
  - [x] 识别编号列表或子标题（"### Story X.Y"）
- [x] 1.2 提取 Story 元数据
  - [x] Story ID（如 "3.2" 从 "Story 3.2: Title" 中提取）
  - [x] Story 标题
  - [x] Story 描述（从 Markdown 内容提取）
- [x] 1.3 创建 Story 对象列表
  - [x] 初始化 status="pending"
  - [x] 设置 prerequisites=[]（后续任务填充）
- [x] 1.4 处理无 Stories 章节的情况
  - [x] 返回空列表
  - [x] 记录 WARNING 日志

### Task 2: 实现 Prerequisites 提取 (AC: 2)
- [x] 2.1 扩展 `parse_stories()` 解析 Prerequisites
  - [x] 在每个 Story 的 Markdown 内容中查找 "Prerequisites" 子章节
  - [x] 支持多种格式：
    - YAML 块：`prerequisites: [3.1]`
    - Markdown 列表：`- Story 3.1`
    - 文本引用：`Requires Story 3.1`
- [x] 2.2 规范化 Prerequisites 格式
  - [x] 将所有格式转换为统一的 Story ID 列表
  - [x] 验证 Story ID 格式（X.Y 格式）
  - [x] 去重和排序

### Task 3: 实现 Story 领域模型 (AC: 1, 2)
- [x] 3.1 创建或更新 `aedt/domain/models/story.py` 模块
  - [x] 定义 `Story` dataclass
  - [x] 字段：id, title, description, prerequisites, status, commit_hash, agent_id
- [x] 3.2 实现 `Story.validate(epic_stories: List[str])` 方法
  - [x] 验证 id 和 title 非空
  - [x] 验证 prerequisites 中的 Story IDs 存在于 epic_stories 中
  - [x] 返回 (bool, Optional[str]) 元组

### Task 4: 集成到 Epic 解析流程 (AC: 1, 2, 3)
- [x] 4.1 更新 `EpicParser.parse_single_epic()` 方法
  - [x] 提取 Epic 的 Markdown 内容（除去 frontmatter）
  - [x] 调用 `parse_stories(epic_content)`
  - [x] 将解析的 Story 列表赋值给 `Epic.stories`
- [x] 4.2 验证 Story 列表的一致性
  - [x] Epic ID 和 Story ID 的前缀匹配（Epic 3 的 Stories 应为 3.X）
  - [x] 警告：如果 Story ID 不匹配

### Task 5: 支持多种 Story 定义格式 (AC: 1)
- [x] 5.1 支持编号列表格式
  ```markdown
  ## Stories
  1. Story 3.1: Parse Epic Documents
  2. Story 3.2: Extract Story List
  ```
- [x] 5.2 支持子标题格式
  ```markdown
  ### Story 3.1: Parse Epic Documents
  Description...
  ### Story 3.2: Extract Story List
  Description...
  ```
- [x] 5.3 混合格式兼容性测试

### Task 6: 错误处理和日志 (AC: 3)
- [x] 6.1 处理 Markdown 解析错误
  - [x] 捕获解析库异常
  - [x] 记录 WARNING 并返回空 Story 列表
- [x] 6.2 完善日志记录
  - [x] INFO: 成功解析 N 个 Stories
  - [x] WARNING: Epic 无 Stories、Story ID 格式错误、Prerequisites 无效
  - [x] DEBUG: 每个 Story 的详细解析信息

### Task 7: 单元测试 (AC: 1, 2, 3)
- [x] 7.1 扩展 `tests/unit/domain/test_epic_parser.py`
  - [x] 测试 parse_stories() 基本功能
  - [x] 测试编号列表格式
  - [x] 测试子标题格式
  - [x] 测试 Prerequisites 提取
  - [x] 测试空 Stories 章节
- [x] 7.2 创建测试 fixtures
  - [x] `tests/fixtures/epics/epic-with-stories-list.md`
  - [x] `tests/fixtures/epics/epic-with-stories-headings.md`
  - [x] `tests/fixtures/epics/epic-no-stories.md`
  - [x] `tests/fixtures/epics/epic-with-prerequisites.md`
- [x] 7.3 测试 Story 模型验证逻辑

### Task 8: 集成测试 (AC: 1, 2, 3)
- [x] 8.1 更新 `tests/integration/test_epic_parsing_e2e.py`
  - [x] 测试完整的 Epic + Stories 解析
  - [x] 验证 Epic.stories 列表正确填充
  - [x] 测试 Prerequisites 的 DAG 构建（预览 Story 3.4）
- [x] 8.2 测试真实 Epic 文档
  - [x] 使用项目实际的 epics.md 作为测试输入
  - [x] 验证 Epic 3 的 8 个 Stories 被正确解析

## Dev Notes

### 架构和设计模式

**模块位置和职责：**
- `aedt/domain/epic_parser.py` - 添加 `parse_stories()` 方法
- `aedt/domain/models/story.py` - 新建：Story 领域模型
- 依赖 Story 3.1 的 `parse_single_epic()` 方法

**关键设计决策：**
1. **多格式支持**：兼容编号列表和子标题两种 Story 定义格式，增强灵活性
2. **Prerequisites 规范化**：统一多种 Prerequisites 表示方式为标准格式
3. **惰性验证**：Story 的 prerequisites 验证在 DAG 构建时进行（Story 3.4），解析时仅提取

**依赖库：**
- `markdown-it-py>=2.0.0` - Markdown 解析（需添加到 requirements.txt）
- 或 `mistune>=2.0.0` - 备选 Markdown 解析器

### 技术约束和 NFRs

**性能要求 (NFR6)：**
- Story 列表提取应在 Epic 解析的 50ms 预算内完成
- 支持 Epic 包含 100+ Stories（虽然实际项目不太可能）

**可靠性 (NFR16)：**
- Story 解析失败不影响 Epic 对象创建
- Epic.stories 可以为空列表，系统继续运行

**模块独立性 (NFR17)：**
- `parse_stories()` 方法独立可测试
- Story 模型独立于 Epic 模型

### Learnings from Previous Story

**From Story 3.1 (Status: drafted)**

Story 3.1 实现了 Epic 文档解析的基础设施，本 Story 3.2 将直接扩展该功能：

- **复用 EpicParser 类**：在 `aedt/domain/epic_parser.py` 中添加 `parse_stories()` 方法，而不是创建新模块
- **复用 Epic 模型**：Epic.stories 字段已在 Story 3.1 中定义，本 Story 负责填充该字段
- **复用测试框架**：扩展 `tests/unit/domain/test_epic_parser.py`，添加 Story 解析测试用例
- **复用错误处理模式**：采用与 Epic 解析相同的容错策略（单个 Story 失败不阻塞整体）

**注意事项：**
- 确保 Story 3.1 已完成并通过测试后再开始本 Story 的实施
- 新增的 `python-frontmatter` 和 `markdown-it-py` 依赖应在 Story 3.1 中已添加

[Source: docs/3-1-parse-bmad-epic-documents-and-extract-metadata.md]

### Project Structure Notes

**修改的文件：**
```
aedt/
  domain/
    epic_parser.py          # MODIFIED: 添加 parse_stories() 方法
    models/
      story.py              # NEW: Story 领域模型
tests/
  unit/
    domain/
      test_epic_parser.py   # MODIFIED: 添加 Story 解析测试
  integration/
    test_epic_parsing_e2e.py # MODIFIED: 添加 Stories 集成测试
  fixtures/
    epics/
      epic-with-stories-list.md      # NEW: 测试 fixture
      epic-with-stories-headings.md  # NEW: 测试 fixture
      epic-no-stories.md             # NEW: 测试 fixture
```

**依赖关系：**
- **依赖 Story 3.1**：必须先完成 Epic 基本解析
- **为 Story 3.4 准备**：提取的 prerequisites 数据将用于构建 Story DAG

### References

**Tech Spec:**
- [Source: docs/tech-spec-epic-3.md#Story-领域模型]
- [Source: docs/tech-spec-epic-3.md#EpicParser-API]
- [Source: docs/tech-spec-epic-3.md#Acceptance-Criteria-AC3]

**Epic Definition:**
- [Source: docs/epics.md#Story-3.2]

**Architecture:**
- [Source: docs/architecture.md#Domain-Layer]

**PRD:**
- [Source: docs/prd.md#FR13-Story-列表提取]

**Previous Story:**
- [Source: docs/3-1-parse-bmad-epic-documents-and-extract-metadata.md]

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

实现发现：
- 代码已在 Story 3.1 实现中完成，包括 parse_stories() 方法、Story 模型、Prerequisites 提取
- 缺失单元测试和集成测试
- Prerequisites 提取正则表达式需优化以支持 "Requires Story X.Y and Story A.B" 格式

修复：
- 更新 `_extract_prerequisites()` 方法的正则以支持多个 Story ID 在同一行
- 使用 `re.finditer()` 查找包含关键词的整行，然后提取所有 Story ID
- 添加 13 个单元测试（TestParseStories, TestExtractPrerequisites）
- 添加 test_story.py 11 个测试
- 添加 5 个集成测试（TestStoryParsingE2E）

### Completion Notes List

**代码复用：**
- Story 3.1 已实现核心功能：parse_stories(), _parse_stories_from_numbered_list(), _parse_stories_from_headings()
- Story 模型已完整，包含验证逻辑

**新增测试：**
- tests/unit/domain/test_epic_parser.py: 添加 TestParseStories (7 tests) 和 TestExtractPrerequisites (6 tests)
- tests/unit/domain/test_story.py: 新建文件，11 个 Story 模型测试
- tests/integration/test_epic_parsing_e2e.py: 添加 TestStoryParsingE2E (5 tests)

**Prerequisites 提取逻辑：**
- 支持 3 种格式：YAML ([3.1, 3.2])、Markdown 列表 (- Story 3.1)、文本引用 (Requires Story 3.1 and Story 3.2)
- 正则优化：使用 MULTILINE 匹配包含关键词的整行，提取所有 Story ID
- 自动去重和排序

**测试覆盖率：**
- 所有 AC 覆盖（AC1: Story 提取, AC2: Prerequisites, AC3: 无 Stories 处理）
- 24 个新测试，全部通过

### File List

**MODIFIED**:
- aedt/domain/epic_parser.py (优化 Prerequisites 提取正则)
- tests/unit/domain/test_epic_parser.py (添加 13 个测试)
- tests/integration/test_epic_parsing_e2e.py (添加 5 个测试)
- docs/3-2-extract-story-list-from-epic-documents.md (标记完成，Status: review)

**NEW**:
- tests/unit/domain/test_story.py (11 个 Story 模型测试)
