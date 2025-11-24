# Story 5.6: 处理 Epic 完成并触发质量检查

Status: drafted

## Story

作为用户,
我希望 AEDT 在 Epic 完成时自动运行质量检查,
以便只有高质量的代码被合并。

## Acceptance Criteria

1. **Epic 完成时触发质量检查**
   - 给定 Epic 1 完成所有 Story
   - 当最后一个 Story 标记为完成时
   - Epic 状态设置为 "quality_checking"
   - 触发 "epic_complete" 阶段的质量门控
   - 系统记录质量检查开始时间

2. **质量检查通过后合并**
   - 给定质量检查全部通过
   - 当质量检查完成时
   - Epic 状态变为 "merging"
   - 调用 `WorktreeManager.merge_to_main()` 合并到主分支
   - 如果合并成功,Epic 状态变为 "completed"

3. **质量检查失败处理**
   - 给定质量检查有任何失败
   - 当检查完成时
   - Epic 状态设置为 "failed"
   - 记录失败详情(失败的检查、错误信息)
   - 通知用户并提供修复指导
   - 保留 Worktree 不清理,便于调试

4. **Epic 完成后自动启动队列**
   - 给定 Epic 1 成功完成并合并
   - 当合并完成时
   - 调用 `Scheduler.auto_start_queued()` 启动队列中的下一个 Epic
   - 释放并发槽位,允许新 Epic 启动

## Tasks / Subtasks

- [ ] 实现 `Scheduler.on_epic_completed(epic_id)` 方法 (AC: #1, #2, #3, #4)
  - [ ] 接收 Epic ID 作为参数
  - [ ] 更新 Epic 状态为 "quality_checking"
  - [ ] 触发质量检查流程
  - [ ] 根据检查结果决定下一步(合并或失败)
  - [ ] 记录完整的完成流程到日志

- [ ] 集成质量门控系统 (AC: #1, #3)
  - [ ] 调用 `QualityGate.run_checks("epic_complete", worktree_path)`
  - [ ] 等待所有质量检查完成
  - [ ] 收集检查结果(通过/失败,详细信息)
  - [ ] 如果配置禁用质量检查,跳过此步骤

- [ ] 实现合并流程 (AC: #2)
  - [ ] 质量检查通过后,更新状态为 "merging"
  - [ ] 调用 `WorktreeManager.merge_to_main(epic)`
  - [ ] 等待合并完成(可能涉及冲突检测)
  - [ ] 合并成功后,更新状态为 "completed"
  - [ ] 触发 Worktree 清理(如果配置启用自动清理)

- [ ] 实现失败处理逻辑 (AC: #3)
  - [ ] 质量检查失败时,更新状态为 "failed"
  - [ ] 保存失败详情到 Epic 状态文件:
    - [ ] `failed_checks: List[str]` - 失败的检查项
    - [ ] `failure_messages: Dict[str, str]` - 每个失败检查的错误信息
  - [ ] 保留 Worktree 不清理
  - [ ] 生成修复指导(基于失败类型)
  - [ ] 触发用户通知事件

- [ ] 实现自动启动队列逻辑 (AC: #4)
  - [ ] Epic 完成(状态为 "completed")后调用 `auto_start_queued()`
  - [ ] 从并发队列中移除已完成的 Epic
  - [ ] 启动下一个可运行的 Epic(如果有)
  - [ ] 记录自动启动事件

- [ ] 添加配置支持 (AC: #1, #2)
  - [ ] 支持 `quality_gates.skip_epic_complete` 配置(跳过质量检查,直接合并)
  - [ ] 支持 `git.auto_merge` 配置(禁用自动合并,手动触发)
  - [ ] 支持 `git.auto_cleanup` 配置(合并后自动清理 Worktree)

- [ ] 编写单元测试 (AC: #1, #2, #3, #4)
  - [ ] `test_epic_completion_triggers_quality_check()` - 测试完成触发质量检查
  - [ ] `test_quality_check_pass_triggers_merge()` - 测试检查通过后合并
  - [ ] `test_quality_check_fail_marks_failed()` - 测试检查失败处理
  - [ ] `test_merge_success_starts_queued_epic()` - 测试合并后启动队列
  - [ ] `test_skip_quality_checks_config()` - 测试跳过质量检查配置
  - [ ] 使用 mock QualityGate 和 WorktreeManager

## Dev Notes

### 架构约束

- **质量门控依赖**: 需要 Epic 7 的 QualityGate 模块(可能尚未实现,需要定义接口)
- **合并依赖**: 需要 Epic 4 的 WorktreeManager.merge_to_main() 方法
- **状态一致性**: Epic 状态变化需要原子更新,避免中间状态
- **事件驱动**: Epic 完成是异步事件,需要事件总线协调

### 实现要点

**1. Scheduler.on_epic_completed() 实现**:
```python
async def on_epic_completed(self, epic_id: str):
    """
    Epic 完成处理流程

    流程:
    1. 更新状态为 "quality_checking"
    2. 运行质量检查
    3. 如果通过 → 合并到主分支
    4. 如果失败 → 标记失败并保留 Worktree
    5. 如果合并成功 → 启动队列中的下一个 Epic

    Args:
        epic_id: Epic ID
    """
    epic = self.epic_parser.get_epic(epic_id)

    self.logger.info(
        f"Epic {epic_id} completed all Stories. "
        f"Starting completion flow..."
    )

    # 1. 更新状态为 quality_checking
    epic.status = "quality_checking"
    epic.completed_at = datetime.now().isoformat()
    await self.state_manager.update_epic_state(epic)

    # 触发 TUI 更新
    await self.event_bus.emit("epic_status_changed", {
        "epic_id": epic_id,
        "status": "quality_checking"
    })

    # 2. 运行质量检查
    try:
        quality_result = await self._run_quality_checks(epic)

        if quality_result.passed:
            # 质量检查通过 → 合并
            await self._merge_epic(epic)
        else:
            # 质量检查失败 → 标记失败
            await self._handle_quality_check_failure(epic, quality_result)

    except Exception as e:
        self.logger.error(
            f"Epic {epic_id} completion flow failed: {e}",
            exc_info=True
        )
        await self._handle_completion_error(epic, e)

async def _run_quality_checks(self, epic: Epic) -> QualityCheckResult:
    """
    运行 Epic 完成阶段的质量检查

    Returns:
        QualityCheckResult 包含检查结果
    """
    # 检查配置是否跳过质量检查
    if self.config.get("quality_gates.skip_epic_complete", False):
        self.logger.info(
            f"Epic {epic.id}: Skipping quality checks "
            f"(skip_epic_complete=true)"
        )
        return QualityCheckResult(passed=True, checks=[])

    self.logger.info(
        f"Epic {epic.id}: Running quality checks "
        f"(stage: epic_complete)"
    )

    # 调用 QualityGate 模块
    result = await self.quality_gate.run_checks(
        stage="epic_complete",
        worktree_path=epic.worktree_path,
        epic=epic
    )

    # 记录检查结果
    self.logger.info(
        f"Epic {epic.id}: Quality checks completed. "
        f"Passed: {result.passed}, "
        f"Failed: {len(result.failed_checks)}"
    )

    return result

async def _merge_epic(self, epic: Epic):
    """
    合并 Epic 到主分支

    流程:
    1. 更新状态为 "merging"
    2. 调用 WorktreeManager.merge_to_main()
    3. 如果成功 → 更新状态为 "completed"
    4. 清理 Worktree(如果配置启用)
    5. 启动队列中的下一个 Epic
    """
    # 检查配置是否禁用自动合并
    if not self.config.get("git.auto_merge", True):
        self.logger.info(
            f"Epic {epic.id}: Auto-merge disabled. "
            f"Manual merge required."
        )
        epic.status = "ready_to_merge"
        await self.state_manager.update_epic_state(epic)
        return

    # 1. 更新状态为 merging
    epic.status = "merging"
    await self.state_manager.update_epic_state(epic)

    await self.event_bus.emit("epic_status_changed", {
        "epic_id": epic.id,
        "status": "merging"
    })

    # 2. 执行合并
    try:
        merge_result = await self.worktree_manager.merge_to_main(epic)

        if merge_result.success:
            # 3. 合并成功
            epic.status = "completed"
            epic.merged_at = datetime.now().isoformat()
            epic.merge_commit_hash = merge_result.commit_hash
            await self.state_manager.update_epic_state(epic)

            self.logger.info(
                f"Epic {epic.id} merged successfully. "
                f"Commit: {merge_result.commit_hash}"
            )

            # 4. 清理 Worktree
            if self.config.get("git.auto_cleanup", True):
                await self.worktree_manager.cleanup_worktree(epic)

            # 5. 启动队列中的下一个 Epic
            await self.auto_start_queued(epic.id)

            # 触发完成事件
            await self.event_bus.emit("epic_completed", {
                "epic_id": epic.id,
                "merge_commit": merge_result.commit_hash
            })

        else:
            # 合并失败(可能有冲突)
            await self._handle_merge_failure(epic, merge_result)

    except Exception as e:
        self.logger.error(
            f"Epic {epic.id} merge failed: {e}",
            exc_info=True
        )
        await self._handle_merge_error(epic, e)

async def _handle_quality_check_failure(
    self,
    epic: Epic,
    result: QualityCheckResult
):
    """
    处理质量检查失败

    保存失败详情,保留 Worktree,通知用户
    """
    epic.status = "failed"
    epic.failed_reason = "quality_check_failed"
    epic.failed_checks = result.failed_checks
    epic.failure_messages = result.failure_messages

    await self.state_manager.update_epic_state(epic)

    self.logger.error(
        f"Epic {epic.id} quality checks failed. "
        f"Failed checks: {', '.join(result.failed_checks)}"
    )

    # 生成修复指导
    guidance = self._generate_fix_guidance(result)

    # 触发失败事件
    await self.event_bus.emit("epic_failed", {
        "epic_id": epic.id,
        "reason": "quality_check_failed",
        "failed_checks": result.failed_checks,
        "guidance": guidance,
        "worktree_path": epic.worktree_path  # 保留供调试
    })

def _generate_fix_guidance(self, result: QualityCheckResult) -> str:
    """
    根据失败的检查生成修复指导

    示例:
    - lint 失败 → "Run `npm run lint -- --fix` to auto-fix issues"
    - tests 失败 → "Fix failing tests in: test/unit/foo.test.js"
    """
    guidance = []

    for check_name in result.failed_checks:
        if check_name == "lint":
            guidance.append(
                "Run linter with auto-fix: `npm run lint -- --fix` or `pylint --fix`"
            )
        elif check_name == "unit_tests":
            guidance.append(
                f"Fix failing unit tests. See logs: {result.failure_messages[check_name]}"
            )
        elif check_name == "format_check":
            guidance.append(
                "Run formatter: `npm run format` or `black .`"
            )
        else:
            guidance.append(
                f"Fix {check_name} issues. Details: {result.failure_messages.get(check_name, 'N/A')}"
            )

    guidance.append(
        f"\nWorktree preserved at: {epic.worktree_path}"
    )
    guidance.append(
        "After fixing, resume with: `aedt resume epic-{epic.id}`"
    )

    return "\n".join(guidance)
```

**2. QualityCheckResult 数据模型**:
```python
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class QualityCheckResult:
    """质量检查结果"""
    passed: bool  # 所有检查是否通过
    checks: List[str]  # 运行的检查列表
    failed_checks: List[str] = None  # 失败的检查
    failure_messages: Dict[str, str] = None  # 每个失败检查的详细信息

    def __post_init__(self):
        if self.failed_checks is None:
            self.failed_checks = []
        if self.failure_messages is None:
            self.failure_messages = {}
```

**3. QualityGate 接口定义(Epic 7 将实现)**:
```python
class QualityGate:
    """
    质量门控系统

    负责运行各种质量检查(linter, tests, format check 等)
    """

    async def run_checks(
        self,
        stage: str,
        worktree_path: str,
        epic: Epic
    ) -> QualityCheckResult:
        """
        运行指定阶段的质量检查

        Args:
            stage: 检查阶段 ("epic_complete", "pre_commit", "pre_merge")
            worktree_path: Git Worktree 路径(运行检查的目录)
            epic: Epic 对象(用于上下文)

        Returns:
            QualityCheckResult 包含检查结果
        """
        # Epic 7 将实现此方法
        # MVP 阶段可以返回 mock 结果或简单的 lint + test
        raise NotImplementedError("QualityGate will be implemented in Epic 7")
```

**4. WorktreeManager.merge_to_main() 接口(Epic 4 实现)**:
```python
@dataclass
class MergeResult:
    """合并结果"""
    success: bool
    commit_hash: Optional[str] = None
    conflicts: List[str] = None  # 冲突文件列表
    error_message: Optional[str] = None

class WorktreeManager:
    async def merge_to_main(self, epic: Epic) -> MergeResult:
        """
        合并 Epic 分支到主分支

        Args:
            epic: Epic 对象

        Returns:
            MergeResult 包含合并结果
        """
        # Epic 4 将实现此方法
        raise NotImplementedError("WorktreeManager will be implemented in Epic 4")
```

**5. Epic 状态文件扩展**:
```yaml
# .aedt/projects/{project-id}/epics/epic-1.yaml
epic_id: 1
title: "Project Initialization and CLI Framework"
status: "completed"  # 新状态: quality_checking, merging, failed, ready_to_merge
worktree_path: ".aedt/worktrees/epic-1"
completed_at: "2025-11-24T10:30:00"
merged_at: "2025-11-24T10:35:00"
merge_commit_hash: "a1b2c3d4e5f6"

# 质量检查失败时的字段(仅在失败时)
failed_reason: "quality_check_failed"  # or "merge_failed"
failed_checks: ["lint", "unit_tests"]
failure_messages:
  lint: "ESLint found 3 errors in src/cli.js"
  unit_tests: "2 tests failed in tests/cli.test.js"
```

**6. 配置文件扩展**:
```yaml
# .aedt/config.yaml

quality_gates:
  skip_epic_complete: false  # 跳过 Epic 完成时的质量检查

git:
  auto_merge: true  # 质量检查通过后自动合并
  auto_cleanup: true  # 合并后自动清理 Worktree
```

### 从前一个 Story 的经验教训

**从 Story 5-5 (Multi 模式启动 Epic)**:

Story 5-5 展示了复杂的异步流程管理:

- **异步监控**: 使用 `asyncio.wait()` 等待多个任务完成
- **状态更新**: 及时更新状态并触发事件
- **错误处理**: 每个步骤都有异常处理

**在本 Story 中的应用**:

1. **流程编排**: Epic 完成流程也是多步骤异步操作,复用类似的模式
2. **事件驱动**: 触发 `epic_completed` 事件,通知其他模块(TUI、队列管理)
3. **失败恢复**: 失败时保留上下文,支持手动恢复

### 项目结构对齐

**修改组件**:
- `src/scheduler/scheduler.py` - 添加 `on_epic_completed()` 方法

**新增接口**(Epic 7 和 Epic 4 将实现):
- `src/quality/quality_gate.py` - QualityGate 接口定义
- `src/worktree/manager.py` - WorktreeManager.merge_to_main() 接口

**数据模型**:
- `src/models/quality.py` - QualityCheckResult 数据类
- `src/models/merge.py` - MergeResult 数据类
- `src/models/epic.py` - Epic 类添加字段:
  - `completed_at: Optional[str]`
  - `merged_at: Optional[str]`
  - `merge_commit_hash: Optional[str]`
  - `failed_reason: Optional[str]`
  - `failed_checks: List[str]`
  - `failure_messages: Dict[str, str]`

### 测试策略

**单元测试**:
```python
# tests/scheduler/test_epic_completion.py

async def test_epic_completion_triggers_quality_check():
    """测试 Epic 完成触发质量检查"""
    epic = Epic(id="1", status="developing")
    scheduler = Scheduler(...)

    # Mock QualityGate
    mock_result = QualityCheckResult(passed=True, checks=["lint", "tests"])
    scheduler.quality_gate.run_checks = AsyncMock(return_value=mock_result)

    await scheduler.on_epic_completed(epic.id)

    # 验证质量检查被调用
    scheduler.quality_gate.run_checks.assert_called_once_with(
        stage="epic_complete",
        worktree_path=epic.worktree_path,
        epic=epic
    )

async def test_quality_check_pass_triggers_merge():
    """测试质量检查通过后触发合并"""
    epic = Epic(id="1")
    scheduler = Scheduler(...)

    # Mock 质量检查通过
    mock_quality_result = QualityCheckResult(passed=True, checks=[])
    scheduler.quality_gate.run_checks = AsyncMock(return_value=mock_quality_result)

    # Mock 合并成功
    mock_merge_result = MergeResult(success=True, commit_hash="abc123")
    scheduler.worktree_manager.merge_to_main = AsyncMock(return_value=mock_merge_result)

    await scheduler.on_epic_completed(epic.id)

    # 验证合并被调用
    scheduler.worktree_manager.merge_to_main.assert_called_once()

    # 验证状态更新为 completed
    assert epic.status == "completed"
    assert epic.merge_commit_hash == "abc123"

async def test_quality_check_fail_marks_failed():
    """测试质量检查失败处理"""
    epic = Epic(id="1")
    scheduler = Scheduler(...)

    # Mock 质量检查失败
    mock_result = QualityCheckResult(
        passed=False,
        checks=["lint", "tests"],
        failed_checks=["lint"],
        failure_messages={"lint": "ESLint errors"}
    )
    scheduler.quality_gate.run_checks = AsyncMock(return_value=mock_result)

    await scheduler.on_epic_completed(epic.id)

    # 验证状态更新为 failed
    assert epic.status == "failed"
    assert epic.failed_reason == "quality_check_failed"
    assert "lint" in epic.failed_checks

async def test_merge_success_starts_queued_epic():
    """测试合并成功后启动队列中的 Epic"""
    epic = Epic(id="1")
    scheduler = Scheduler(...)

    # Mock 质量检查和合并成功
    scheduler.quality_gate.run_checks = AsyncMock(
        return_value=QualityCheckResult(passed=True, checks=[])
    )
    scheduler.worktree_manager.merge_to_main = AsyncMock(
        return_value=MergeResult(success=True, commit_hash="abc123")
    )
    scheduler.auto_start_queued = AsyncMock()

    await scheduler.on_epic_completed(epic.id)

    # 验证 auto_start_queued 被调用
    scheduler.auto_start_queued.assert_called_once_with(epic.id)
```

### References

- [Source: docs/epics.md#Story-5.6 - Epic 5 Story 定义]
- [Source: docs/prd.md#质量门控 - FR36, FR37]
- [Source: docs/prd.md#Git 自动化 - FR30]
- [Source: docs/architecture.md#质量门控架构 - 设计决策]

**覆盖的功能需求**:
- FR37: 系统可以在 Epic 完成时运行单元测试
- FR30: 系统可以在 Epic 完成后自动合并到主分支
- FR40: 系统可以在质量检查失败时通知用户

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
