# Story 3.4: Build Story Dependency DAG (Multi 模式支持)

Status: drafted
Epic: 3 - Epic Parsing and Dependency Analysis
Created: 2025-11-23

## Story

As a **developer**,
I want **the system to analyze Story-level dependencies (prerequisites)**,
so that **Story-level Subagents can be scheduled in the correct order during multi-mode execution**.

## Acceptance Criteria

### AC1: 构建 Story 级别 DAG
**Given** Epic 包含多个 Stories，每个 Story 定义了 prerequisites
**When** 系统在 multi-mode 下解析该 Epic
**Then** 系统应该：
- 提取每个 Story 的 `prerequisites` 字段
- 构建 Story 级别的 DAG（有向无环图）
- 检测 Story 级别的循环依赖
- 返回可并行运行的 Story 列表
- 返回必须等待 prerequisites 的 Story 列表

### AC2: 验证 Story Prerequisites
**Given** Story 定义了 prerequisites
**When** 系统验证 Story prerequisites
**Then** 系统应该验证：
- 所有 prerequisite Story IDs 存在于同一 Epic 内
- 没有前向依赖（仅允许向后或并行依赖）
- 没有循环依赖被检测到

### AC3: 识别可并行的 Stories
**Given** Epic 包含 3 个 Stories：
- Story 3.1: prerequisites=[]
- Story 3.2: prerequisites=["3.1"]
- Story 3.3: prerequisites=["3.1", "3.2"]
**And** Story 3.1 已完成
**When** 系统查询可并行的 Stories
**Then** 返回 [Story 3.2]（依赖已满足）
**And** Story 3.3 仍在等待 Story 3.2

## Tasks / Subtasks

### Task 1: 扩展 DependencyAnalyzer 支持 Story DAG (AC: 1)
- [ ] 1.1 在 `aedt/domain/dependency_analyzer.py` 中添加方法
  - [ ] 实现 `build_story_dag(stories: List[Story]) -> DAG`
  - [ ] 复用 Story 3.3 的 DAG 类
- [ ] 1.2 实现 Story DAG 构建逻辑
  - [ ] 遍历 Stories，为每个 Story 调用 `dag.add_node(story.id, story)`
  - [ ] 遍历每个 Story 的 prerequisites
  - [ ] 为每个 prerequisite 调用 `dag.add_edge(story.id, prereq_id)`
  - [ ] 验证所有 prerequisites 存在于 Epic 内

### Task 2: 实现 Story Prerequisites 验证 (AC: 2)
- [ ] 2.1 实现 `validate_story_prerequisites(stories: List[Story]) -> Tuple[bool, Optional[str]]`
  - [ ] 构建 Story ID 集合
  - [ ] 遍历每个 Story 的 prerequisites
  - [ ] 检查 prerequisite ID 是否在集合中
  - [ ] 验证 prerequisite 不是前向依赖（Story ID 顺序检查）
- [ ] 2.2 循环依赖检测
  - [ ] 调用 `dag.has_cycle()`（复用 Story 3.3）
  - [ ] 如果检测到循环，识别循环路径
  - [ ] 抛出 `CircularDependencyError` 包含详细信息
- [ ] 2.3 前向依赖检查（可选，基于编号顺序）
  - [ ] 检查 Story 3.2 不应依赖 Story 3.3（前向）
  - [ ] 记录 WARNING 如果检测到前向依赖

### Task 3: 实现 Story 并行查询 (AC: 3)
- [ ] 3.1 在 `DependencyAnalyzer` 中添加方法
  - [ ] 实现 `get_parallel_stories(dag: DAG, completed_story_ids: List[str]) -> List[Story]`
  - [ ] 复用 `dag.get_parallel_nodes()` 方法（Story 3.3）
- [ ] 3.2 查询逻辑
  - [ ] 遍历 DAG 中的所有 Story 节点
  - [ ] 检查每个 Story 的所有 prerequisites 是否都在 completed_story_ids 中
  - [ ] 返回依赖已满足的 Story 列表

### Task 4: 更新 Story 模型验证方法 (AC: 2)
- [ ] 4.1 扩展 `aedt/domain/models/story.py`
  - [ ] 更新 `Story.validate(epic_stories: List[str])` 方法
  - [ ] 验证 prerequisites 中的每个 Story ID 存在于 epic_stories 中
  - [ ] 返回详细的错误消息
- [ ] 4.2 添加辅助方法
  - [ ] `Story.has_unmet_prerequisites(completed_ids: Set[str]) -> bool`
  - [ ] 检查是否有未满足的依赖

### Task 5: 异常处理扩展 (AC: 2)
- [ ] 5.1 扩展 `aedt/domain/exceptions.py`
  - [ ] 定义 `InvalidPrerequisiteError` 异常
  - [ ] ERROR_CODE = "DA003"
  - [ ] 包含 invalid_prereq_id 和 story_id 属性
- [ ] 5.2 在 `build_story_dag()` 中抛出异常
  - [ ] Prerequisites 不存在时抛出 `InvalidPrerequisiteError`
  - [ ] 循环依赖时抛出 `CircularDependencyError`

### Task 6: 集成到 Epic 执行流程 (AC: 1, 3)
- [ ] 6.1 确定调用时机
  - [ ] 当 Epic execution_mode = "multi" 时
  - [ ] 在 Epic 5 Scheduler 启动 Epic 时调用
- [ ] 6.2 设计集成接口
  ```python
  # 在 Scheduler 中的使用
  if epic.execution_mode == "multi":
      story_dag = analyzer.build_story_dag(epic.stories)
      parallel_stories = analyzer.get_parallel_stories(story_dag, [])
      # 为每个 parallel_story 启动独立 Subagent
  ```

### Task 7: 日志记录和调试 (AC: 1, 2, 3)
- [ ] 7.1 实现详细日志
  - [ ] INFO: Story DAG 构建开始/完成，Story 数量
  - [ ] WARNING: 前向依赖、空 prerequisites
  - [ ] ERROR: 循环依赖、无效 prerequisites
  - [ ] DEBUG: 每个 Story 的依赖关系
- [ ] 7.2 日志示例
  ```
  INFO  [DependencyAnalyzer] Building Story DAG for Epic 3: 8 Stories
  DEBUG [DependencyAnalyzer] Story 3.2 depends on: [3.1]
  DEBUG [DependencyAnalyzer] Story 3.3 depends on: [3.1, 3.2]
  INFO  [DependencyAnalyzer] Story DAG built successfully: 8 nodes, 10 edges
  INFO  [DependencyAnalyzer] Parallel Stories (0 completed): [3.1]
  ```

### Task 8: 单元测试 (AC: 1, 2, 3)
- [ ] 8.1 扩展 `tests/unit/domain/test_dependency_analyzer.py`
  - [ ] 测试 build_story_dag() 成功场景
  - [ ] 测试循环依赖检测（Story 级别）
  - [ ] 测试无效 prerequisites 检测
  - [ ] 测试 get_parallel_stories()
- [ ] 8.2 创建测试场景
  - [ ] 简单依赖链：3.1 → 3.2 → 3.3
  - [ ] 并行依赖：3.1 无依赖，3.2 和 3.3 都依赖 3.1
  - [ ] 复杂依赖：3.4 依赖 3.2 和 3.3，3.2 和 3.3 依赖 3.1
  - [ ] 循环依赖：3.2 ↔ 3.3
  - [ ] 无效 prerequisite：3.2 依赖 3.9（不存在）
- [ ] 8.3 Mock 和 Fixture
  - [ ] Mock Logger
  - [ ] 创建测试用的 Story 对象列表

### Task 9: 集成测试 (AC: 1, 2, 3)
- [ ] 9.1 创建 `tests/integration/test_story_dag.py`
  - [ ] 测试从 Epic 解析到 Story DAG 构建的完整流程
  - [ ] 使用 Epic 3 的实际 8 个 Stories
  - [ ] 验证 DAG 结构与预期一致
- [ ] 9.2 测试 multi-mode 调度准备
  - [ ] 模拟 Scheduler 调用 build_story_dag()
  - [ ] 验证可并行 Stories 列表正确
  - [ ] 测试渐进式完成场景（3.1 完成 → 3.2 可启动）

## Dev Notes

### 架构和设计模式

**模块位置和职责：**
- `aedt/domain/dependency_analyzer.py` - 扩展：添加 Story DAG 方法
- `aedt/domain/models/story.py` - 扩展：添加验证方法
- `aedt/domain/models/dag.py` - 复用：Story 3.3 的 DAG 类
- `aedt/domain/exceptions.py` - 扩展：添加 InvalidPrerequisiteError

**关键设计决策：**
1. **DAG 类复用**：Epic DAG 和 Story DAG 使用相同的 DAG 类，仅节点类型不同
2. **验证时机**：Prerequisites 验证在 DAG 构建时进行，早期发现错误
3. **前向依赖警告**：允许前向依赖，但记录 WARNING（灵活性 vs 最佳实践）
4. **与 Epic DAG 一致**：使用相同的循环检测和拓扑排序算法

**Multi 模式 vs Single 模式：**
- **Single Mode**：1 个 Subagent 处理所有 Stories（Epic ≤5 Stories）
- **Multi Mode**：每个 Story 独立 Subagent（Epic >5 Stories）
- **Story DAG 仅用于 Multi Mode**：决定 Story-level Subagent 的启动顺序

### 技术约束和 NFRs

**性能要求 (NFR6)：**
- Story DAG 构建应与 Epic DAG 相同的性能标准
- 支持 Epic 包含 50+ Stories 的场景

**可靠性 (NFR16)：**
- Story 循环依赖必须被检测并阻止
- Invalid prerequisites 必须明确报错

**模块独立性 (NFR17)：**
- Story DAG 构建逻辑独立可测试
- 与 Epic 5 Scheduler 的耦合最小化

### Learnings from Previous Stories

**From Story 3.1 & 3.2 (Status: drafted)**
- Story 模型的 prerequisites 字段在 Story 3.2 中提取
- 本 Story 负责使用这些 prerequisites 构建 DAG

**From Story 3.3 (Status: drafted)**
- **完全复用 DAG 类**：不需要创建新的数据结构
- **复用算法**：has_cycle(), topological_sort(), get_parallel_nodes()
- **复用异常**：CircularDependencyError 同样适用于 Story

**集成模式：**
```python
# Story 3.2 提供
epic = EpicParser.parse_single_epic("epic-003.md")
# epic.stories = [Story(id="3.1", prerequisites=[]),
#                 Story(id="3.2", prerequisites=["3.1"]), ...]

# Story 3.3 提供
dag_class = DAG  # 可复用

# Story 3.4 实现
story_dag = DependencyAnalyzer.build_story_dag(epic.stories)  # 使用 DAG 类
parallel = DependencyAnalyzer.get_parallel_stories(story_dag, completed=[])
```

[Source: docs/3-1-parse-bmad-epic-documents-and-extract-metadata.md]
[Source: docs/3-2-extract-story-list-from-epic-documents.md]
[Source: docs/3-3-build-epic-dependency-dag.md]

### Project Structure Notes

**修改的文件：**
```
aedt/
  domain/
    dependency_analyzer.py     # MODIFIED: 添加 build_story_dag(), get_parallel_stories()
    models/
      story.py                 # MODIFIED: 添加 validate() 和辅助方法
    exceptions.py              # MODIFIED: 添加 InvalidPrerequisiteError
tests/
  unit/
    domain/
      test_dependency_analyzer.py # MODIFIED: 添加 Story DAG 测试
  integration/
    test_story_dag.py          # NEW: Story DAG 集成测试
```

**依赖关系：**
- **使用 Story 3.2 输出**：Story 列表（包含 prerequisites）
- **复用 Story 3.3**：DAG 类和算法
- **为 Epic 5 & 6 准备**：提供 Story 级调度能力（multi-mode）

### Multi-Mode 执行流程示例

```python
# 在 Scheduler (Epic 5) 中的使用
class Scheduler:
    def start_epic(self, epic: Epic):
        if epic.execution_mode == "multi":
            # Story 3.4: 构建 Story DAG
            story_dag = self.dependency_analyzer.build_story_dag(epic.stories)

            # 初始：没有完成的 Stories
            completed_story_ids = []

            while not all_stories_completed:
                # 查询可并行的 Stories
                parallel_stories = self.dependency_analyzer.get_parallel_stories(
                    story_dag, completed_story_ids
                )

                # Epic 6: 为每个可并行 Story 启动 Subagent
                for story in parallel_stories:
                    self.launch_story_subagent(epic, story)

                # 等待任意 Story 完成
                completed_story = self.wait_for_story_completion()
                completed_story_ids.append(completed_story.id)

        elif epic.execution_mode == "single":
            # 启动单个 Epic-level Subagent 处理所有 Stories
            self.launch_epic_subagent(epic)
```

### References

**Tech Spec:**
- [Source: docs/tech-spec-epic-3.md#Story-领域模型]
- [Source: docs/tech-spec-epic-3.md#DependencyAnalyzer-API-Story-DAG-相关]
- [Source: docs/tech-spec-epic-3.md#Acceptance-Criteria-AC8-AC12]
- [Source: docs/tech-spec-epic-3.md#工作流-4-Story-level-DAG-构建]

**Epic Definition:**
- [Source: docs/epics.md#Story-3.4]

**Architecture:**
- [Source: docs/architecture.md#Execution-Modes-Single-vs-Multi]

**PRD:**
- [Source: docs/prd.md#FR25-自动调度-Epic-启动]
- [Source: docs/prd.md#FR12-依赖分析]

**Previous Stories:**
- [Source: docs/3-1-parse-bmad-epic-documents-and-extract-metadata.md]
- [Source: docs/3-2-extract-story-list-from-epic-documents.md]
- [Source: docs/3-3-build-epic-dependency-dag.md]

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent during implementation_

### Completion Notes List

_To be filled by dev agent after completion:_
- Story DAG 构建逻辑和性能
- Prerequisites 验证的边界情况
- 与 Epic DAG 的代码复用情况
- Multi-mode 调度准备接口

### File List

_To be filled by dev agent:_
- **NEW**: test_story_dag.py
- **MODIFIED**: dependency_analyzer.py, story.py, exceptions.py
- **DELETED**: (if any)
