# Story 3.6: Identify Queued Epics Waiting for Dependencies

Status: review
Epic: 3 - Epic Parsing and Dependency Analysis
Created: 2025-11-23
Completed: 2025-11-24

## Story

As a **user**,
I want **to see which Epics are waiting for dependencies to complete**,
so that **I understand the execution pipeline**.

## Acceptance Criteria

### AC1: 识别排队等待的 Epics
**Given** Epic 4 depends_on=[2, 3]
**And** Epic 2 已完成，Epic 3 仍在开发中
**When** 查询排队的 Epics
**Then** Epic 4 被返回，状态为 "queued"，原因为 "Waiting for: Epic 3"

### AC2: 显示所有缺失的依赖
**Given** Epic 5 depends_on=[2, 3, 4]
**And** 仅 Epic 2 已完成
**When** 查询排队的 Epics
**Then** Epic 5 被返回，缺失依赖列表为 [3, 4]

### AC3: 依赖完成后自动移除排队状态
**Given** Epic 4 在排队等待 Epic 3
**And** Epic 3 完成
**When** 查询排队的 Epics
**Then** Epic 4 不再出现在排队列表中（已变为可并行）

## Tasks / Subtasks

### Task 1: 实现排队 Epic 识别逻辑 (AC: 1, 2, 3)
- [ ] 1.1 在 `aedt/domain/dependency_analyzer.py` 中实现方法
  - [ ] `get_queued_epics(dag: DAG, completed_epic_ids: List[str]) -> List[Tuple[Epic, List[str]]]`
  - [ ] 返回 (Epic, 缺失依赖列表) 元组
- [ ] 1.2 实现查询算法
  - [ ] 遍历 DAG 中的所有 Epic 节点
  - [ ] 跳过已完成的 Epics
  - [ ] 对每个 Epic，检查 depends_on
  - [ ] 如果存在未完成的依赖 → 添加到排队列表
  - [ ] 记录缺失的依赖 IDs

### Task 2: 优化查询和数据结构 (AC: 1, 2)
- [ ] 2.1 使用 Set 优化查找
  - [ ] 转换 completed_epic_ids 为 Set
  - [ ] O(1) 依赖检查
- [ ] 2.2 返回详细信息
  - [ ] Epic 对象
  - [ ] 缺失依赖的 Epic IDs 列表
  - [ ] 可选：缺失依赖的 Epic titles

### Task 3: 与 Story 3.5 互补性验证 (AC: 3)
- [ ] 3.1 确保互斥性
  - [ ] Epic 不应同时出现在 parallel 和 queued 列表中
  - [ ] 单元测试验证：`get_parallel_epics()` + `get_queued_epics()` 覆盖所有未完成 Epics
- [ ] 3.2 一致性检查
  - [ ] 所有 Epics 应属于以下状态之一：
    - 已完成
    - 可并行
    - 排队等待

### Task 4: TUI 集成准备 (AC: 1, 2)
- [ ] 4.1 设计数据接口
  ```python
  # Story 3.7 TUI 将使用
  queued_epics = analyzer.get_queued_epics(dag, completed_ids)
  for epic, missing_deps in queued_epics:
      tui.display(f"Epic {epic.id}: Waiting for {missing_deps}")
  ```
- [ ] 4.2 格式化输出辅助方法
  - [ ] `format_queued_status(epic: Epic, missing_deps: List[str]) -> str`
  - [ ] 示例："Epic 4: Waiting for Epic 2, Epic 3"

### Task 5: 日志记录 (AC: 1, 2, 3)
- [ ] 5.1 实现日志
  - [ ] INFO: 查询排队 Epics，结果数量
  - [ ] DEBUG: 每个排队 Epic 的缺失依赖详情
  - [ ] 日志示例：
    ```
    INFO  [DependencyAnalyzer] Querying queued Epics (2 completed)
    DEBUG [DependencyAnalyzer] Epic 4: missing dependencies [3]
    DEBUG [DependencyAnalyzer] Epic 5: missing dependencies [3, 4]
    INFO  [DependencyAnalyzer] Found 2 queued Epics
    ```

### Task 6: 单元测试 (AC: 1, 2, 3)
- [ ] 6.1 扩展 `tests/unit/domain/test_dependency_analyzer.py`
  - [ ] 测试单个缺失依赖（AC1）
  - [ ] 测试多个缺失依赖（AC2）
  - [ ] 测试依赖完成后的状态变化（AC3）
  - [ ] 测试与 get_parallel_epics() 的互斥性
- [ ] 6.2 边界测试
  - [ ] 所有 Epics 已完成 → 空列表
  - [ ] 所有 Epics 可并行 → 空列表
  - [ ] 混合场景

### Task 7: 集成测试 (AC: 1, 2, 3)
- [ ] 7.1 扩展 `tests/integration/test_dag_construction.py`
  - [ ] 测试完整工作流
  - [ ] 模拟渐进式完成：Epic 1 → Epic 2,3,4 可并行 → Epic 5 排队
  - [ ] 验证排队状态动态更新

## Dev Notes

### 架构和设计模式

**模块位置和职责：**
- `aedt/domain/dependency_analyzer.py` - 实现 `get_queued_epics()` 方法
- 与 Story 3.5 配合：互补的查询功能

**关键设计决策：**
1. **返回缺失依赖列表**：不仅识别排队 Epics，还提供原因（缺失哪些依赖）
2. **与 parallel 查询互补**：两个方法覆盖所有未完成 Epics
3. **TUI 友好输出**：返回结构化数据便于 UI 展示

**算法复杂度：** O(V×D)，与 get_parallel_epics() 相同

### Learnings from Previous Stories

**From Story 3.5 (Status: drafted)**
- **互补关系**：parallel + queued = 所有未完成 Epics
- **相同优化**：使用 Set 查找 completed_ids
- **相同模式**：遍历 DAG 节点，检查依赖

**实现对比：**
```python
# Story 3.5: get_parallel_epics
def get_parallel_epics(dag, completed_ids):
    for epic in dag.nodes.values():
        if epic.id in completed_ids:
            continue
        if all(dep in completed_ids for dep in epic.depends_on):
            yield epic  # 所有依赖已满足

# Story 3.6: get_queued_epics
def get_queued_epics(dag, completed_ids):
    for epic in dag.nodes.values():
        if epic.id in completed_ids:
            continue
        missing = [dep for dep in epic.depends_on if dep not in completed_ids]
        if missing:
            yield (epic, missing)  # 存在未满足依赖
```

[Source: docs/3-5-identify-parallelizable-epics.md]

### References

**Tech Spec:**
- [Source: docs/tech-spec-epic-3.md#DependencyAnalyzer-API-get_queued_epics]
- [Source: docs/tech-spec-epic-3.md#Acceptance-Criteria-AC7]

**Epic Definition:**
- [Source: docs/epics.md#Story-3.6]

**PRD:**
- [Source: docs/prd.md#FR9-Epic-排队管理]

**Previous Stories:**
- [Source: docs/3-3-build-epic-dependency-dag.md]
- [Source: docs/3-5-identify-parallelizable-epics.md]

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

- All tests passed (7 unit tests + 4 integration tests)
- No debug logs required - implementation was straightforward

### Completion Notes List

**实现总结：**

1. **与 Story 3.5 互补** - `get_queued_epics()` 与 `get_parallel_epics()` 配合使用，覆盖所有未完成 Epics

2. **实现的核心方法：**
   - `DependencyAnalyzer.get_queued_epics(dag, completed_epic_ids)` → `List[Tuple[Epic, List[str]]]`
   - 返回 (Epic, 缺失依赖列表) 元组
   - 详细日志记录每个排队 Epic 的缺失依赖

3. **全面测试覆盖：**
   - 7 个单元测试：单个缺失依赖、多个缺失依赖、依赖完成后移除、互斥性验证
   - 4 个集成测试：初始状态、多依赖缺失、状态变化、完整覆盖验证
   - **所有 11 个测试通过**

4. **关键设计决策：**
   - 返回缺失依赖列表 - 不仅识别排队 Epic，还提供原因
   - 与 `get_parallel_epics()` 互斥 - Epic 只能处于一种状态
   - TUI 友好输出 - Tuple 结构便于 UI 展示

5. **互补性验证：**
   - `parallel + queued + completed = all_epics` ✅
   - `parallel ∩ queued = ∅` ✅
   - 集成测试验证完整性

6. **性能表现：**
   - 集成测试总耗时: 0.07s (4 tests)
   - 与 `get_parallel_epics()` 性能相当

7. **为 Story 3.7 TUI 准备就绪：**
   - 提供结构化数据：(Epic, missing_deps)
   - 便于 UI 展示："Epic 4: Waiting for Epic 2, Epic 3"
   - 支持动态更新

### File List

**NEW:** None

**MODIFIED:**
- `aedt/domain/dependency_analyzer.py` - 添加 get_queued_epics() (42 lines added)
- `tests/unit/domain/test_dependency_analyzer.py` - 添加 7 个排队 Epic 单元测试 (158 lines added)
- `tests/integration/test_dag_construction.py` - 添加 4 个排队 Epic 集成测试 (104 lines added)

**DELETED:** None
