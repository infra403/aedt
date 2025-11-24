# Story 5.5: 在 Multi 模式下启动 Epic (Story 级别 Subagents)

Status: drafted

## Story

作为用户,
我希望大型 Epic 的 Story 能够并行完成,
以便开发速度更快且上下文更聚焦。

## Acceptance Criteria

1. **并行启动多个 Story 级别 Subagent**
   - 给定 Epic 3 有 8 个 Story,处于 "multi" 模式
   - 给定 story_concurrency 设置为 3
   - 当 AEDT 启动 Epic 3 时
   - 系统识别前 3 个无依赖的 Story
   - 为每个 Story 启动独立的 Subagent
   - 剩余 5 个 Story 进入队列等待

2. **自动启动队列中的 Story**
   - 给定 Story 1 完成
   - 当系统检测到完成事件时
   - 从队列中取出 Story 4(下一个可并行的 Story)
   - 自动为 Story 4 启动新的 Subagent

3. **尊重 Story 依赖关系**
   - 给定 Story 5 依赖 Story 2 和 Story 3
   - 当 Story 2 和 Story 3 都完成后
   - Story 5 才能从队列启动
   - 即使有空闲的并发槽位,也要等待依赖满足

4. **Epic 级别进度聚合**
   - 给定 Epic 有 8 个 Story,已完成 5 个
   - 当系统更新进度时
   - Epic 进度显示为 62.5% (5/8)
   - TUI 显示: "Epic 3: Developing 62.5% (5/8 stories, 3 running)"

## Tasks / Subtasks

- [ ] 实现 `Scheduler.start_epic_multi_mode(epic, worktree_path)` 方法 (AC: #1, #2, #3, #4)
  - [ ] 接收 Epic 对象和 Worktree 路径
  - [ ] 构建 Story DAG(依赖关系图)
  - [ ] 初始化 Story 并发队列
  - [ ] 启动初始的可并行 Story(最多 story_concurrency 个)
  - [ ] 返回 Epic 的聚合 agent_id (如 "multi-epic-3")

- [ ] 实现 Story DAG 构建逻辑 (AC: #3)
  - [ ] 调用 `DependencyAnalyzer.build_story_dag(epic.stories)`
  - [ ] 验证 DAG 无循环依赖
  - [ ] 如果存在循环依赖,抛出 `DependencyError` 异常
  - [ ] 记录 DAG 结构到日志(用于调试)

- [ ] 实现 Story 并发控制逻辑 (AC: #1, #2)
  - [ ] 维护 `running_stories: List[(story_id, agent_id)]` 跟踪运行中的 Story
  - [ ] 维护 `completed_stories: List[story_id]` 跟踪已完成的 Story
  - [ ] 从 Epic 元数据读取 `story_concurrency` 参数(默认 3)
  - [ ] 启动 Story 前检查: `len(running_stories) < story_concurrency`

- [ ] 实现自动启动下一个 Story (AC: #2, #3)
  - [ ] 监听 Story 完成事件
  - [ ] 从 `running_stories` 移除已完成的 Story
  - [ ] 调用 `story_dag.get_parallel_stories(completed_stories)` 获取可启动的 Story
  - [ ] 过滤出依赖已满足且未启动的 Story
  - [ ] 启动下一个 Story(如果有空闲槽位)

- [ ] 实现 `SubagentOrchestrator.start_story_agent(story, epic, worktree_path)` 方法 (AC: #1)
  - [ ] 构建 Story 级别的 prompt(仅包含单个 Story)
  - [ ] 使用 Claude Code Task 工具启动 Subagent
  - [ ] 设置工作目录为 `worktree_path`
  - [ ] 返回 Subagent ID (Task ID)

- [ ] 实现 Story 级别 prompt 构建逻辑 (AC: #1)
  - [ ] 包含 Story 标题和 Acceptance Criteria
  - [ ] 包含 Story 的技术要求
  - [ ] 包含 Epic 上下文(Epic 目标、已完成的 Story)
  - [ ] 明确指示: "完成后 commit 并输出 'Story X.Y completed.'"

- [ ] 实现 Story 完成监控 (AC: #2, #4)
  - [ ] 为每个 Story Subagent 启动独立的监控任务
  - [ ] 流式读取 Subagent 输出
  - [ ] 解析 "Story X.Y completed" 事件
  - [ ] 更新 Story 状态为 "completed"
  - [ ] 触发 Epic 进度更新

- [ ] 实现 Epic 进度聚合 (AC: #4)
  - [ ] 计算进度: `len(completed_stories) / len(epic.stories) * 100`
  - [ ] 统计运行中的 Story 数量
  - [ ] 更新 Epic 状态文件
  - [ ] 触发 TUI 更新事件

- [ ] 编写单元测试 (AC: #1, #2, #3, #4)
  - [ ] `test_start_epic_multi_mode()` - 测试 Multi 模式启动
  - [ ] `test_story_dag_construction()` - 测试 Story DAG 构建
  - [ ] `test_story_concurrency_limit()` - 测试并发限制
  - [ ] `test_auto_start_next_story()` - 测试自动启动队列中的 Story
  - [ ] `test_respect_story_dependencies()` - 测试依赖关系验证
  - [ ] `test_epic_progress_aggregation()` - 测试进度聚合
  - [ ] 使用 mock Claude Code Task 工具

## Dev Notes

### 架构约束

- **Story 并发限制**: `epic.story_concurrency` 控制 Epic 内并行的 Story 数量(默认 3)
- **全局并发限制**: 所有 Epic 和 Story 的总 Subagent 数量受 `subagent.max_concurrent` 限制
- **依赖关系**: Story 依赖关系从 Epic 文档的 Story 元数据中解析
- **Worktree 共享**: 同一 Epic 的所有 Story Subagent 共享一个 Worktree,需要同步 Git 操作

### 实现要点

**1. Scheduler.start_epic_multi_mode() 实现**:
```python
async def start_epic_multi_mode(self, epic: Epic, worktree_path: str) -> str:
    """
    Multi 模式启动 Epic: 多个 Story 级别 Subagent

    Args:
        epic: Epic 对象
        worktree_path: Git Worktree 路径

    Returns:
        聚合 agent_id (如 "multi-epic-3")
    """
    # 1. 构建 Story DAG
    story_dag = self.dependency_analyzer.build_story_dag(epic.stories)

    # 2. 验证 DAG(检测循环依赖)
    if story_dag.has_cycle():
        raise DependencyError(
            f"Epic {epic.id} has circular Story dependencies"
        )

    self.logger.info(
        f"Epic {epic.id}: Story DAG built with {len(epic.stories)} stories"
    )

    # 3. 初始化 Story 并发状态
    story_concurrency = epic.story_concurrency or 3
    running_stories = []  # List[(story_id, agent_id)]
    completed_stories = []

    # 4. 启动初始的可并行 Story
    parallel_stories = story_dag.get_parallel_stories(completed=[])

    for story in parallel_stories[:story_concurrency]:
        agent_id = await self._start_single_story(
            story, epic, worktree_path
        )
        running_stories.append((story.id, agent_id))

        self.logger.info(
            f"Epic {epic.id}: Started Story {story.id} "
            f"(agent: {agent_id})"
        )

    # 5. 启动监控任务(异步处理 Story 完成)
    asyncio.create_task(
        self._monitor_multi_mode_progress(
            epic, story_dag, running_stories, completed_stories
        )
    )

    self.logger.info(
        f"Epic {epic.id} started in multi mode: "
        f"{len(running_stories)} stories running, "
        f"{len(epic.stories) - len(running_stories)} queued"
    )

    # 6. 返回聚合 agent_id
    return f"multi-epic-{epic.id}"

async def _start_single_story(
    self,
    story: Story,
    epic: Epic,
    worktree_path: str
) -> str:
    """启动单个 Story 的 Subagent"""
    # 构建 Story 级别 prompt
    prompt = self._build_story_prompt(story, epic)

    # 启动 Subagent
    agent_id = await self.orchestrator.start_story_agent(
        story=story,
        epic=epic,
        worktree_path=worktree_path,
        prompt=prompt
    )

    return agent_id
```

**2. Story DAG 构建**:
```python
# 在 DependencyAnalyzer 中实现

class DependencyAnalyzer:
    def build_story_dag(self, stories: List[Story]) -> DAG:
        """
        构建 Story 依赖关系图

        Story 依赖从 Story 元数据的 `depends_on` 字段解析:

        Story 示例:
        ```yaml
        id: "3.5"
        title: "Merge conflict detection"
        depends_on: ["3.2", "3.3"]  # 依赖 Story 3.2 和 3.3
        ```
        """
        dag = DAG()

        # 添加所有 Story 作为节点
        for story in stories:
            dag.add_node(story.id, story)

        # 添加依赖边
        for story in stories:
            if story.depends_on:
                for dep_id in story.depends_on:
                    dag.add_edge(dep_id, story.id)

        # 检测循环依赖
        if dag.has_cycle():
            cycle = dag.find_cycle()
            raise DependencyError(
                f"Circular dependency detected in Stories: {cycle}"
            )

        return dag

class DAG:
    def get_parallel_stories(self, completed: List[str]) -> List[Story]:
        """
        获取可以并行启动的 Story

        条件:
        1. 依赖的 Story 都在 completed 列表中
        2. Story 本身未完成
        """
        parallel = []

        for story_id, story in self.nodes.items():
            if story_id in completed:
                continue

            # 检查所有依赖是否已完成
            deps = self.get_dependencies(story_id)
            if all(dep in completed for dep in deps):
                parallel.append(story)

        return parallel
```

**3. Story 级别 Prompt 构建**:
```python
def _build_story_prompt(self, story: Story, epic: Epic) -> str:
    """
    构建 Story 级别的 Subagent prompt

    Prompt 结构:
    - Epic 上下文(简要)
    - 单个 Story 详情
    - 开发指令
    - 架构引用
    """
    # 加载架构文档
    architecture = self._load_architecture_docs()

    # 已完成的 Story(提供上下文)
    completed_context = ""
    if epic.completed_stories:
        completed_context = f"""
## Completed Stories (for context)

The following Stories in this Epic have already been completed:
{chr(10).join(f"- Story {s}" for s in epic.completed_stories)}

Build upon these implementations where appropriate.
        """.strip()

    # 组装 prompt
    prompt = f"""
# Story {story.id}: {story.title}

## Epic Context

This Story is part of Epic {epic.id}: {epic.title}

{epic.description}

{completed_context}

## Story Goal

{story.description}

## Acceptance Criteria

{self._format_acceptance_criteria(story.acceptance_criteria)}

## Technical Notes

{story.technical_notes or 'N/A'}

## Development Instructions

1. **Implement the Story**: Follow the acceptance criteria exactly.
2. **Write tests**: Include unit tests with > 80% coverage.
3. **Commit your work**: After completing the Story, run:
   ```bash
   git add .
   git commit -m "Story {story.id}: {story.title}"
   ```
4. **Report completion**: Output exactly: "Story {story.id} completed."

## Project Architecture Reference

{architecture}

## Current Worktree

You are working in: {epic.worktree_path}
Branch: epic-{epic.id}

---

Begin implementation now. Good luck!
    """.strip()

    return prompt
```

**4. SubagentOrchestrator.start_story_agent() 实现**:
```python
async def start_story_agent(
    self,
    story: Story,
    epic: Epic,
    worktree_path: str,
    prompt: str
) -> str:
    """
    启动 Story 级别 Subagent

    Args:
        story: Story 对象
        epic: 所属 Epic
        worktree_path: Git Worktree 路径
        prompt: Story prompt

    Returns:
        Subagent ID (Task ID)
    """
    # 配置 Task
    task_config = {
        "description": f"Story {story.id}: {story.title}",
        "prompt": prompt,
        "model": self.config.get("subagent.model", "claude-sonnet-4"),
        "timeout": self.config.get("subagent.story_timeout", 1800),  # 30 分钟
        "working_directory": worktree_path,
    }

    # 启动 Task
    task = await Task.create(**task_config)

    # 记录启动
    self.logger.info(
        f"Started Story agent: story={story.id}, epic={epic.id}, "
        f"task_id={task.id}, worktree={worktree_path}"
    )

    # 存储 Task 引用
    self.active_story_tasks[(epic.id, story.id)] = task

    return task.id
```

**5. Multi 模式进度监控**:
```python
import re

async def _monitor_multi_mode_progress(
    self,
    epic: Epic,
    story_dag: DAG,
    running_stories: List[Tuple[str, str]],
    completed_stories: List[str]
):
    """
    监控 Multi 模式 Epic 的进度

    职责:
    1. 监听所有 Story Subagent 的完成事件
    2. 更新 Epic 进度
    3. 自动启动下一个可并行的 Story
    4. 检测 Epic 完成
    """
    story_concurrency = epic.story_concurrency or 3

    while running_stories or len(completed_stories) < len(epic.stories):
        # 等待任意 Story 完成
        completed_story_id, agent_id = await self._wait_for_any_story_completion(
            running_stories
        )

        # 更新状态
        completed_stories.append(completed_story_id)
        running_stories.remove((completed_story_id, agent_id))

        # 更新 Epic 进度
        progress = len(completed_stories) / len(epic.stories) * 100
        epic.progress = progress
        epic.completed_stories = completed_stories

        await self.state_manager.update_epic_state(epic)

        self.logger.info(
            f"Epic {epic.id}: Story {completed_story_id} completed "
            f"({len(completed_stories)}/{len(epic.stories)}, {progress:.0f}%)"
        )

        # 触发 TUI 更新
        await self.event_bus.emit("epic_progress_updated", {
            "epic_id": epic.id,
            "progress": progress,
            "completed_stories": completed_stories,
            "running_stories": [s_id for s_id, _ in running_stories],
            "total_stories": len(epic.stories)
        })

        # 启动下一个可并行的 Story
        if len(running_stories) < story_concurrency:
            next_stories = story_dag.get_parallel_stories(completed_stories)

            for story in next_stories:
                if story.id in completed_stories:
                    continue
                if any(s_id == story.id for s_id, _ in running_stories):
                    continue
                if len(running_stories) >= story_concurrency:
                    break

                # 启动 Story
                try:
                    agent_id = await self._start_single_story(
                        story, epic, epic.worktree_path
                    )
                    running_stories.append((story.id, agent_id))

                    self.logger.info(
                        f"Epic {epic.id}: Auto-started Story {story.id} "
                        f"(dependencies satisfied)"
                    )

                except Exception as e:
                    self.logger.error(
                        f"Failed to start Story {story.id}: {e}"
                    )

    # 所有 Story 完成
    self.logger.info(f"Epic {epic.id} all Stories completed!")
    epic.status = "completed"
    await self.state_manager.update_epic_state(epic)

    # 触发 Epic 完成事件(质量检查、合并等)
    await self.on_epic_completed(epic.id)

async def _wait_for_any_story_completion(
    self,
    running_stories: List[Tuple[str, str]]
) -> Tuple[str, str]:
    """
    等待任意一个 Story 完成

    Returns:
        (completed_story_id, agent_id)
    """
    # 为每个 Story 创建监控任务
    tasks = []
    for story_id, agent_id in running_stories:
        task = asyncio.create_task(
            self._monitor_single_story_completion(story_id, agent_id)
        )
        tasks.append((story_id, agent_id, task))

    # 等待任意一个完成
    done, pending = await asyncio.wait(
        [t for _, _, t in tasks],
        return_when=asyncio.FIRST_COMPLETED
    )

    # 取消其他任务(它们会继续运行,但监控会停止)
    for task in pending:
        task.cancel()

    # 找到完成的 Story
    for story_id, agent_id, task in tasks:
        if task in done:
            return story_id, agent_id

async def _monitor_single_story_completion(
    self,
    story_id: str,
    agent_id: str
):
    """
    监控单个 Story 的完成

    通过解析 Subagent 输出识别 "Story X.Y completed"
    """
    task = self.orchestrator.active_story_tasks.get(
        (epic.id, story_id)
    )

    if not task:
        self.logger.warning(
            f"No active task found for Story {story_id}"
        )
        return

    pattern = re.compile(
        rf"Story\s+{re.escape(story_id)}\s+completed",
        re.IGNORECASE
    )

    # 流式读取输出
    async for line in task.stream_output():
        if pattern.search(line):
            self.logger.debug(
                f"Story {story_id} completion detected: {line}"
            )
            return  # 完成
```

**6. Epic 状态文件结构(Multi 模式)**:
```yaml
# .aedt/projects/{project-id}/epics/epic-3.yaml
epic_id: 3
title: "Dependency Analysis Module"
status: "developing"
execution_mode: "auto"
chosen_execution_mode: "multi"
story_concurrency: 3
worktree_path: ".aedt/worktrees/epic-3"
agent_id: "multi-epic-3"
progress: 62.5
completed_stories: ["3.1", "3.2", "3.3", "3.4", "3.5"]
running_stories: ["3.6", "3.7", "3.8"]
stories:
  - id: "3.1"
    status: "completed"
    agent_id: "task-abc123"
    commit_hash: "a1b2c3d"
  - id: "3.2"
    status: "completed"
    agent_id: "task-def456"
    commit_hash: "e4f5g6h"
  # ...
  - id: "3.6"
    status: "in-progress"
    agent_id: "task-xyz789"
  - id: "3.7"
    status: "in-progress"
    agent_id: "task-uvw012"
  - id: "3.8"
    status: "in-progress"
    agent_id: "task-rst345"
```

### 从前一个 Story 的经验教训

**从 Story 5-3 (Story 级别 Subagent 启动准备)**:

Story 5-3 简化了 Epic 启动流程,统一使用 Story 级别 Subagent:

- **架构简化**: 移除了执行模式决策逻辑,固定使用 Multi 模式
- **上下文隔离**: 每个 Story 使用独立 Subagent,避免 AI 上下文累积导致降级
- **启动准备**: 为本 Story 准备好 Epic 元数据(story_concurrency 参数)

**在本 Story 中的应用**:

1. **Subagent 启动逻辑**: 实现 `start_story_agent()` 方法,使用 Claude Code Task 工具
2. **Prompt 构建**: 构建结构化的 Story 级别 prompt,包含上下文、指令、架构引用
3. **监控机制**: Multi 模式需要监控多个 Subagent,使用 `asyncio.wait()` 并发监听
4. **状态管理**: Epic 状态需要跟踪多个 Story 的状态,而不仅仅是整体进度

### 项目结构对齐

**修改组件**:
- `src/scheduler/scheduler.py` - 添加 `start_epic_multi_mode()` 方法
- `src/subagent/orchestrator.py` - 添加 `start_story_agent()` 方法
- `src/dependency/analyzer.py` - 添加 `build_story_dag()` 方法

**数据模型**:
- `src/models/epic.py` - Epic 类添加字段:
  - `running_stories: List[str]` - 运行中的 Story ID 列表
- `src/models/story.py` - Story 类添加字段:
  - `depends_on: List[str]` - 依赖的 Story ID 列表
  - `agent_id: Optional[str]` - Subagent ID
  - `commit_hash: Optional[str]` - 完成后的 Git commit hash

### 测试策略

**单元测试**:
```python
# tests/scheduler/test_multi_mode.py

async def test_start_epic_multi_mode():
    """测试 Multi 模式启动"""
    epic = Epic(
        id="3",
        stories=[
            Story("3.1"), Story("3.2"), Story("3.3"),
            Story("3.4"), Story("3.5"), Story("3.6"),
            Story("3.7"), Story("3.8")
        ],
        story_concurrency=3,
        worktree_path=".aedt/worktrees/epic-3"
    )

    scheduler = Scheduler(...)
    agent_id = await scheduler.start_epic_multi_mode(epic, epic.worktree_path)

    assert agent_id == "multi-epic-3"
    # 验证启动了 3 个 Story
    assert len(scheduler.orchestrator.active_story_tasks) == 3

async def test_respect_story_dependencies():
    """测试依赖关系验证"""
    stories = [
        Story("3.1"),
        Story("3.2"),
        Story("3.3", depends_on=["3.1", "3.2"]),  # 依赖 3.1 和 3.2
    ]
    epic = Epic(id="3", stories=stories, story_concurrency=3)

    scheduler = Scheduler(...)
    await scheduler.start_epic_multi_mode(epic, epic.worktree_path)

    # 初始只启动 3.1 和 3.2
    running = [s_id for s_id, _ in scheduler.running_stories]
    assert "3.1" in running
    assert "3.2" in running
    assert "3.3" not in running  # 依赖未满足

    # 模拟 3.1 和 3.2 完成
    await scheduler._on_story_completed("3.1")
    await scheduler._on_story_completed("3.2")

    # 3.3 应该自动启动
    running = [s_id for s_id, _ in scheduler.running_stories]
    assert "3.3" in running

async def test_epic_progress_aggregation():
    """测试进度聚合"""
    epic = Epic(id="3", stories=[Story(f"3.{i}") for i in range(1, 9)])
    epic.completed_stories = ["3.1", "3.2", "3.3", "3.4", "3.5"]

    # 5/8 完成
    progress = len(epic.completed_stories) / len(epic.stories) * 100
    assert progress == pytest.approx(62.5, rel=1e-2)
```

### References

- [Source: docs/epics.md#Story-5.5 - Epic 5 Story 定义]
- [Source: docs/prd.md#Subagent 编排系统 - FR22]
- [Source: docs/architecture.md#Story 级别 Subagent 设计]
- [Source: docs/sprint-artifacts/5-3-story-level-subagent-startup-preparation.md - Story 级别 Subagent 准备]

**覆盖的功能需求**:
- FR22: 系统可以监听 Subagent 的输出和进度
- 架构需求: Story 级别 Subagent 实现,依赖关系处理

**架构决策**:
- 所有 Epic 统一使用 Story 级别 Subagent (Multi 模式)
- 避免 AI 上下文累积导致代码质量降级

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
- 2025-11-24: 更新引用 - 移除 Story 5.4 引用,更新为 Story 5.3 (SM Agent)
