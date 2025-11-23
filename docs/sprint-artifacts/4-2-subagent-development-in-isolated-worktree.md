# Story 4.2: Subagent 在隔离的 Worktree 中开发

Status: drafted

## Story

作为 Subagent，
我希望在隔离的 Git Worktree 中工作，
以便我的更改不会干扰其他并行的 Epic。

## Acceptance Criteria

1. **AC1: Subagent 工作目录设置**
   - 当 Epic 2 有一个位于 `.aedt/worktrees/epic-2/` 的 Worktree 时
   - Subagent 开始为 Epic 2 工作
   - Subagent 的工作目录被设置为 Worktree 路径
   - 所有文件操作都在 Worktree 内进行
   - 提交被记录到 "epic-2" 分支

2. **AC2: 并行开发隔离**
   - 当 Epic 3 在 `.aedt/worktrees/epic-3/` 中并行开发时
   - 两个 Subagent 都修改 `src/parser.py`
   - 更改在各自的 Worktree 中被隔离
   - 开发期间不发生冲突

## Tasks / Subtasks

- [ ] **任务 1：扩展 SubagentOrchestrator 支持 Worktree 路径** (AC: 1)
  - [ ] 1.1 修改 `start_epic_agent()` 方法接受 `worktree_path` 参数
  - [ ] 1.2 在 Subagent 启动时传递工作目录路径
  - [ ] 1.3 验证 Worktree 路径存在且可访问

- [ ] **任务 2：构建 Subagent Prompt 包含工作目录信息** (AC: 1)
  - [ ] 2.1 在 Subagent prompt 中添加："Working directory: <worktree_path>"
  - [ ] 2.2 明确指示所有操作应在指定目录内进行
  - [ ] 2.3 包含 Git 分支信息："Branch: epic-{id}"

- [ ] **任务 3：确保 Git 操作在 Worktree 中执行** (AC: 1)
  - [ ] 3.1 配置 Git 操作使用 Worktree 路径作为工作目录
  - [ ] 3.2 验证 `git commit` 和 `git status` 在正确的 Worktree 中运行
  - [ ] 3.3 添加路径验证，防止误操作主工作目录

- [ ] **任务 4：集成测试并行开发场景** (AC: 2)
  - [ ] 4.1 模拟两个 Epic 并行修改同一文件
  - [ ] 4.2 验证更改在各自 Worktree 中隔离
  - [ ] 4.3 确认不产生即时冲突（冲突仅在合并时检测）

- [ ] **任务 5：单元测试** (AC: 1, 2)
  - [ ] 5.1 测试 Subagent 工作目录正确设置
  - [ ] 5.2 测试 Git 操作在 Worktree 中执行
  - [ ] 5.3 测试并行 Subagent 隔离性

## Dev Notes

### 架构约束和模式

**模块定位：**
- 属于**应用逻辑层 (Application Layer)**
- `SubagentOrchestrator` 与 `WorktreeManager` 协作
- 为 Subagent 提供隔离的开发环境

**技术实现要点：**

1. **Subagent 启动时传递 Worktree 路径**
   ```python
   def start_epic_agent(self, epic: Epic, worktree_path: str):
       """启动 Epic-level Subagent，工作目录设为 Worktree"""
       prompt = f"""
       Working directory: {worktree_path}
       Branch: epic-{epic.id}

       You are developing Epic {epic.id}: {epic.title}
       All file operations should occur in the working directory.
       Commits should be made to the current branch.
       """
       # 启动 Claude Code Task 并传递 prompt
   ```

2. **Git 操作路径配置**
   - 使用 `GitPython` 的 `Repo(worktree_path)` 确保操作在正确位置
   - 验证当前分支为 `epic-{id}`
   - 所有提交自动记录到 Epic 分支

3. **并行隔离机制**
   - 每个 Epic 独立的 Worktree 确保文件系统级别隔离
   - Subagent 只能访问自己的 Worktree 目录
   - 冲突仅在合并到主分支时检测（Story 4.4 实现）

4. **依赖关系**
   - **前置条件：** Story 4.1 (Worktree 必须已创建)
   - **关联：** Epic 6 (Subagent Orchestration System)
   - **后续：** Story 4.3 (Story-level 提交)

### 从前一个 Story 的学习

**从 Story 4.1 获得的上下文：**
- Worktree 创建在 `.aedt/worktrees/epic-{id}/`
- 分支命名为 `epic-{id}`
- Worktree 信息存储在 Epic 状态中
- `WorktreeManager` 提供 `create_worktree()` 方法

**复用接口：**
- 使用 `WorktreeManager` 获取 Epic 的 Worktree 路径
- 读取 Epic 状态获取 `worktree_path` 和 `branch_name`

### 项目结构对齐

**预期修改文件：**
```
aedt/
├── application/
│   └── subagent_orchestrator.py   # 修改：添加 worktree_path 参数
├── infrastructure/
│   └── worktree_manager.py         # 使用：获取 Worktree 信息
└── tests/
    └── test_subagent_orchestrator.py  # 新增测试
```

**接口变更：**
```python
# Before
def start_epic_agent(self, epic: Epic):
    pass

# After
def start_epic_agent(self, epic: Epic, worktree_path: str):
    pass
```

### 测试策略

**单元测试覆盖：**
- Subagent 启动时正确设置工作目录
- Git 操作在 Worktree 中执行
- Prompt 包含正确的路径和分支信息

**集成测试场景：**
- 两个 Epic 并行开发，修改相同文件
- 验证隔离性和无冲突
- Scheduler → WorktreeManager → SubagentOrchestrator 完整流程

### References

- [Source: docs/epics.md#Epic-4-Story-4.2]
- [Source: docs/architecture.md#3.4-Subagent-编排模块]
- [Source: stories/4-1-create-git-worktree-for-epic.md] (前一个 story)
- FR Coverage: FR28 (Worktree 隔离开发)
- 依赖：Story 4.1, Epic 6

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent during implementation_

### Completion Notes List

_To be filled by dev agent:_
- New patterns/services created
- Architectural decisions made
- Technical debt items
- Warnings for next story
- Interfaces/methods for reuse

### File List

_To be filled by dev agent:_
- **NEW**: Files created
- **MODIFIED**: Files changed
- **DELETED**: Files removed

---

## Change Log

- **2025-11-24**: Story 初始创建，状态设为 drafted
