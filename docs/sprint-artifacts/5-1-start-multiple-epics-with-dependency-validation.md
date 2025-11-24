# Story 5.1: 启动多个 Epic 并验证依赖关系

Status: drafted

## Story

作为用户,
我希望能够选择多个 Epic 并并行启动它们,
以便最大化开发速度。

## Acceptance Criteria

1. **并行启动无依赖的 Epic**
   - 给定 5 个 Epic (1, 2, 3 无依赖; 4 依赖 1, 2)
   - 当运行 `aedt start epic-1 epic-2 epic-3` 时
   - 系统验证所有 3 个 Epic 的依赖关系
   - 所有 3 个 Epic 并行启动(无依赖)
   - 为每个 Epic 创建 Worktree
   - 为每个 Epic 启动 Subagent

2. **阻止启动有未满足依赖的 Epic**
   - 给定 Epic 4 依赖 Epic 1 和 Epic 2
   - 当 Epic 1 尚未完成时运行 `aedt start epic-4`
   - 系统显示: "Cannot start Epic 4. Missing dependencies: Epic 1, Epic 2"
   - Epic 4 不被启动

3. **依赖验证准确性**
   - 系统正确解析所有 Epic 的 depends_on 字段
   - 验证依赖的 Epic 是否已完成(状态为 "completed")
   - 检测并报告所有缺失的依赖

## Tasks / Subtasks

- [ ] 实现 `Scheduler.start_epics(epic_ids)` 方法 (AC: #1, #2, #3)
  - [ ] 接收 Epic ID 列表作为参数
  - [ ] 返回 Dict[str, str] (Epic ID → 启动结果: "started"/"queued"/"failed")
  - [ ] 集成 DependencyAnalyzer 和 WorktreeManager

- [ ] 实现依赖验证逻辑 (AC: #2, #3)
  - [ ] 调用 `DependencyAnalyzer.get_parallel_epics()` 检查依赖是否满足
  - [ ] 如果依赖未满足: 添加到队列,返回 "queued"
  - [ ] 如果依赖已满足: 继续启动流程

- [ ] 实现 Epic 启动流程 (AC: #1)
  - [ ] 调用 `WorktreeManager.create_worktree(epic)` 创建隔离的 Git Worktree
  - [ ] 调用 `SubagentOrchestrator.start_agent(epic)` 启动 Subagent
  - [ ] 更新 Epic 状态为 "developing"
  - [ ] 返回 "started"

- [ ] 添加错误处理和用户反馈 (AC: #2)
  - [ ] 依赖验证失败时生成清晰的错误信息
  - [ ] 列出所有缺失的依赖 Epic
  - [ ] 记录错误到日志系统

- [ ] 编写单元测试 (AC: #1, #2, #3)
  - [ ] 测试无依赖 Epic 的并行启动
  - [ ] 测试有依赖 Epic 的阻止逻辑
  - [ ] 测试依赖验证的各种边界情况(循环依赖、不存在的依赖等)
  - [ ] 使用 mock 隔离 WorktreeManager 和 SubagentOrchestrator

## Dev Notes

### 架构约束

- **模块依赖**: Scheduler 模块依赖 DependencyAnalyzer、WorktreeManager 和 SubagentOrchestrator
- **异步处理**: 使用 asyncio 实现非阻塞的并行启动,避免阻塞 TUI 主线程
- **状态管理**: Epic 状态变化需要通过 StateManager 持久化到文件系统

### 实现要点

**1. Scheduler.start_epics() 核心逻辑**:
```python
async def start_epics(self, epic_ids: List[str]) -> Dict[str, str]:
    """
    启动多个 Epic,验证依赖关系

    Returns:
        Dict[Epic ID → "started"/"queued"/"failed" + 原因]
    """
    results = {}

    # 1. 构建 Epic DAG
    epics = [self.epic_parser.get_epic(id) for id in epic_ids]
    dag = self.dependency_analyzer.build_epic_dag(epics)

    # 2. 验证 DAG(检测循环依赖)
    if dag.has_cycle():
        raise DependencyError("Circular dependency detected")

    # 3. 为每个 Epic 验证依赖并启动
    for epic_id in epic_ids:
        # 检查依赖是否满足
        parallel_epics = self.dependency_analyzer.get_parallel_epics(
            dag,
            completed=self._get_completed_epic_ids()
        )

        if epic_id in [e.id for e in parallel_epics]:
            # 依赖满足,启动 Epic
            try:
                # 创建 Worktree
                worktree_path = await self.worktree_manager.create_worktree(epic)

                # 启动 Subagent
                agent_id = await self.orchestrator.start_agent(epic, worktree_path)

                # 更新状态
                epic.status = "developing"
                epic.agent_id = agent_id
                epic.worktree_path = worktree_path
                self.state_manager.update_epic_state(epic)

                results[epic_id] = "started"
            except Exception as e:
                results[epic_id] = f"failed: {str(e)}"
        else:
            # 依赖未满足,添加到队列
            missing_deps = self._get_missing_dependencies(epic_id, dag)
            self.queue.add(epic_id)
            results[epic_id] = f"queued (missing: {', '.join(missing_deps)})"

    return results
```

**2. 依赖验证辅助方法**:
```python
def _get_completed_epic_ids(self) -> List[str]:
    """获取已完成的 Epic ID 列表"""
    return [e.id for e in self.state_manager.get_all_epics()
            if e.status == "completed"]

def _get_missing_dependencies(self, epic_id: str, dag: DAG) -> List[str]:
    """获取缺失的依赖 Epic ID"""
    epic = dag.nodes[epic_id]
    completed = self._get_completed_epic_ids()
    return [dep for dep in epic.depends_on if dep not in completed]
```

**3. 错误处理策略**:
- **循环依赖**: 在 DAG 构建阶段检测,抛出 `DependencyError` 异常
- **不存在的依赖**: 在解析 Epic 元数据时验证,记录警告
- **Worktree 创建失败**: 捕获异常,返回 "failed" 状态,不影响其他 Epic
- **Subagent 启动失败**: 同上,清理已创建的 Worktree

### 项目结构对齐

**相关组件位置**:
- `src/scheduler/scheduler.py` - Scheduler 类实现
- `src/scheduler/queue.py` - ScheduleQueue 类实现
- `src/dependency/analyzer.py` - DependencyAnalyzer 类实现
- `src/worktree/manager.py` - WorktreeManager 类实现
- `src/subagent/orchestrator.py` - SubagentOrchestrator 类实现

**数据存储**:
- Epic 状态文件: `.aedt/projects/{project-id}/epics/{epic-id}.yaml`
- 队列状态文件: `.aedt/projects/{project-id}/queue.yaml`

### 测试策略

**单元测试覆盖**:
- `test_start_epics_parallel()` - 测试无依赖的并行启动
- `test_start_epics_with_dependencies()` - 测试依赖验证和队列
- `test_circular_dependency_detection()` - 测试循环依赖检测
- `test_missing_dependency_error()` - 测试缺失依赖的错误信息
- `test_worktree_creation_failure()` - 测试 Worktree 创建失败的处理
- `test_subagent_start_failure()` - 测试 Subagent 启动失败的处理

**集成测试**:
- 使用真实 Git 仓库测试 Worktree 创建
- 使用 mock 的 Claude Code Task 测试 Subagent 编排

### References

- [Source: docs/epics.md#Story-5.1 - Epic 5 Story 定义]
- [Source: docs/prd.md#智能并行调度引擎 - 功能需求]
- [Source: docs/architecture.md#3.3-调度引擎模块 - Scheduler 设计]
- [Source: docs/architecture.md#3.2-Epic-解析与依赖分析模块 - DependencyAnalyzer API]

**覆盖的功能需求**:
- FR16: Epic 启动与依赖验证
- FR17: 并行调度引擎

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2025-11-24: Story 初始创建 (SM Agent)
