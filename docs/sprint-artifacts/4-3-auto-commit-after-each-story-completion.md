# Story 4.3: 每个 Story 完成后自动提交

Status: drafted

## Story

作为用户，
我希望每个 Story 被单独提交，
以便 Git 历史是细粒度的，冲突最小化。

## Acceptance Criteria

1. **AC1: Story 完成时自动提交**
   - 当 Epic 2 有 3 个 Stories 时
   - Subagent 完成 Story 2.1
   - 生成 Git 提交，消息为："Story 2.1: Initialize CLI"
   - 提交记录在 "epic-2" 分支上

2. **AC2: Epic 完成时所有 Story 都有对应提交**
   - 当 Subagent 完成所有 3 个 Stories 时
   - Epic 完成
   - "epic-2" 分支上有 3 个提交
   - 每个提交对应一个 Story

## Tasks / Subtasks

- [ ] **任务 1：在 Subagent Prompt 中添加提交指令** (AC: 1)
  - [ ] 1.1 更新 Subagent prompt 模板，包含提交命令
  - [ ] 1.2 指示格式：`git add . && git commit -m 'Story X: <title>'`
  - [ ] 1.3 明确每个 Story 完成后必须提交

- [ ] **任务 2：监控 Subagent 输出检测 Story 完成** (AC: 1)
  - [ ] 2.1 在 `SubagentOrchestrator` 中实现输出解析
  - [ ] 2.2 检测关键字："Story X completed" 或类似标记
  - [ ] 2.3 触发提交验证流程

- [ ] **任务 3：验证提交是否成功创建** (AC: 1, 2)
  - [ ] 3.1 使用 `git log` 检查最新提交
  - [ ] 3.2 验证提交消息格式匹配 "Story X: <title>"
  - [ ] 3.3 确认提交在正确的分支上

- [ ] **任务 4：提交缺失时的警告处理** (AC: 1)
  - [ ] 4.1 如果 Story 完成但无提交，记录警告
  - [ ] 4.2 日志消息："Story X completed but no commit detected"
  - [ ] 4.3 可选：通知用户手动检查

- [ ] **任务 5：跟踪 Epic 提交历史** (AC: 2)
  - [ ] 5.1 在 Epic 状态中记录每个 Story 的 commit_hash
  - [ ] 5.2 Epic 完成时验证所有 Story 都有提交
  - [ ] 5.3 生成提交摘要报告

- [ ] **任务 6：单元和集成测试** (AC: 1, 2)
  - [ ] 6.1 测试 Story 完成触发提交检测
  - [ ] 6.2 测试提交验证逻辑
  - [ ] 6.3 测试缺失提交警告
  - [ ] 6.4 集成测试：完整 Epic 的提交历史

## Dev Notes

### 架构约束和模式

**模块定位：**
- 主要涉及 `SubagentOrchestrator` 模块
- 与 `WorktreeManager` 协作验证提交
- 与 `StateManager` 协作记录提交哈希

**技术实现要点：**

1. **Subagent Prompt 模板扩展**
   ```python
   prompt = f"""
   After completing each Story, you MUST commit your changes:
   1. Run: git add .
   2. Run: git commit -m "Story {story.id}: {story.title}"
   3. Report: "Story {story.id} completed"

   This ensures granular Git history and minimizes merge conflicts.
   """
   ```

2. **输出监控和解析**
   ```python
   def monitor_subagent_output(self, agent_id: str):
       """监控 Subagent 输出，检测 Story 完成事件"""
       # 解析输出寻找 "Story X.Y completed"
       # 触发 verify_story_commit()
   ```

3. **提交验证逻辑**
   ```python
   def verify_story_commit(self, epic: Epic, story: Story) -> bool:
       """验证 Story 提交是否存在"""
       repo = Repo(epic.worktree_path)
       latest_commit = repo.head.commit
       expected_message = f"Story {story.id}: {story.title}"

       if expected_message in latest_commit.message:
           # 记录 commit_hash 到 Story 状态
           story.commit_hash = latest_commit.hexsha
           return True
       else:
           logger.warning(f"Story {story.id} completed but no commit detected")
           return False
   ```

4. **提交历史跟踪**
   - 在 Story 数据模型中添加 `commit_hash` 字段
   - Epic 完成时生成提交摘要
   - 支持后续的合并和回滚操作

5. **依赖关系**
   - **前置条件：** Story 4.2 (Subagent 必须在 Worktree 中工作)
   - **前置条件：** Epic 6 (Subagent 必须能报告完成状态)
   - **后续：** Story 4.5 (自动合并到主分支)

### 从前一个 Story 的学习

**从 Story 4.2 获得的上下文：**
- Subagent 工作目录已设置为 Worktree 路径
- Git 操作在隔离的 Worktree 中执行
- `SubagentOrchestrator` 已扩展支持 `worktree_path`

**复用模式：**
- 继续使用 `GitPython` 的 `Repo(worktree_path)` 模式
- 扩展 Subagent prompt 构建逻辑
- 利用现有的输出监控机制

**从 Story 4.1 获得的上下文：**
- Worktree 和分支管理由 `WorktreeManager` 处理
- Epic 状态持久化到 `.aedt/projects/<project>/status.yaml`

### 项目结构对齐

**预期修改文件：**
```
aedt/
├── application/
│   └── subagent_orchestrator.py   # 修改：添加输出监控和提交验证
├── models/
│   └── story.py                    # 修改：添加 commit_hash 字段
├── infrastructure/
│   └── worktree_manager.py         # 使用：验证提交
└── tests/
    └── test_story_commits.py       # 新增测试
```

**数据模型扩展：**
```python
@dataclass
class Story:
    id: str
    title: str
    description: str
    status: str
    commit_hash: Optional[str] = None  # 新增字段
    prerequisites: List[str] = field(default_factory=list)
```

### 测试策略

**单元测试覆盖：**
- Story 完成检测逻辑
- 提交验证成功和失败场景
- 缺失提交警告记录

**集成测试场景：**
- 完整 Epic 开发流程，验证每个 Story 提交
- 验证 Epic 完成时所有提交都存在
- 验证提交消息格式正确

### References

- [Source: docs/epics.md#Epic-4-Story-4.3]
- [Source: docs/architecture.md#3.4-Subagent-编排模块]
- [Source: stories/4-1-create-git-worktree-for-epic.md] (Worktree 管理)
- [Source: stories/4-2-subagent-development-in-isolated-worktree.md] (前一个 story)
- FR Coverage: FR29 (Story-level 提交)
- 依赖：Story 4.2, Epic 6

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
