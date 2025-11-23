# Story 4.8: 合并后清理 Worktree

Status: drafted

## Story

作为用户，
我希望 AEDT 在成功合并后自动清理 Worktree，
以便释放磁盘空间并保持工作区整洁。

## Acceptance Criteria

1. **AC1: 合并后自动清理**
   - 当 Epic 2 成功合并到 main 时
   - 合并完成
   - `.aedt/worktrees/epic-2/` 的 Worktree 被移除
   - "epic-2" 分支被删除
   - Epic 状态更新：`worktree_path=null`, `status="completed"`

2. **AC2: 手动清理所有 Worktree**
   - 当我想手动清理所有 Worktree 时
   - 我运行 `aedt clean`
   - 所有 `.aedt/worktrees/` 中的 Worktree 被移除
   - 所有 Epic 分支被删除
   - CLI 提示确认："Remove all Worktrees? [y/N]"

## Tasks / Subtasks

- [ ] **任务 1：实现 Worktree 清理方法** (AC: 1)
  - [ ] 1.1 在 `WorktreeManager` 中添加 `cleanup_worktree(epic_id)` 方法
  - [ ] 1.2 使用 GitPython 移除 Worktree：`repo.git.worktree('remove', path)`
  - [ ] 1.3 删除分支：`repo.git.branch('-D', branch_name)`
  - [ ] 1.4 处理 Worktree 不存在的情况

- [ ] **任务 2：集成到合并成功流程** (AC: 1)
  - [ ] 2.1 在 `Scheduler.on_epic_completed()` 中，合并成功后调用清理
  - [ ] 2.2 检查配置 `config.git.auto_cleanup` 是否启用
  - [ ] 2.3 如果启用，自动清理；否则跳过

- [ ] **任务 3：更新 Epic 状态** (AC: 1)
  - [ ] 3.1 清理后设置 `epic.worktree_path = null`
  - [ ] 3.2 设置 `epic.status = "completed"`
  - [ ] 3.3 持久化状态到文件

- [ ] **任务 4：实现手动清理命令** (AC: 2)
  - [ ] 4.1 添加 CLI 命令 `aedt clean`
  - [ ] 4.2 列出所有现有 Worktree
  - [ ] 4.3 提示用户确认：`click.confirm("Remove all Worktrees? [y/N]")`
  - [ ] 4.4 清理所有 Worktree 和分支

- [ ] **任务 5：错误处理** (AC: 1, 2)
  - [ ] 5.1 处理 Worktree 已被手动删除的情况
  - [ ] 5.2 处理分支删除失败（如分支不存在）
  - [ ] 5.3 记录清理操作到日志
  - [ ] 5.4 部分清理失败时继续处理其他 Worktree

- [ ] **任务 6：单元和集成测试** (AC: 1, 2)
  - [ ] 6.1 测试单个 Worktree 清理
  - [ ] 6.2 测试批量清理所有 Worktree
  - [ ] 6.3 测试自动清理配置开关
  - [ ] 6.4 测试 Worktree 不存在时的错误处理

## Dev Notes

### 架构约束和模式

**模块定位：**
- 属于**基础设施层 (Infrastructure Layer)**
- 扩展 `WorktreeManager` 功能
- 与 `Scheduler` 和 `CLI` 集成

**技术实现要点：**

1. **Worktree 清理实现**
   ```python
   def cleanup_worktree(self, epic_id: str) -> bool:
       """清理 Epic 的 Worktree 和分支

       Returns:
           bool: 清理是否成功
       """
       try:
           epic = state_manager.get_epic(epic_id)
           repo = Repo(self.repo_path)

           # 1. 移除 Worktree
           if epic.worktree_path and os.path.exists(epic.worktree_path):
               repo.git.worktree('remove', epic.worktree_path)
               logger.info(f"Worktree removed: {epic.worktree_path}")
           else:
               logger.warning(f"Worktree not found: {epic.worktree_path}")

           # 2. 删除分支
           branch_name = f"epic-{epic_id}"
           try:
               repo.git.branch('-D', branch_name)
               logger.info(f"Branch deleted: {branch_name}")
           except GitCommandError:
               logger.warning(f"Branch not found: {branch_name}")

           # 3. 更新状态
           epic.worktree_path = None
           epic.status = "completed"
           state_manager.save_epic_state(epic)

           return True

       except Exception as e:
           logger.error(f"Cleanup failed for Epic {epic_id}: {e}")
           return False
   ```

2. **集成到 Scheduler**
   ```python
   def on_epic_completed(self, epic_id: str):
       """Epic 完成回调"""
       # 1. 运行质量检查
       if not quality_gate.run_epic_checks(epic_id):
           return

       # 2. 自动合并
       if not worktree_manager.merge_to_main(epic_id):
           return

       # 3. 自动清理（如果配置启用）
       if config.git.auto_cleanup:
           worktree_manager.cleanup_worktree(epic_id)
           logger.info(f"Epic {epic_id} cleanup completed")
   ```

3. **手动清理命令**
   ```python
   @click.command()
   def clean():
       """清理所有 Worktree 和分支"""
       # 列出所有 Worktree
       worktrees = worktree_manager.list_all_worktrees()

       if not worktrees:
           click.echo("No worktrees to clean")
           return

       click.echo(f"Found {len(worktrees)} worktrees:")
       for wt in worktrees:
           click.echo(f"  - Epic {wt.epic_id}: {wt.path}")

       # 确认
       if not click.confirm("Remove all worktrees?", default=False):
           click.echo("Cleanup cancelled")
           return

       # 清理所有
       success_count = 0
       for wt in worktrees:
           if worktree_manager.cleanup_worktree(wt.epic_id):
               success_count += 1

       click.echo(f"\nCleaned up {success_count}/{len(worktrees)} worktrees")
   ```

4. **配置项**
   ```yaml
   # .aedt/config.yaml
   git:
     worktree_base: ".aedt/worktrees"
     branch_prefix: "epic"
     auto_cleanup: true  # 新增：自动清理开关
   ```

5. **依赖关系**
   - **前置条件：** Story 4.5 (合并必须成功)
   - **集成：** Epic 完成流程的最后一步

### 从前一个 Story 的学习

**从 Story 4.1-4.7 获得的上下文：**
- Worktree 创建和管理模式已建立
- Git 操作错误处理已成熟
- Epic 状态更新机制已完善
- `WorktreeManager` 已有多个相关方法

**复用模式：**
- 继续使用 GitPython 执行 Git 命令
- 遵循现有的错误处理模式
- 使用现有的日志记录系统

**架构一致性：**
- Worktree 生命周期完整：创建 (4.1) → 使用 (4.2-4.3) → 合并 (4.5) → 清理 (4.8)

### 项目结构对齐

**预期修改文件：**
```
aedt/
├── infrastructure/
│   └── worktree_manager.py    # 修改：添加 cleanup_worktree() 和 list_all_worktrees()
├── application/
│   └── scheduler.py            # 修改：集成自动清理到 Epic 完成流程
├── cli/
│   └── commands.py             # 新增：clean 命令
├── config/
│   └── config_schema.yaml      # 修改：添加 auto_cleanup 配置
└── tests/
    └── test_worktree_cleanup.py  # 新增测试
```

**接口设计：**
```python
class WorktreeManager:
    def cleanup_worktree(self, epic_id: str) -> bool:
        """清理单个 Worktree"""
        pass

    def list_all_worktrees(self) -> List[Worktree]:
        """列出所有 Worktree"""
        pass

    def cleanup_all_worktrees(self) -> Tuple[int, int]:
        """清理所有 Worktree，返回 (成功数, 总数)"""
        pass
```

### 测试策略

**单元测试覆盖：**
- 单个 Worktree 清理成功
- Worktree 不存在时的处理
- 分支不存在时的处理
- Epic 状态正确更新

**集成测试场景：**
- 完整 Epic 生命周期：创建 → 开发 → 合并 → 清理
- 批量清理多个 Worktree
- 自动清理配置开关测试

**测试用例：**
```python
def test_auto_cleanup_after_merge():
    """测试合并后自动清理"""
    # 1. 创建并完成 Epic
    # 2. 合并成功
    # 3. 验证 Worktree 和分支已删除
    # 4. 验证 Epic 状态为 "completed"
    # 5. 验证 worktree_path 为 null

def test_manual_cleanup_all():
    """测试手动清理所有 Worktree"""
    # 1. 创建 3 个 Epic 的 Worktree
    # 2. 运行 aedt clean
    # 3. 验证所有 Worktree 和分支已删除
```

### References

- [Source: docs/epics.md#Epic-4-Story-4.8]
- [Source: docs/architecture.md#3.5-Git-Worktree-管理模块]
- [Source: stories/4-1-create-git-worktree-for-epic.md] (Worktree 创建)
- [Source: stories/4-5-automatic-merge-to-main-branch-no-conflicts.md] (合并逻辑)
- FR Coverage: FR27 (Worktree 清理), FR35 (批量清理)
- 依赖：Story 4.5

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
