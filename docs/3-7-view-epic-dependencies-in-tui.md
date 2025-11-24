# Story 3.7: View Epic Dependencies in TUI

Status: review
Epic: 3 - Epic Parsing and Dependency Analysis
Created: 2025-11-23
Completed: 2025-11-24

## Story

As a **user**,
I want **to see which Epics an Epic depends on and their status**,
so that **I understand why an Epic is queued**.

## Acceptance Criteria

### AC1: 显示 Epic 依赖关系
**Given** Epic 4 depends_on=[2, 3]
**And** Epic 2 状态为 "completed"，Epic 3 状态为 "developing"
**When** 在 TUI 中查看 Epic 4 详情
**Then** 依赖关系章节显示：
```
Dependencies:
  - Epic 2: Foundation (✓ Completed)
  - Epic 3: Parser (⚙ Developing)
```

### AC2: 显示无依赖的 Epic
**Given** Epic 1 没有依赖 (depends_on=[])
**When** 查看 Epic 1 详情
**Then** 依赖关系章节显示："None"

### AC3: 状态图标清晰
**When** TUI 显示依赖状态
**Then** 使用清晰的状态图标：
- ✓ (completed) - 已完成
- ⚙ (developing) - 开发中
- ⏳ (queued) - 排队等待
- ✗ (failed) - 失败

## Tasks / Subtasks

### Task 1: 扩展 TUI Epic 详情面板 (AC: 1, 2, 3)
- [ ] 1.1 定位 TUI Epic 面板代码
  - [ ] 在 Epic 8 的 TUI 实现中扩展
  - [ ] 或创建依赖显示组件（如果 TUI 尚未实现）
- [ ] 1.2 添加依赖关系显示区域
  - [ ] 在 Epic 详情面板添加 "Dependencies" 章节
  - [ ] 列出所有 depends_on Epics
  - [ ] 显示每个依赖 Epic 的状态

### Task 2: 查询依赖 Epic 状态 (AC: 1, 3)
- [ ] 2.1 集成 StateManager
  - [ ] 从 StateManager 查询每个依赖 Epic 的状态
  - [ ] 状态值：backlog, contexted, developing, completed, failed
- [ ] 2.2 实现状态映射
  ```python
  STATUS_ICONS = {
      "completed": "✓",
      "developing": "⚙",
      "queued": "⏳",
      "failed": "✗",
      "backlog": "○"
  }
  ```

### Task 3: 格式化依赖显示 (AC: 1, 2)
- [ ] 3.1 实现格式化函数
  ```python
  def format_dependencies(epic: Epic, state_manager) -> str:
      if not epic.depends_on:
          return "None"

      lines = []
      for dep_id in epic.depends_on:
          dep_epic = state_manager.get_epic(dep_id)
          status = dep_epic.status
          icon = STATUS_ICONS.get(status, "?")
          lines.append(f"  - Epic {dep_id}: {dep_epic.title} ({icon} {status.capitalize()})")

      return "\n".join(lines)
  ```
- [ ] 3.2 处理缺失依赖
  - [ ] 如果依赖的 Epic 不存在，显示 "? Unknown"

### Task 4: TUI 交互设计 (AC: 1)
- [ ] 4.1 设计导航流程
  - [ ] 用户选择 Epic → 显示详情面板
  - [ ] 详情面板包含：Title, Description, Status, **Dependencies**, Stories
- [ ] 4.2 实现依赖链导航（可选增强）
  - [ ] 点击依赖 Epic → 跳转到该 Epic 的详情
  - [ ] 支持递归查看依赖链

### Task 5: 数据接口设计 (AC: 1, 2, 3)
- [ ] 5.1 定义 TUI 数据模型
  ```python
  @dataclass
  class EpicDetailView:
      epic: Epic
      dependencies: List[Tuple[Epic, str]]  # (Epic, status_icon)
      stories: List[Story]
      progress: float
  ```
- [ ] 5.2 实现数据提供者
  - [ ] `TUIDataProvider.get_epic_detail(epic_id) -> EpicDetailView`
  - [ ] 聚合 Epic、依赖状态、Stories 信息

### Task 6: 测试 TUI 组件 (AC: 1, 2, 3)
- [ ] 6.1 创建 TUI 单元测试（如果 TUI 框架支持）
  - [ ] 测试依赖显示逻辑
  - [ ] 测试状态图标映射
  - [ ] Mock StateManager
- [ ] 6.2 手动测试场景
  - [ ] Epic 有多个依赖，部分完成
  - [ ] Epic 无依赖
  - [ ] 依赖 Epic 不存在（边界情况）

### Task 7: 集成到 Epic 8 TUI (AC: 1, 2, 3)
- [ ] 7.1 确认 Epic 8 TUI 实现状态
  - [ ] 如果 Epic 8 未开始，创建占位符接口
  - [ ] 如果 Epic 8 已实现，扩展现有组件
- [ ] 7.2 提供数据查询接口
  - [ ] 供 TUI 调用 `get_queued_epics()`（Story 3.6）
  - [ ] 供 TUI 查询 Epic 状态

## Dev Notes

### 架构和设计模式

**模块位置和职责：**
- TUI 组件位置取决于 Epic 8 的实现
- 数据提供者：`aedt/presentation/tui_data_provider.py`（建议）
- 集成 Story 3.6 的 `get_queued_epics()` 和 StateManager

**关键设计决策：**
1. **数据层分离**：TUI 不直接调用 DependencyAnalyzer，通过 DataProvider 中介
2. **状态图标统一**：全局定义状态图标映射，保持 UI 一致性
3. **延迟依赖**：本 Story 提供接口，Epic 8 负责 TUI 实现

**Epic 8 依赖：**
- Story 3.7 定义数据接口和逻辑
- Epic 8 实现 TUI 框架和渲染
- 两者协作完成完整功能

### 技术约束和 NFRs

**性能要求 (NFR6)：**
- TUI 响应时间 < 200ms
- 依赖查询优化：缓存 Epic 状态

**可用性：**
- 清晰的视觉反馈（状态图标）
- 简洁的依赖展示

### Learnings from Previous Stories

**From Story 3.6 (Status: drafted)**
- **复用排队查询**：`get_queued_epics()` 提供 TUI 展示数据
- **缺失依赖信息**：直接用于 UI 显示

**From Story 3.5 (Status: drafted)**
- **并行 Epics 列表**：TUI 可同时显示可启动的 Epics

**TUI 数据流：**
```
TUI Component
    ↓
TUIDataProvider
    ↓ ↓ ↓
DependencyAnalyzer (Story 3.6)
StateManager (Epic 1)
EpicParser (Story 3.1)
```

[Source: docs/3-5-identify-parallelizable-epics.md]
[Source: docs/3-6-identify-queued-epics-waiting-for-dependencies.md]

### Project Structure Notes

**新文件创建（建议）：**
```
aedt/
  presentation/
    tui_data_provider.py       # NEW: TUI 数据提供者
tests/
  unit/
    presentation/
      test_tui_data_provider.py # NEW: 数据提供者测试
```

**依赖关系：**
- **依赖 Story 3.6**：使用 `get_queued_epics()`
- **依赖 Epic 1**：使用 StateManager 查询状态
- **为 Epic 8 准备**：提供 TUI 数据接口

### References

**Tech Spec:**
- [Source: docs/tech-spec-epic-3.md#与-Epic-8-TUI-集成]
- [Source: docs/tech-spec-epic-3.md#Acceptance-Criteria-AC10]

**Epic Definition:**
- [Source: docs/epics.md#Story-3.7]

**Architecture:**
- [Source: docs/architecture.md#Presentation-Layer]
- [Source: docs/architecture.md#TUI-组件]

**PRD:**
- [Source: docs/prd.md#FR10-依赖关系查看]

**Previous Stories:**
- [Source: docs/3-6-identify-queued-epics-waiting-for-dependencies.md]

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

- All tests passed (9 unit tests)
- No debug logs required - implementation was straightforward

### Completion Notes List

**实现总结：**

1. **创建 Presentation 层** - 为 TUI 显示准备了数据接口层，与 Epic 8 TUI 框架解耦

2. **实现的核心模块：**
   - `aedt/presentation/tui_data_provider.py` - TUI 数据提供者
   - `EpicDependencyView` 数据类 - TUI 视图模型
   - `TUIDataProvider` 类 - 依赖视图生成和格式化

3. **关键功能：**
   - `get_epic_dependency_view()` - 获取单个 Epic 的依赖视图
   - `format_dependencies()` - 格式化依赖为 TUI 显示字符串
   - `get_all_epic_views()` - 批量获取所有 Epic 的视图
   - 状态图标映射 (STATUS_ICONS) - 统一的视觉反馈

4. **状态图标实现 (AC3)：**
   - ✓ completed
   - ⚙ developing/in-progress
   - ⏳ queued
   - ✗ failed
   - ○ backlog
   - ◐ contexted
   - ◔ drafted
   - ◑ review

5. **测试覆盖：**
   - 9 个单元测试：依赖视图生成、格式化、状态图标、边界情况
   - **所有测试通过** (耗时 0.06s)

6. **设计决策：**
   - 数据层分离 - TUI 不直接调用 DependencyAnalyzer，通过 DataProvider 中介
   - 视图模型 - `EpicDependencyView` 封装所有 TUI 需要的数据
   - 延迟依赖 - 本 Story 提供接口，Epic 8 负责 TUI 框架实现

7. **为 Epic 8 准备就绪：**
   - 提供完整的数据接口
   - 格式化输出已实现
   - Epic 8 只需调用 `TUIDataProvider` 并渲染结果

8. **示例输出格式 (AC1, AC2)：**
```
Dependencies:
  - Epic 2: Foundation (✓ Completed)
  - Epic 3: Parser (⚙ Developing)

或

Dependencies: None
```

### File List

**NEW:**
- `aedt/presentation/__init__.py` - Presentation 层初始化
- `aedt/presentation/tui_data_provider.py` - TUI 数据提供者 (169 lines)
- `tests/unit/presentation/__init__.py` - Presentation 层测试初始化
- `tests/unit/presentation/test_tui_data_provider.py` - TUI 数据提供者测试 (196 lines, 9 tests)

**MODIFIED:** None

**DELETED:** None
