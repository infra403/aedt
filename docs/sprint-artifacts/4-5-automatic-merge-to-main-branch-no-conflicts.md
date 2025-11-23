# Story 4.5: 自动合并到主分支（无冲突）

Status: drafted

## Story

作为用户，
我希望 AEDT 自动将完成的 Epic 合并到主分支，
以便我不必手动处理合并。

## Acceptance Criteria

1. **AC1: 无冲突自动合并**
   - 当 Epic 2 完成且所有质量检查通过时
   - 没有其他 Epic 修改相同的文件
   - AEDT 运行合并流程
   - "epic-2" 分支被合并到 "main"
   - 合并提交消息为："Merge Epic 2: <title>"
   - Epic 状态更新为 "merged"

2. **AC2: 有冲突时中止合并**
   - 当 Epic 2 与另一个开发中的 Epic 有文件冲突时
   - AEDT 尝试合并
   - 合并被中止
   - Epic 状态设置为 "awaiting_merge"
   - 用户收到通知："Epic 2 has conflicts. Resolve manually."

## Tasks / Subtasks

- [ ] **任务 1：实现自动合并流程** (AC: 1)
  - [ ] 1.1 在 `WorktreeManager` 中添加 `merge_to_main(epic_id, main_branch="main")` 方法
  - [ ] 1.2 检出主分支：`repo.git.checkout('main')`
  - [ ] 1.3 执行合并：`repo.git.merge(f'epic-{epic_id}')`
  - [ ] 1.4 生成合并提交消息

- [ ] **任务 2：集成冲突检测** (AC: 2)
  - [ ] 2.1 合并前调用 `detect_conflicts([epic_id, ...])`
  - [ ] 2.2 如果有冲突，返回 False 并记录
  - [ ] 2.3 设置 Epic 状态为 "awaiting_merge"

- [ ] **任务 3：集成质量门控** (AC: 1)
  - [ ] 3.1 合并前运行质量检查（Epic 7）
  - [ ] 3.2 如果质量检查失败，中止合并
  - [ ] 3.3 记录失败原因到 Epic 状态

- [ ] **任务 4：处理合并失败场景** (AC: 2)
  - [ ] 4.1 捕获 Git 合并冲突异常
  - [ ] 4.2 执行 `repo.git.merge('--abort')` 回滚
  - [ ] 4.3 通知用户需要手动解决
  - [ ] 4.4 记录详细错误日志

- [ ] **任务 5：更新 Epic 状态** (AC: 1)
  - [ ] 5.1 合并成功后更新状态为 "merged"
  - [ ] 5.2 记录合并时间和提交哈希
  - [ ] 5.3 触发 Worktree 清理（Story 4.8）

- [ ] **任务 6：单元和集成测试** (AC: 1, 2)
  - [ ] 6.1 测试无冲突自动合并
  - [ ] 6.2 测试有冲突中止合并
  - [ ] 6.3 测试质量检查失败场景
  - [ ] 6.4 集成测试完整合并工作流

## Dev Notes

### 架构约束和模式

**模块定位：**
- 属于**基础设施层 (Infrastructure Layer)**
- 扩展 `WorktreeManager` 的合并能力
- 与 `Scheduler` 和 `QualityGate` 协作

**技术实现要点：**

1. **自动合并流程**
   ```python
   def merge_to_main(
       self,
       epic_id: str,
       main_branch: str = "main"
   ) -> bool:
       """自动合并 Epic 分支到主分支

       Returns:
           bool: 合并是否成功
       """
       try:
           # 1. 检测冲突
           conflicts = self.detect_conflicts([epic_id])
           if conflicts:
               logger.warning(f"Epic {epic_id} has conflicts: {conflicts}")
               return False

           # 2. 检出主分支
           repo = Repo(self.repo_path)
           repo.git.checkout(main_branch)

           # 3. 合并 Epic 分支
           epic_branch = f"epic-{epic_id}"
           repo.git.merge(epic_branch, '-m', f"Merge Epic {epic_id}: {epic.title}")

           logger.info(f"Epic {epic_id} merged successfully")
           return True

       except GitCommandError as e:
           # 合并冲突
           logger.error(f"Merge failed for Epic {epic_id}: {e}")
           repo.git.merge('--abort')
           return False
   ```

2. **与 Scheduler 集成**
   ```python
   def on_epic_completed(self, epic_id: str):
       """Epic 完成回调"""
       # 1. 运行质量门控
       if not quality_gate.run_epic_checks(epic_id):
           logger.error(f"Quality checks failed for Epic {epic_id}")
           return

       # 2. 自动合并
       if worktree_manager.merge_to_main(epic_id):
           # 3. 更新状态为 "merged"
           state_manager.update_epic_status(epic_id, "merged")
           # 4. 清理 Worktree
           worktree_manager.cleanup_worktree(epic_id)
       else:
           # 设置为等待合并
           state_manager.update_epic_status(epic_id, "awaiting_merge")
   ```

3. **错误处理和回滚**
   - 捕获 `GitCommandError` 异常
   - 自动执行 `git merge --abort` 恢复状态
   - 保留 Epic 分支，允许手动解决
   - 记录详细日志供调试

4. **状态机转换**
   ```
   completed → (质量检查) → (冲突检测) → merged
                ↓ 失败                       ↓ 失败
                failed                      awaiting_merge
   ```

5. **依赖关系**
   - **前置条件：** Story 4.4 (冲突检测必须存在)
   - **前置条件：** Epic 7 (质量检查必须存在)
   - **后续：** Story 4.8 (Worktree 清理)

### 从前一个 Story 的学习

**从 Story 4.4 获得的上下文：**
- `detect_conflicts()` 方法已实现
- 冲突报告格式：`Dict[filename, List[epic_id]]`
- GitPython 用于所有 Git 操作

**复用接口：**
- 调用 `WorktreeManager.detect_conflicts()` 检查冲突
- 继续使用 GitPython 的异常处理模式

**从 Story 4.1-4.3 获得的上下文：**
- Epic 状态持久化机制已建立
- 日志记录模式已确定
- Worktree 和分支管理已成熟

### 项目结构对齐

**预期修改文件：**
```
aedt/
├── infrastructure/
│   └── worktree_manager.py    # 修改：添加 merge_to_main() 方法
├── application/
│   └── scheduler.py            # 修改：集成自动合并到 Epic 完成流程
├── models/
│   └── epic.py                 # 可能修改：添加 "merged" 和 "awaiting_merge" 状态
└── tests/
    └── test_auto_merge.py      # 新增测试
```

**Epic 状态扩展：**
```python
# 新增状态
EPIC_STATUS_MERGED = "merged"
EPIC_STATUS_AWAITING_MERGE = "awaiting_merge"
```

### 测试策略

**单元测试覆盖：**
- 无冲突成功合并
- 有冲突中止合并
- Git 合并失败异常处理
- 质量检查失败场景

**集成测试场景：**
- 完整 Epic 开发流程：创建 → 开发 → 质量检查 → 合并
- 并行 Epic 冲突检测和合并暂停
- 合并后 Worktree 清理

**测试用例：**
```python
def test_merge_success_no_conflicts():
    """测试无冲突成功合并"""
    # 创建 Epic 分支并提交更改
    # 运行合并
    # 验证主分支包含更改
    # 验证 Epic 状态为 "merged"

def test_merge_abort_on_conflict():
    """测试有冲突时中止合并"""
    # 创建两个 Epic 修改相同文件
    # 尝试合并第一个 Epic
    # 验证合并被中止
    # 验证状态为 "awaiting_merge"
```

### References

- [Source: docs/epics.md#Epic-4-Story-4.5]
- [Source: docs/architecture.md#3.5-Git-Worktree-管理模块]
- [Source: stories/4-4-detect-file-conflicts-across-parallel-epics.md] (前一个 story)
- FR Coverage: FR30 (自动合并)
- NFR Coverage: NFR10 (Git 操作容错)
- 依赖：Story 4.4, Epic 7

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
