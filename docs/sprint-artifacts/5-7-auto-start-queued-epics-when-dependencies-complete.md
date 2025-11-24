# Story 5.7: 依赖完成时自动启动队列中的 Epic

Status: drafted

## Story

作为用户,
我希望等待依赖的 Epic 能够自动启动,
以便我不需要手动跟踪依赖何时完成。

## Acceptance Criteria

1. **依赖部分完成时保持队列状态**
   - 给定 Epic 4 依赖 Epic 1 和 Epic 2
   - 给定 Epic 1 和 Epic 2 都在开发中
   - 给定 Epic 4 在队列中,状态为 "queued"
   - 当 Epic 1 完成并合并时
   - Epic 4 保持 "queued" 状态(Epic 2 仍在开发中)
   - 系统记录: "Epic 4 waiting for dependencies: Epic 2"

2. **所有依赖完成时自动启动**
   - 给定 Epic 4 依赖 Epic 1 和 Epic 2
   - 给定 Epic 1 已完成
   - 当 Epic 2 也完成并合并时
   - AEDT 自动启动 Epic 4(依赖已满足)
   - CLI 日志: "Epic 4 dependencies satisfied. Starting automatically."

3. **尊重并发限制**
   - 给定并发限制为 3
   - 给定当前有 3 个 Epic 正在运行
   - 当一个依赖 Epic 完成时
   - 如果队列中的 Epic 依赖已满足
   - 系统启动该 Epic(因为有空闲槽位)

4. **并发限制已满时等待**
   - 给定并发限制为 3
   - 给定当前有 3 个 Epic 正在运行
   - 当一个依赖 Epic 完成并合并时
   - 如果立即有另一个无依赖的 Epic 在队列前面
   - 系统先启动无依赖的 Epic(FIFO 顺序)
   - 有依赖的 Epic 继续等待槽位

## Tasks / Subtasks

- [ ] 实现 `Scheduler.auto_start_queued(completed_epic_id)` 方法 (AC: #1, #2, #3, #4)
  - [ ] 接收刚完成的 Epic ID 作为参数
  - [ ] 从并发队列移除已完成的 Epic
  - [ ] 遍历队列中的所有 Epic
  - [ ] 检查每个 Epic 的依赖是否满足
  - [ ] 检查是否有空闲的并发槽位
  - [ ] 启动满足条件的 Epic

- [ ] 实现依赖验证逻辑 (AC: #1, #2)
  - [ ] 为队列中的每个 Epic 调用 `DependencyAnalyzer.get_parallel_epics()`
  - [ ] 传递已完成的 Epic ID 列表
  - [ ] 如果 Epic 在可并行列表中 → 依赖已满足
  - [ ] 如果不在 → 依赖未满足,记录缺失的依赖

- [ ] 实现并发槽位检查 (AC: #3, #4)
  - [ ] 调用 `queue.can_start()` 检查是否低于并发限制
  - [ ] 如果 `can_start() == False`,跳过启动
  - [ ] 如果 `can_start() == True`,继续启动流程

- [ ] 实现队列优先级处理 (AC: #4)
  - [ ] 按队列顺序(FIFO)遍历 Epic
  - [ ] 优先启动先进入队列的 Epic
  - [ ] 尊重 Epic 优先级(如果设置了 HIGH 优先级)
  - [ ] 每次只启动一个 Epic,然后重新检查槽位

- [ ] 实现自动启动日志记录 (AC: #2)
  - [ ] 记录依赖检查结果
  - [ ] 记录缺失的依赖(如果有)
  - [ ] 记录自动启动事件
  - [ ] 生成用户友好的日志消息

- [ ] 集成到 Epic 完成流程 (AC: #2)
  - [ ] 在 `Scheduler.on_epic_completed()` 中调用 `auto_start_queued()`
  - [ ] 在 Epic 合并成功后触发
  - [ ] 确保在 Worktree 清理之前调用

- [ ] 编写单元测试 (AC: #1, #2, #3, #4)
  - [ ] `test_partial_dependency_keeps_queued()` - 测试部分依赖完成时保持队列状态
  - [ ] `test_all_dependencies_auto_start()` - 测试所有依赖完成时自动启动
  - [ ] `test_respect_concurrency_limit()` - 测试尊重并发限制
  - [ ] `test_fifo_queue_order()` - 测试 FIFO 队列顺序
  - [ ] `test_priority_override()` - 测试高优先级 Epic 插队
  - [ ] 使用 mock DependencyAnalyzer 和 ScheduleQueue

## Dev Notes

### 架构约束

- **依赖分析**: 复用 Story 5.1 的 `DependencyAnalyzer.get_parallel_epics()` 方法
- **并发控制**: 复用 Story 5.2 的 `ScheduleQueue` 并发管理
- **触发点**: 在 Story 5.6 的 Epic 完成流程中调用
- **原子性**: 启动操作需要原子化,避免并发竞争

### 实现要点

**1. Scheduler.auto_start_queued() 实现**:
```python
async def auto_start_queued(self, completed_epic_id: Optional[str] = None):
    """
    自动启动队列中的 Epic

    触发时机:
    1. Epic 完成并合并后
    2. 手动调用(例如用户手动启动队列)

    逻辑:
    1. 从并发队列移除已完成的 Epic
    2. 获取所有队列中的 Epic
    3. 检查每个 Epic 的依赖是否满足
    4. 检查并发槽位是否可用
    5. 启动满足条件的 Epic(按队列顺序)

    Args:
        completed_epic_id: 刚完成的 Epic ID(用于日志)
    """
    # 1. 从队列移除已完成的 Epic
    if completed_epic_id:
        await self.queue.mark_completed(completed_epic_id)

        self.logger.info(
            f"Epic {completed_epic_id} completed. "
            f"Checking queue for next Epic to start..."
        )

    # 2. 获取队列中的 Epic
    queued_epics = await self._get_queued_epics()

    if not queued_epics:
        self.logger.debug("Queue is empty. No Epics to start.")
        return

    # 3. 获取已完成的 Epic 列表(用于依赖验证)
    completed_epic_ids = await self._get_completed_epic_ids()

    self.logger.debug(
        f"Completed Epics: {completed_epic_ids}, "
        f"Queued Epics: {[e.id for e in queued_epics]}"
    )

    # 4. 遍历队列,尝试启动满足条件的 Epic
    for epic in queued_epics:
        # 检查并发槽位
        if not self.queue.can_start():
            self.logger.info(
                f"Concurrency limit reached. "
                f"Epic {epic.id} remains queued."
            )
            break  # 槽位已满,停止尝试

        # 检查依赖是否满足
        dependencies_met = await self._check_dependencies_met(
            epic, completed_epic_ids
        )

        if not dependencies_met:
            missing_deps = self._get_missing_dependencies(
                epic, completed_epic_ids
            )
            self.logger.info(
                f"Epic {epic.id} waiting for dependencies: "
                f"{', '.join(missing_deps)}"
            )
            continue  # 依赖未满足,检查下一个

        # 依赖满足且有槽位 → 启动 Epic
        try:
            await self._start_epic(epic.id)
            await self.queue.mark_running(epic.id)

            self.logger.info(
                f"Epic {epic.id} dependencies satisfied. "
                f"Starting automatically."
            )

            # 触发事件
            await self.event_bus.emit("epic_auto_started", {
                "epic_id": epic.id,
                "triggered_by": completed_epic_id
            })

            # 从队列移除
            await self.queue.remove_from_queue(epic.id)

            # 只启动一个,然后重新检查槽位
            # (避免一次启动过多)

        except Exception as e:
            self.logger.error(
                f"Failed to auto-start Epic {epic.id}: {e}",
                exc_info=True
            )

async def _get_queued_epics(self) -> List[Epic]:
    """
    获取队列中的所有 Epic

    Returns:
        按队列顺序排列的 Epic 列表(FIFO)
    """
    queued_epic_ids = self.queue.get_queued_epic_ids()

    epics = []
    for epic_id in queued_epic_ids:
        epic = self.epic_parser.get_epic(epic_id)
        epics.append(epic)

    return epics

async def _get_completed_epic_ids(self) -> List[str]:
    """
    获取所有已完成的 Epic ID

    Returns:
        已完成的 Epic ID 列表
    """
    all_epics = await self.state_manager.get_all_epics()

    completed = [
        epic.id for epic in all_epics
        if epic.status == "completed"
    ]

    return completed

async def _check_dependencies_met(
    self,
    epic: Epic,
    completed_epic_ids: List[str]
) -> bool:
    """
    检查 Epic 的依赖是否全部满足

    Args:
        epic: Epic 对象
        completed_epic_ids: 已完成的 Epic ID 列表

    Returns:
        True 如果依赖全部满足,False 否则
    """
    if not epic.depends_on:
        # 无依赖
        return True

    # 检查所有依赖是否在已完成列表中
    return all(
        dep_id in completed_epic_ids
        for dep_id in epic.depends_on
    )

def _get_missing_dependencies(
    self,
    epic: Epic,
    completed_epic_ids: List[str]
) -> List[str]:
    """
    获取缺失的依赖 Epic ID

    Returns:
        未完成的依赖 Epic ID 列表
    """
    if not epic.depends_on:
        return []

    return [
        dep_id for dep_id in epic.depends_on
        if dep_id not in completed_epic_ids
    ]
```

**2. ScheduleQueue 扩展(支持队列查询)**:
```python
class ScheduleQueue:
    """管理 Epic 启动队列和并发限制"""

    def get_queued_epic_ids(self) -> List[str]:
        """
        获取队列中的所有 Epic ID(按 FIFO 顺序)

        Returns:
            Epic ID 列表,按进入队列的顺序
        """
        return [epic_id for epic_id, _ in self.queued]

    async def remove_from_queue(self, epic_id: str):
        """
        从队列移除指定的 Epic

        Args:
            epic_id: Epic ID
        """
        async with self._lock:
            # 从 deque 中移除
            self.queued = deque([
                (eid, priority)
                for eid, priority in self.queued
                if eid != epic_id
            ])

            await self._save_queue_state()

            self.logger.debug(f"Removed Epic {epic_id} from queue")
```

**3. 集成到 Epic 完成流程**:
```python
# 在 Scheduler.on_epic_completed() 中调用

async def _merge_epic(self, epic: Epic):
    """合并 Epic 到主分支"""
    # ... 合并逻辑 ...

    if merge_result.success:
        # 合并成功
        epic.status = "completed"
        await self.state_manager.update_epic_state(epic)

        # 清理 Worktree
        if self.config.get("git.auto_cleanup", True):
            await self.worktree_manager.cleanup_worktree(epic)

        # *** 启动队列中的下一个 Epic ***
        await self.auto_start_queued(completed_epic_id=epic.id)

        # 触发完成事件
        await self.event_bus.emit("epic_completed", {
            "epic_id": epic.id,
            "merge_commit": merge_result.commit_hash
        })
```

**4. 依赖检查示例场景**:

**场景 1: 部分依赖完成**
```python
# Epic 4 依赖 Epic 1 和 Epic 2
epic_4 = Epic(id="4", depends_on=["1", "2"])

# 已完成: Epic 1
completed_epic_ids = ["1"]

# 检查依赖
dependencies_met = all(
    dep in completed_epic_ids
    for dep in epic_4.depends_on
)
# Result: False (Epic 2 尚未完成)

missing_deps = [
    dep for dep in epic_4.depends_on
    if dep not in completed_epic_ids
]
# Result: ["2"]

# 日志: "Epic 4 waiting for dependencies: 2"
```

**场景 2: 所有依赖完成**
```python
# Epic 4 依赖 Epic 1 和 Epic 2
epic_4 = Epic(id="4", depends_on=["1", "2"])

# 已完成: Epic 1 和 Epic 2
completed_epic_ids = ["1", "2"]

# 检查依赖
dependencies_met = all(
    dep in completed_epic_ids
    for dep in epic_4.depends_on
)
# Result: True

# Epic 4 将被启动(如果有槽位)
# 日志: "Epic 4 dependencies satisfied. Starting automatically."
```

**5. 队列优先级处理**:

```python
# 队列状态
queued_epics = [
    Epic(id="3", depends_on=[], priority="NORMAL"),    # 无依赖,普通优先级
    Epic(id="4", depends_on=["1", "2"], priority="HIGH"),  # 有依赖,高优先级
    Epic(id="5", depends_on=[], priority="NORMAL"),    # 无依赖,普通优先级
]

# 遍历队列(FIFO 顺序)
for epic in queued_epics:
    if queue.can_start() and dependencies_met(epic):
        start_epic(epic)
        break  # 只启动一个

# 结果:
# 1. Epic 3 先被检查,无依赖且有槽位 → 启动
# 2. Epic 4 虽然优先级高,但依赖未满足 → 跳过
# 3. Epic 5 被跳过(Epic 3 已启动,槽位占用)

# 如果 Epic 1 和 2 完成后:
# Epic 4 的依赖满足 → 下次会被启动
```

**6. 并发限制场景**:

```python
# 配置: max_concurrent = 3
# 当前运行: Epic A, Epic B, Epic C (3 个)
# 队列: Epic 4 (依赖 Epic A), Epic 5 (无依赖)

# Epic A 完成 → 触发 auto_start_queued("A")
# 槽位: 2/3 (Epic B, Epic C)
# 检查 Epic 4: 依赖满足(Epic A 已完成)
# 检查 Epic 5: 无依赖

# FIFO 顺序: Epic 4 先进入队列
# → 启动 Epic 4

# Epic B 完成 → 触发 auto_start_queued("B")
# 槽位: 2/3 (Epic C, Epic 4)
# → 启动 Epic 5
```

### 从前一个 Story 的经验教训

**从 Story 5-6 (Epic 完成处理)**:

Story 5-6 展示了 Epic 完成后的流程编排:

- **自动触发**: Epic 完成后自动触发质量检查和合并
- **状态流转**: 清晰的状态变化(quality_checking → merging → completed)
- **集成点**: 在合并成功后调用 `auto_start_queued()`

**在本 Story 中的应用**:

1. **集成点明确**: 在 `_merge_epic()` 的合并成功分支调用
2. **日志记录**: 详细记录依赖检查和启动事件
3. **错误处理**: 启动失败不影响其他队列中的 Epic

**从 Story 5-2 (并发控制)**:

- **队列管理**: 复用 `ScheduleQueue` 的并发限制逻辑
- **原子操作**: 使用 `asyncio.Lock` 保护队列状态

**在本 Story 中的应用**:

1. **槽位检查**: 调用 `queue.can_start()` 确保不超出限制
2. **队列操作**: 使用 `remove_from_queue()` 移除已启动的 Epic

### 项目结构对齐

**修改组件**:
- `src/scheduler/scheduler.py` - 添加 `auto_start_queued()` 方法
- `src/scheduler/queue.py` - 扩展 `ScheduleQueue` 添加队列查询方法

**无需新增组件** - 复用现有的 DependencyAnalyzer 和 ScheduleQueue

### 测试策略

**单元测试**:
```python
# tests/scheduler/test_auto_start_queued.py

async def test_partial_dependency_keeps_queued():
    """测试部分依赖完成时保持队列状态"""
    epic_4 = Epic(id="4", depends_on=["1", "2"])

    scheduler = Scheduler(...)
    scheduler.queue.queued = deque([("4", Priority.NORMAL)])

    # 模拟 Epic 1 完成(Epic 2 仍在开发中)
    scheduler.state_manager.get_all_epics = AsyncMock(return_value=[
        Epic(id="1", status="completed"),
        Epic(id="2", status="developing"),
        Epic(id="4", status="queued")
    ])

    await scheduler.auto_start_queued(completed_epic_id="1")

    # Epic 4 应该仍在队列中
    assert "4" in scheduler.queue.get_queued_epic_ids()
    # Epic 4 未被启动
    assert "4" not in scheduler.queue.running

async def test_all_dependencies_auto_start():
    """测试所有依赖完成时自动启动"""
    epic_4 = Epic(id="4", depends_on=["1", "2"])

    scheduler = Scheduler(...)
    scheduler.queue.queued = deque([("4", Priority.NORMAL)])
    scheduler.queue.running = []

    # 模拟 Epic 1 和 2 都已完成
    scheduler.state_manager.get_all_epics = AsyncMock(return_value=[
        Epic(id="1", status="completed"),
        Epic(id="2", status="completed"),
        Epic(id="4", status="queued")
    ])

    # Mock _start_epic
    scheduler._start_epic = AsyncMock()

    await scheduler.auto_start_queued(completed_epic_id="2")

    # Epic 4 应该被启动
    scheduler._start_epic.assert_called_once_with("4")
    assert "4" in scheduler.queue.running

async def test_respect_concurrency_limit():
    """测试尊重并发限制"""
    scheduler = Scheduler(...)
    scheduler.queue.max_concurrent = 3
    scheduler.queue.running = ["1", "2", "3"]  # 已满
    scheduler.queue.queued = deque([("4", Priority.NORMAL)])

    await scheduler.auto_start_queued()

    # Epic 4 不应该被启动(槽位已满)
    assert "4" in scheduler.queue.get_queued_epic_ids()
    assert "4" not in scheduler.queue.running

async def test_fifo_queue_order():
    """测试 FIFO 队列顺序"""
    scheduler = Scheduler(...)
    scheduler.queue.max_concurrent = 3
    scheduler.queue.running = []
    scheduler.queue.queued = deque([
        ("3", Priority.NORMAL),
        ("4", Priority.NORMAL),
        ("5", Priority.NORMAL),
    ])

    # 所有 Epic 无依赖,都可以启动
    scheduler.state_manager.get_all_epics = AsyncMock(return_value=[])
    scheduler._start_epic = AsyncMock()

    await scheduler.auto_start_queued()

    # 应该按顺序启动(最多 3 个)
    assert scheduler._start_epic.call_count == 3
    # 调用顺序应该是 3, 4, 5
    calls = [call[0][0] for call in scheduler._start_epic.call_args_list]
    assert calls == ["3", "4", "5"]
```

**集成测试**:
```python
async def test_dependency_chain_auto_start():
    """测试依赖链自动启动"""
    # Epic 2 依赖 Epic 1
    # Epic 3 依赖 Epic 2
    epics = [
        Epic(id="1", depends_on=[]),
        Epic(id="2", depends_on=["1"]),
        Epic(id="3", depends_on=["2"]),
    ]

    scheduler = Scheduler(...)

    # 启动 Epic 1
    await scheduler.start_epics(["1"])

    # 模拟 Epic 1 完成
    await scheduler.on_epic_completed("1")

    # Epic 2 应该自动启动
    assert "2" in scheduler.queue.running

    # 模拟 Epic 2 完成
    await scheduler.on_epic_completed("2")

    # Epic 3 应该自动启动
    assert "3" in scheduler.queue.running
```

### References

- [Source: docs/epics.md#Story-5.7 - Epic 5 Story 定义]
- [Source: docs/prd.md#并行调度引擎 - FR25, FR9]
- [Source: docs/sprint-artifacts/5-2-control-maximum-concurrent-subagents.md - 并发控制]
- [Source: docs/sprint-artifacts/5-6-handle-epic-completion-and-trigger-quality-checks.md - Epic 完成流程]

**覆盖的功能需求**:
- FR25: 系统可以在 Epic 依赖完成后自动启动等待中的 Epic
- FR9: 系统可以自动排队有依赖的 Epic

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
