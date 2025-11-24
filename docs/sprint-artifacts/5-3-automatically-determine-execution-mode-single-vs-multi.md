# Story 5.3: Story 级别 Subagent 启动准备

Status: drafted

## Story

作为用户,
我希望 AEDT 为每个 Story 启动独立的 Subagent,
以便避免上下文累积导致 AI 降级,保持每个 Story 的开发质量。

## Acceptance Criteria

1. **统一使用 Story 级别 Subagent**
   - 给定任何 Epic(无论有多少个 Story)
   - 当 AEDT 启动 Epic 时
   - 系统为每个 Story 启动独立的 Subagent
   - 每个 Subagent 拥有全新的上下文

2. **Epic 元数据解析**
   - 给定 Epic 文档包含 `story_concurrency` 字段
   - 当系统解析 Epic 时
   - 正确读取 `story_concurrency` 参数(默认 3)
   - 验证参数有效性(正整数,范围 1-10)

3. **Epic 启动流程集成**
   - 给定 Epic 已创建 Worktree
   - 当系统启动 Epic 时
   - 直接调用 `start_epic_multi_mode(epic, worktree_path)`
   - 不需要模式决策逻辑

4. **状态持久化**
   - 给定 Epic 启动后
   - 当系统保存状态时
   - Epic 状态文件包含 `story_concurrency` 参数
   - 重启后保持一致

## Tasks / Subtasks

- [ ] 简化 `Scheduler._start_epic()` 方法 (AC: #1, #3)
  - [ ] 移除执行模式决策逻辑
  - [ ] 直接调用 `start_epic_multi_mode(epic, worktree_path)`
  - [ ] 创建 Worktree 后立即启动 Story 级别 Subagent
  - [ ] 记录启动事件到日志

- [ ] 扩展 Epic 元数据解析 (AC: #2)
  - [ ] 在 Epic 文档 YAML frontmatter 中读取 `story_concurrency` 字段
  - [ ] 默认值: 3
  - [ ] 验证有效性: 正整数,范围 1-10
  - [ ] 无效时记录警告并使用默认值

- [ ] 更新 Epic 状态文件结构 (AC: #4)
  - [ ] 保存 `story_concurrency` 到状态文件
  - [ ] 保存每个 Story 的 Subagent ID
  - [ ] 保存 Story 的完成状态

- [ ] 移除不需要的配置参数 (AC: #1)
  - [ ] 删除 `execution_mode.auto_threshold` 配置
  - [ ] 简化配置文件结构

- [ ] 编写单元测试 (AC: #1, #2, #3, #4)
  - [ ] `test_direct_multi_mode_start()` - 测试直接启动 Multi 模式
  - [ ] `test_story_concurrency_parsing()` - 测试 story_concurrency 解析
  - [ ] `test_story_concurrency_validation()` - 测试参数验证
  - [ ] `test_state_persistence()` - 测试状态持久化

## Dev Notes

### 架构决策：为什么统一使用 Story 级别 Subagent？

**核心原因：避免 AI 上下文累积导致降级**

在实际使用 AI 编码工具时,发现了一个关键问题：

**问题场景：**
```
Epic 有 5 个 Story,使用 1 个 Epic 级别 Subagent 串行完成：

Story 1 完成 → 上下文已有很多代码
Story 2 完成 → 上下文继续增长
Story 3, 4, 5 → 上下文非常庞大

结果：AI 编辑器因上下文过载而降级：
- 使用 // ... existing code ... 省略实现
- 只给出代码框架,不写完整逻辑
- 跳过测试或简化测试
```

**解决方案：每个 Story 使用独立 Subagent**

**优势：**
1. ✅ **上下文隔离** - 每个 Story 都是全新上下文,AI 始终处于"最佳状态"
2. ✅ **并行能力最大化** - 即使小 Epic 也能并行(如果 Story 无依赖)
3. ✅ **失败隔离** - 一个 Story 失败不影响其他 Story
4. ✅ **实现简化** - 不需要维护两套启动逻辑

### 实现要点

**1. 简化的 Scheduler._start_epic() 实现**:
```python
async def _start_epic(self, epic_id: str):
    """
    启动单个 Epic - 统一使用 Story 级别 Subagent

    流程:
    1. 创建 Worktree
    2. 直接调用 start_epic_multi_mode()
    3. 更新状态
    """
    epic = self.epic_parser.get_epic(epic_id)

    # 1. 创建 Worktree(所有 Epic 都需要)
    worktree_path = await self.worktree_manager.create_worktree(epic)
    epic.worktree_path = worktree_path

    # 2. 启动 Story 级别 Subagent (Multi 模式)
    # Story 5.5 实现此方法
    await self.start_epic_multi_mode(epic, worktree_path)

    # 3. 更新状态并持久化
    epic.status = "developing"
    epic.agent_id = f"multi-epic-{epic.id}"
    await self.state_manager.update_epic_state(epic)

    self.logger.info(
        f"Epic {epic.id} started with Story-level Subagents "
        f"(story_concurrency: {epic.story_concurrency}, "
        f"worktree: {worktree_path})"
    )
```

**2. Epic 元数据结构**:

Epic 文档 YAML frontmatter 示例:
```yaml
epic_id: 5
title: "Intelligent Parallel Scheduling Engine"
depends_on: [3, 4]
priority: HIGH
story_concurrency: 3  # Epic 内 Story 最大并发数
estimated_stories: 7
```

**3. EpicParser 解析 story_concurrency**:
```python
class EpicParser:
    def parse_epic_metadata(self, frontmatter: dict) -> Epic:
        """解析 Epic 元数据"""
        story_concurrency = frontmatter.get("story_concurrency", 3)

        # 验证有效性
        if not isinstance(story_concurrency, int) or story_concurrency < 1 or story_concurrency > 10:
            self.logger.warning(
                f"Epic {frontmatter['epic_id']}: Invalid story_concurrency "
                f"'{story_concurrency}'. Defaulting to 3."
            )
            story_concurrency = 3

        epic = Epic(
            id=frontmatter["epic_id"],
            title=frontmatter["title"],
            depends_on=frontmatter.get("depends_on", []),
            priority=frontmatter.get("priority", "MEDIUM"),
            story_concurrency=story_concurrency,
            # ... 其他字段
        )

        return epic
```

**4. 简化的配置文件**:
```yaml
# .aedt/config.yaml
subagent:
  max_concurrent: 5  # 全局 Subagent 总数限制
  timeout: 3600
  model: "claude-sonnet-4"

# 不再需要 execution_mode 配置
```

**5. Epic 状态文件示例**:
```yaml
# .aedt/projects/{project-id}/epics/epic-5.yaml
epic_id: 5
title: "Intelligent Parallel Scheduling Engine"
status: "developing"
story_concurrency: 3  # Epic 内并发限制
worktree_path: ".aedt/worktrees/epic-5"
agent_id: "multi-epic-5"
progress: 42.8
completed_stories: ["5.1", "5.2", "5.3"]
running_stories: ["5.4", "5.5", "5.6"]
stories:
  - id: "5.1"
    status: "completed"
    agent_id: "task-abc123"
    commit_hash: "a1b2c3d"
  - id: "5.2"
    status: "completed"
    agent_id: "task-def456"
    commit_hash: "e4f5g6h"
  - id: "5.3"
    status: "completed"
    agent_id: "task-ghi789"
    commit_hash: "i8j9k0l"
  - id: "5.4"
    status: "in-progress"
    agent_id: "task-jkl012"
  - id: "5.5"
    status: "in-progress"
    agent_id: "task-mno345"
  - id: "5.6"
    status: "in-progress"
    agent_id: "task-pqr678"
  - id: "5.7"
    status: "queued"
```

### 与其他 Story 的关系

**Story 5.1 - 启动多个 Epic**:
- 复用 `_start_epic()` 方法
- 简化后的实现更清晰

**Story 5.2 - 并发控制**:
- Epic 级别并发: `max_concurrent` (全局)
- Story 级别并发: `story_concurrency` (Epic 内)

**Story 5.5 - Multi 模式实现**:
- 本 Story 准备好启动参数
- Story 5.5 实现具体的 Story Subagent 启动逻辑

**Story 5.6 - Epic 完成处理**:
- 所有 Story 完成后触发
- 不受执行模式影响

**Story 5.7 - 自动启动队列**:
- 复用简化后的 `_start_epic()` 方法

### 项目结构对齐

**修改组件**:
- `src/scheduler/scheduler.py` - 简化 `_start_epic()` 方法
- `src/epic/parser.py` - 解析 `story_concurrency` 参数

**数据模型**:
- `src/models/epic.py` - Epic 类包含 `story_concurrency` 字段

**配置文件**:
- `.aedt/config.yaml` - 移除 `execution_mode` 部分

**状态文件**:
- `.aedt/projects/{project-id}/epics/{epic-id}.yaml` - 移除 `chosen_execution_mode`,保留 `story_concurrency`

### 测试策略

**单元测试**:
```python
# tests/scheduler/test_story_level_subagent.py

async def test_direct_multi_mode_start():
    """测试直接启动 Story 级别 Subagent"""
    epic = Epic(
        id="1",
        stories=[Story("1.1"), Story("1.2"), Story("1.3")],
        story_concurrency=3
    )

    scheduler = Scheduler(...)
    await scheduler._start_epic(epic.id)

    # 验证直接调用了 start_epic_multi_mode
    scheduler.start_epic_multi_mode.assert_called_once_with(
        epic, epic.worktree_path
    )

def test_story_concurrency_parsing():
    """测试 story_concurrency 解析"""
    frontmatter = {
        "epic_id": 5,
        "title": "Test Epic",
        "story_concurrency": 4
    }

    parser = EpicParser()
    epic = parser.parse_epic_metadata(frontmatter)

    assert epic.story_concurrency == 4

def test_story_concurrency_validation():
    """测试 story_concurrency 验证"""
    # 测试无效值
    frontmatter = {
        "epic_id": 5,
        "title": "Test Epic",
        "story_concurrency": 15  # 超出范围
    }

    parser = EpicParser()
    epic = parser.parse_epic_metadata(frontmatter)

    # 应该回退到默认值
    assert epic.story_concurrency == 3

async def test_state_persistence():
    """测试状态持久化"""
    epic = Epic(id="5", story_concurrency=4)
    scheduler = Scheduler(...)

    await scheduler._start_epic(epic.id)

    # 检查状态文件
    saved_state = await state_manager.get_epic_state(epic.id)
    assert saved_state["story_concurrency"] == 4
    assert saved_state["agent_id"] == "multi-epic-5"
```

**集成测试**:
- 使用真实 Epic 文档测试元数据解析
- 测试启动流程与 Story 5.5 的集成
- 验证状态文件正确保存

### 架构简化的好处

**移除 Single 模式后:**

1. **代码更简洁**
   - 不需要 `determine_execution_mode()` 方法
   - 不需要 `if/else` 分支逻辑
   - `_start_epic()` 方法减少 50% 代码量

2. **配置更简单**
   - 移除 `execution_mode` 配置部分
   - 减少用户配置复杂度

3. **测试更简单**
   - 只需测试一种启动模式
   - 减少边界情况测试

4. **维护更容易**
   - 只维护一套 Subagent 启动逻辑
   - 减少技术债务

### References

- [Source: docs/epics.md#Story-5.3 - Epic 5 Story 定义]
- [Source: docs/prd.md#并行调度与 Subagent 编排]
- [Source: docs/architecture.md#Story 级别 Subagent 设计]
- [Source: docs/sprint-artifacts/5-2-control-maximum-concurrent-subagents.md - 并发控制]

**覆盖的架构需求**:
- Story 级别 Subagent 统一实现
- 上下文隔离设计

**架构决策记录**:
- **ADR**: 移除 Epic 级别 Subagent,统一使用 Story 级别 Subagent
- **原因**: 避免 AI 上下文累积导致代码质量降级
- **影响**: Story 5.4 不再需要,Epic 启动逻辑简化

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
- 2025-11-24: 重大架构变更 - 移除 Single 模式,统一使用 Story 级别 Subagent (SM Agent)
