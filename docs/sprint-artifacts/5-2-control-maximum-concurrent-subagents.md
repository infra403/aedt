# Story 5.2: 控制最大并发 Subagent 数量

Status: drafted

## Story

作为用户,
我希望 AEDT 限制并发 Subagent 的数量,
以便不会压垮系统资源或超出 API 速率限制。

## Acceptance Criteria

1. **强制并发限制**
   - 给定配置文件中 max_concurrent 设置为 3
   - 当我尝试启动 5 个 Epic 时
   - 系统验证所有 5 个 Epic 都有效(无依赖问题)
   - 只有 3 个 Epic 立即启动
   - 剩余 2 个 Epic 被添加到队列
   - CLI 显示: "Started 3 Epics. 2 Epics queued (concurrency limit)."

2. **自动启动队列中的 Epic**
   - 给定 3 个 Epic 正在运行
   - 当其中一个 Epic 完成时
   - 系统检测到完成事件
   - 下一个排队的 Epic 自动启动
   - CLI 显示: "Epic X completed. Starting Epic Y from queue."

3. **队列优先级处理**
   - 给定队列中有多个 Epic 等待
   - 当有空位时
   - 系统按照队列顺序启动下一个 Epic(FIFO)
   - 优先级高的 Epic 可以插队到队列前端

## Tasks / Subtasks

- [ ] 实现 `ScheduleQueue` 类,支持并发限制 (AC: #1, #2, #3)
  - [ ] 初始化时从配置读取 `max_concurrent` 参数
  - [ ] 维护 `running: List[str]` 列表(当前运行的 Epic ID)
  - [ ] 维护 `queued: Deque[str]` 队列(等待的 Epic ID)
  - [ ] 实现 `can_start() -> bool` 方法,检查是否低于并发限制
  - [ ] 实现 `add_to_queue(epic_id, priority=NORMAL)` 方法,支持优先级插队

- [ ] 修改 `Scheduler.start_epics()` 方法,集成并发控制 (AC: #1)
  - [ ] 在启动 Epic 前调用 `queue.can_start()` 检查
  - [ ] 如果 `can_start() == True`: 启动 Epic,添加到 `running` 列表
  - [ ] 如果 `can_start() == False`: 添加到 `queued`,返回 "queued (concurrency limit)"
  - [ ] 返回启动摘要,包含已启动和排队的 Epic 数量

- [ ] 实现 `Scheduler.auto_start_queued()` 方法 (AC: #2)
  - [ ] 在 Epic 完成时自动调用
  - [ ] 从 `running` 列表移除已完成的 Epic
  - [ ] 循环检查 `queue.can_start()` 和 `queue.pop_next()`
  - [ ] 对弹出的 Epic 执行启动流程(创建 Worktree + 启动 Subagent)
  - [ ] 记录并显示自动启动信息

- [ ] 实现优先级队列支持 (AC: #3)
  - [ ] 使用 `collections.deque` + 优先级字段实现
  - [ ] 高优先级 Epic 插入到队列前端,低优先级插入到队列尾部
  - [ ] 默认优先级为 NORMAL

- [ ] 添加配置参数验证 (AC: #1)
  - [ ] 验证 `max_concurrent` 是正整数且 >= 1
  - [ ] 如果配置缺失,使用默认值 5
  - [ ] 记录配置加载信息到日志

- [ ] 编写单元测试 (AC: #1, #2, #3)
  - [ ] `test_concurrent_limit_enforcement()` - 测试并发限制强制执行
  - [ ] `test_auto_start_queued_epic()` - 测试自动启动队列中的 Epic
  - [ ] `test_priority_queue_order()` - 测试优先级队列顺序
  - [ ] `test_max_concurrent_from_config()` - 测试从配置读取并发限制
  - [ ] `test_queue_empty_edge_case()` - 测试队列为空时的边界情况
  - [ ] 使用 mock 隔离 WorktreeManager 和 SubagentOrchestrator

## Dev Notes

### 架构约束

- **并发限制来源**: 从 `.aedt/config.yaml` 的 `subagent.max_concurrent` 字段读取
- **状态持久化**: 队列状态需要持久化到 `.aedt/projects/{project-id}/queue.yaml`,支持崩溃恢复
- **线程安全**: ScheduleQueue 需要线程安全,使用 `asyncio.Lock` 保护共享状态

### 实现要点

**1. ScheduleQueue 类设计**:
```python
from collections import deque
from enum import Enum
from typing import List, Optional
import asyncio

class Priority(Enum):
    HIGH = 1
    NORMAL = 2
    LOW = 3

class ScheduleQueue:
    """管理 Epic 启动队列和并发限制"""

    def __init__(self, max_concurrent: int, state_manager: StateManager):
        self.max_concurrent = max_concurrent
        self.state_manager = state_manager
        self.running: List[str] = []  # 当前运行的 Epic ID
        self.queued: deque = deque()  # 等待队列 (Epic ID, Priority)
        self._lock = asyncio.Lock()  # 保护并发访问

    def can_start(self) -> bool:
        """检查是否可以启动新的 Epic"""
        return len(self.running) < self.max_concurrent

    async def add_to_queue(self, epic_id: str, priority: Priority = Priority.NORMAL):
        """添加 Epic 到队列,支持优先级"""
        async with self._lock:
            # 高优先级插队到前面
            if priority == Priority.HIGH:
                self.queued.appendleft((epic_id, priority))
            else:
                self.queued.append((epic_id, priority))

            # 持久化队列状态
            await self._save_queue_state()

    async def mark_running(self, epic_id: str):
        """标记 Epic 开始运行"""
        async with self._lock:
            self.running.append(epic_id)
            await self._save_queue_state()

    async def mark_completed(self, epic_id: str):
        """标记 Epic 完成,从 running 列表移除"""
        async with self._lock:
            if epic_id in self.running:
                self.running.remove(epic_id)
            await self._save_queue_state()

    def pop_next(self) -> Optional[str]:
        """弹出队列中的下一个 Epic"""
        if self.queued:
            epic_id, _ = self.queued.popleft()
            return epic_id
        return None

    async def _save_queue_state(self):
        """持久化队列状态到文件"""
        state = {
            "running": self.running,
            "queued": [(epic_id, priority.name) for epic_id, priority in self.queued]
        }
        await self.state_manager.save_queue_state(state)
```

**2. 修改 Scheduler.start_epics() 集成并发控制**:
```python
async def start_epics(self, epic_ids: List[str]) -> Dict[str, str]:
    """
    启动多个 Epic,强制并发限制

    Returns:
        Dict[Epic ID → "started"/"queued"/"failed" + 原因]
    """
    results = {}
    started_count = 0
    queued_count = 0

    # 构建 DAG 并验证依赖(继承自 Story 5.1)
    epics = [self.epic_parser.get_epic(id) for id in epic_ids]
    dag = self.dependency_analyzer.build_epic_dag(epics)

    if dag.has_cycle():
        raise DependencyError("Circular dependency detected")

    for epic_id in epic_ids:
        # 检查依赖是否满足
        parallel_epics = self.dependency_analyzer.get_parallel_epics(
            dag,
            completed=self._get_completed_epic_ids()
        )

        if epic_id not in [e.id for e in parallel_epics]:
            # 依赖未满足,添加到队列
            missing_deps = self._get_missing_dependencies(epic_id, dag)
            await self.queue.add_to_queue(epic_id)
            results[epic_id] = f"queued (missing: {', '.join(missing_deps)})"
            queued_count += 1
            continue

        # 依赖满足,检查并发限制
        if not self.queue.can_start():
            # 超出并发限制,添加到队列
            await self.queue.add_to_queue(epic_id)
            results[epic_id] = "queued (concurrency limit)"
            queued_count += 1
            continue

        # 启动 Epic
        try:
            await self._start_epic(epic_id)
            await self.queue.mark_running(epic_id)
            results[epic_id] = "started"
            started_count += 1
        except Exception as e:
            results[epic_id] = f"failed: {str(e)}"

    # 生成启动摘要
    summary = f"Started {started_count} Epics."
    if queued_count > 0:
        summary += f" {queued_count} Epics queued."

    return results, summary

async def _start_epic(self, epic_id: str):
    """启动单个 Epic (提取的辅助方法)"""
    epic = self.epic_parser.get_epic(epic_id)

    # 创建 Worktree
    worktree_path = await self.worktree_manager.create_worktree(epic)

    # 启动 Subagent
    agent_id = await self.orchestrator.start_agent(epic, worktree_path)

    # 更新状态
    epic.status = "developing"
    epic.agent_id = agent_id
    epic.worktree_path = worktree_path
    await self.state_manager.update_epic_state(epic)
```

**3. Scheduler.auto_start_queued() 实现**:
```python
async def auto_start_queued(self, completed_epic_id: str):
    """
    Epic 完成后自动启动队列中的下一个 Epic

    Args:
        completed_epic_id: 刚完成的 Epic ID
    """
    # 标记 Epic 完成,从 running 列表移除
    await self.queue.mark_completed(completed_epic_id)

    # 循环启动队列中的 Epic,直到达到并发限制
    while self.queue.can_start():
        next_epic_id = self.queue.pop_next()

        if next_epic_id is None:
            # 队列为空
            break

        # 再次验证依赖(可能在等待期间依赖状态变化)
        epic = self.epic_parser.get_epic(next_epic_id)
        dag = self.dependency_analyzer.build_epic_dag([epic])
        parallel_epics = self.dependency_analyzer.get_parallel_epics(
            dag,
            completed=self._get_completed_epic_ids()
        )

        if next_epic_id not in [e.id for e in parallel_epics]:
            # 依赖仍未满足,重新加入队列
            await self.queue.add_to_queue(next_epic_id)
            continue

        # 启动 Epic
        try:
            await self._start_epic(next_epic_id)
            await self.queue.mark_running(next_epic_id)

            # 记录自动启动事件
            self.logger.info(
                f"Epic {completed_epic_id} completed. "
                f"Starting Epic {next_epic_id} from queue."
            )

            # 显示给用户(通过 TUI 事件)
            await self.event_bus.emit(
                "epic_auto_started",
                {"completed": completed_epic_id, "started": next_epic_id}
            )

        except Exception as e:
            self.logger.error(f"Failed to auto-start Epic {next_epic_id}: {e}")
            # 失败后不重新加入队列,避免无限循环
```

**4. 配置文件示例**:
```yaml
# .aedt/config.yaml
subagent:
  max_concurrent: 5  # 默认最多 5 个并发
  timeout: 3600
  model: "claude-sonnet-4"
```

**5. 队列状态文件示例**:
```yaml
# .aedt/projects/{project-id}/queue.yaml
running:
  - "epic-1"
  - "epic-2"
  - "epic-3"

queued:
  - epic_id: "epic-4"
    priority: "NORMAL"
  - epic_id: "epic-5"
    priority: "HIGH"
```

### 从前一个 Story 的经验教训

**从 Story 5-1 (启动多个 Epic 并验证依赖关系)**:

Story 5-1 尚未实现(状态为 "drafted"),因此没有实际的完成记录可供参考。但从该 Story 的设计中可以提取以下关键点:

- **Scheduler 架构已定义**: Story 5-1 定义了 `Scheduler.start_epics()` 方法的基本结构
- **依赖验证流程**: 使用 `DependencyAnalyzer.get_parallel_epics()` 检查依赖
- **启动流程分解**: Epic 启动包含 Worktree 创建 + Subagent 启动 + 状态更新
- **错误处理模式**: 每个 Epic 独立处理,一个失败不影响其他

**在本 Story 中的应用**:

1. **复用启动逻辑**: 提取 `_start_epic()` 辅助方法,避免在 `start_epics()` 和 `auto_start_queued()` 中重复代码
2. **保持一致性**: 队列中的 Epic 启动时也要进行依赖验证(可能在等待期间状态变化)
3. **扩展返回值**: 在 Story 5-1 的返回值基础上添加启动摘要字符串

### 项目结构对齐

**新增组件**:
- `src/scheduler/queue.py` - ScheduleQueue 类实现

**修改组件**:
- `src/scheduler/scheduler.py` - 添加并发控制逻辑

**数据存储**:
- 队列状态文件: `.aedt/projects/{project-id}/queue.yaml`

**配置文件**:
- `.aedt/config.yaml` - 添加 `subagent.max_concurrent` 参数

### 测试策略

**单元测试**:
```python
# tests/scheduler/test_queue.py

async def test_concurrent_limit_enforcement():
    """测试并发限制强制执行"""
    queue = ScheduleQueue(max_concurrent=3, state_manager=mock_state_manager)

    # 模拟启动 3 个 Epic
    await queue.mark_running("epic-1")
    await queue.mark_running("epic-2")
    await queue.mark_running("epic-3")

    # 第 4 个 Epic 不能立即启动
    assert queue.can_start() == False

    # 完成一个 Epic 后,可以启动下一个
    await queue.mark_completed("epic-1")
    assert queue.can_start() == True

async def test_auto_start_queued_epic():
    """测试自动启动队列中的 Epic"""
    scheduler = Scheduler(config, queue, ...)

    # 启动 3 个 Epic,第 4 和第 5 个排队
    await scheduler.start_epics(["epic-1", "epic-2", "epic-3", "epic-4", "epic-5"])

    assert len(queue.running) == 3
    assert len(queue.queued) == 2

    # 模拟 epic-1 完成
    await scheduler.auto_start_queued("epic-1")

    # epic-4 应该自动启动
    assert "epic-4" in queue.running
    assert len(queue.queued) == 1

async def test_priority_queue_order():
    """测试优先级队列顺序"""
    queue = ScheduleQueue(max_concurrent=1, state_manager=mock_state_manager)

    await queue.add_to_queue("epic-1", Priority.NORMAL)
    await queue.add_to_queue("epic-2", Priority.HIGH)
    await queue.add_to_queue("epic-3", Priority.NORMAL)

    # 高优先级应该先弹出
    assert queue.pop_next() == "epic-2"
    assert queue.pop_next() == "epic-1"
    assert queue.pop_next() == "epic-3"
```

**集成测试**:
- 测试完整的启动 → 完成 → 自动启动流程
- 使用真实配置文件测试并发限制读取
- 测试队列状态持久化和恢复

### References

- [Source: docs/epics.md#Story-5.2 - Epic 5 Story 定义]
- [Source: docs/prd.md#并行调度与 Subagent 编排 - FR20, FR21]
- [Source: docs/architecture.md#3.3-调度引擎模块 - Scheduler 架构]
- [Source: docs/sprint-artifacts/5-1-start-multiple-epics-with-dependency-validation.md - 前一个 Story 的设计]

**覆盖的功能需求**:
- FR20: 系统可以控制最大并发 Subagent 数量
- FR21: 系统可以将超出并发限制的 Epic 自动排队

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
