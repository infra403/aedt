# Story 4.7: 手动冲突解决工作流

Status: drafted

## Story

作为用户，
我希望手动解决冲突并恢复合并，
以便我对复杂的合并有完全的控制。

## Acceptance Criteria

1. **AC1: 查看冲突详情**
   - 当 Epic 2 与 Epic 3 有冲突时
   - 我运行 `aedt conflicts epic-2`
   - CLI 显示：
     - 冲突文件：src/parser.py
     - 冲突 Epic：Epic 3 (developing)
     - 建议操作："Pause Epic 3, merge Epic 2, then resume Epic 3"

2. **AC2: 强制合并并手动解决**
   - 当我手动解决冲突后
   - 我运行 `aedt merge epic-2 --force`
   - 合并尽管有冲突仍继续进行
   - 我被提示手动处理合并冲突

## Tasks / Subtasks

- [ ] **任务 1：实现冲突详情查看命令** (AC: 1)
  - [ ] 1.1 添加 CLI 命令 `aedt conflicts <epic-id>`
  - [ ] 1.2 从 Epic 状态读取 `conflict_details`
  - [ ] 1.3 格式化输出冲突文件和冲突 Epic
  - [ ] 1.4 提供解决建议

- [ ] **任务 2：生成智能解决建议** (AC: 1)
  - [ ] 2.1 分析冲突 Epic 的状态（developing, completed等）
  - [ ] 2.2 建议优先合并完成的 Epic
  - [ ] 2.3 建议暂停进行中的 Epic 以解决冲突

- [ ] **任务 3：实现强制合并选项** (AC: 2)
  - [ ] 3.1 在 `aedt merge` 命令添加 `--force` 标志
  - [ ] 3.2 跳过冲突检测，直接尝试 Git 合并
  - [ ] 3.3 捕获 Git 合并冲突，进入手动解决模式

- [ ] **任务 4：手动冲突解决指导** (AC: 2)
  - [ ] 4.1 Git 进入冲突状态时，显示指导信息
  - [ ] 4.2 提示："Resolve conflicts in the following files: <list>"
  - [ ] 4.3 提示："After resolving, run: git commit"
  - [ ] 4.4 提示："Then AEDT will detect the merge completion"

- [ ] **任务 5：检测合并完成** (AC: 2)
  - [ ] 5.1 使用 `git status` 检查工作区是否干净
  - [ ] 5.2 如果干净且最新提交是合并提交，标记完成
  - [ ] 5.3 更新 Epic 状态为 "merged"

- [ ] **任务 6：单元和集成测试** (AC: 1, 2)
  - [ ] 6.1 测试冲突详情查看命令
  - [ ] 6.2 测试强制合并选项
  - [ ] 6.3 测试手动解决冲突场景
  - [ ] 6.4 集成测试完整手动解决工作流

## Dev Notes

### 架构约束和模式

**模块定位：**
- 主要涉及 `CLI` 模块（新命令）
- 涉及 `WorktreeManager`（强制合并）
- 涉及 `StateManager`（读取冲突详情）

**技术实现要点：**

1. **冲突详情查看命令**
   ```python
   @click.command()
   @click.argument('epic_id')
   def conflicts(epic_id: str):
       """显示 Epic 的冲突详情"""
       epic = state_manager.get_epic(epic_id)

       if not epic.conflict_details:
           click.echo(f"Epic {epic_id} has no conflicts")
           return

       # 格式化输出
       click.echo(f"\nConflicts for Epic {epic_id}:")
       click.echo(f"  Conflicting files:")
       for file in epic.conflict_details['files']:
           click.echo(f"    - {file}")

       click.echo(f"\n  Conflicting Epics:")
       for conflicting_epic_id in epic.conflict_details['conflicting_epics']:
           conflicting_epic = state_manager.get_epic(conflicting_epic_id)
           click.echo(f"    - Epic {conflicting_epic_id}: {conflicting_epic.title} ({conflicting_epic.status})")

       # 智能建议
       suggestion = _generate_resolution_suggestion(epic, epic.conflict_details)
       click.echo(f"\n  Suggested action: {suggestion}")
   ```

2. **智能解决建议生成**
   ```python
   def _generate_resolution_suggestion(epic, conflict_details):
       """生成冲突解决建议"""
       conflicting_epics = [
           state_manager.get_epic(id)
           for id in conflict_details['conflicting_epics']
       ]

       # 如果所有冲突 Epic 都完成了，当前 Epic 可直接合并
       if all(e.status == "completed" for e in conflicting_epics):
           return "All conflicting epics are completed. Merge them first."

       # 如果有进行中的 Epic，建议暂停
       developing = [e for e in conflicting_epics if e.status == "developing"]
       if developing:
           epic_list = ", ".join([f"Epic {e.id}" for e in developing])
           return f"Pause {epic_list}, merge Epic {epic.id}, then resume."

       return "Manually resolve conflicts in the conflicting files."
   ```

3. **强制合并实现**
   ```python
   @click.command()
   @click.argument('epic_id')
   @click.option('--force', is_flag=True, help='Force merge despite conflicts')
   def merge(epic_id: str, force: bool):
       """合并 Epic 到主分支"""
       epic = state_manager.get_epic(epic_id)

       if not force:
           # 正常合并流程（Story 4.6）
           conflicts = worktree_manager.detect_conflicts([epic_id])
           if conflicts:
               click.echo(f"Conflicts detected. Use --force to merge anyway.")
               return

       # 强制合并
       try:
           repo = Repo(worktree_manager.repo_path)
           repo.git.checkout('main')
           repo.git.merge(f'epic-{epic_id}')
           click.echo(f"Epic {epic_id} merged successfully")
           state_manager.update_epic_status(epic_id, "merged")

       except GitCommandError as e:
           # Git 合并冲突
           click.echo(f"\nMerge conflicts occurred:")
           click.echo(f"  {e}")
           click.echo(f"\nResolve conflicts in the following files:")
           # 列出冲突文件
           conflict_files = repo.git.diff('--name-only', '--diff-filter=U').split('\n')
           for file in conflict_files:
               click.echo(f"  - {file}")
           click.echo(f"\nAfter resolving:")
           click.echo(f"  1. git add <resolved-files>")
           click.echo(f"  2. git commit")
           click.echo(f"  3. AEDT will detect completion automatically")
   ```

4. **合并完成检测**
   ```python
   def detect_merge_completion(self, epic_id: str) -> bool:
       """检测手动合并是否完成"""
       repo = Repo(self.repo_path)

       # 检查工作区是否干净
       if repo.is_dirty():
           return False

       # 检查最新提交是否是合并提交
       latest_commit = repo.head.commit
       if len(latest_commit.parents) > 1:  # 合并提交有多个父提交
           logger.info(f"Merge detected for Epic {epic_id}")
           return True

       return False
   ```

5. **依赖关系**
   - **前置条件：** Story 4.6 (冲突检测和暂停)
   - **后续：** Story 4.8 (合并后清理)

### 从前一个 Story 的学习

**从 Story 4.6 获得的上下文：**
- `conflict_details` 字段已添加到 Epic 状态
- `awaiting_merge` 和 `ready_to_merge` 状态已定义
- 冲突检测已集成到合并流程

**复用接口：**
- 读取 `epic.conflict_details` 获取冲突信息
- 使用现有的 `merge_to_main()` 逻辑
- 扩展 CLI 命令集

**从 Story 4.4-4.5 获得的上下文：**
- Git 操作异常处理模式已建立
- 冲突检测算法已实现

### 项目结构对齐

**预期文件：**
```
aedt/
├── cli/
│   └── commands.py             # 新增：conflicts 和 merge --force 命令
├── infrastructure/
│   └── worktree_manager.py     # 新增：detect_merge_completion()
└── tests/
    └── test_manual_resolution.py  # 新增测试
```

**CLI 命令扩展：**
```python
@click.group()
def cli():
    pass

cli.add_command(conflicts)  # 新增
cli.add_command(merge)      # 扩展 --force 选项
```

### 测试策略

**单元测试覆盖：**
- 冲突详情命令输出格式
- 智能建议生成逻辑
- 强制合并选项
- 合并完成检测

**集成测试场景：**
- 完整手动解决工作流：
  1. 创建冲突
  2. 查看冲突详情
  3. 强制合并
  4. 手动解决冲突
  5. 提交并检测完成

**测试用例：**
```python
def test_manual_conflict_resolution():
    """测试完整手动冲突解决流程"""
    # 1. 创建两个 Epic 修改相同文件
    # 2. Epic 1 完成，尝试合并但检测到冲突
    # 3. 运行 aedt conflicts epic-1
    # 4. 运行 aedt merge epic-1 --force
    # 5. 手动解决冲突并提交
    # 6. 验证 Epic 状态更新为 "merged"
```

### References

- [Source: docs/epics.md#Epic-4-Story-4.7]
- [Source: docs/architecture.md#3.5-Git-Worktree-管理模块]
- [Source: stories/4-6-pause-merge-on-conflict-detection.md] (前一个 story)
- FR Coverage: FR33 (手动冲突解决), FR34 (冲突详情查看)
- 依赖：Story 4.6

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
