# Story 4.6: 检测到冲突时暂停合并

Status: drafted

## Story

作为用户，
我希望 AEDT 在检测到冲突时停止合并过程，
以便我可以手动解决它们。

## Acceptance Criteria

1. **AC1: 检测冲突时暂停合并**
   - 当 Epic 2 准备合并但有冲突时
   - AEDT 检测到冲突
   - 合并不被尝试
   - Epic 状态设置为 "awaiting_merge"
   - TUI 通知显示："Epic 2 has conflicts with Epic 3 (src/parser.py). Resolve manually."

2. **AC2: 手动解决后继续合并**
   - 当我手动解决冲突后
   - 我将 Epic 标记为 "ready_to_merge"
   - 我运行 `aedt merge epic-2`
   - 合并继续进行

## Tasks / Subtasks

- [ ] **任务 1：在合并前集成冲突检测** (AC: 1)
  - [ ] 1.1 在 `merge_to_main()` 前调用 `detect_conflicts([epic_id])`
  - [ ] 1.2 如果检测到冲突，跳过合并步骤
  - [ ] 1.3 设置 Epic 状态为 "awaiting_merge"

- [ ] **任务 2：存储冲突详情到 Epic 状态** (AC: 1)
  - [ ] 2.1 扩展 Epic 状态数据结构添加 `conflict_details` 字段
  - [ ] 2.2 存储：`{conflicting_epics: [epic_ids], files: [filenames]}`
  - [ ] 2.3 持久化到状态文件

- [ ] **任务 3：TUI 显示冲突通知** (AC: 1)
  - [ ] 3.1 在 Epic 面板显示冲突状态
  - [ ] 3.2 格式化消息："Epic X has conflicts with Epic Y (file1, file2)"
  - [ ] 3.3 提供解决建议

- [ ] **任务 4：实现手动合并触发** (AC: 2)
  - [ ] 4.1 添加 CLI 命令 `aedt merge <epic-id>`
  - [ ] 4.2 验证 Epic 状态为 "awaiting_merge" 或 "ready_to_merge"
  - [ ] 4.3 重新运行冲突检测
  - [ ] 4.4 如果无冲突，执行合并

- [ ] **任务 5：支持 "ready_to_merge" 状态标记** (AC: 2)
  - [ ] 5.1 允许用户手动标记 Epic 为 "ready_to_merge"
  - [ ] 5.2 验证冲突已解决（可选验证）
  - [ ] 5.3 触发合并流程

- [ ] **任务 6：单元和集成测试** (AC: 1, 2)
  - [ ] 6.1 测试检测冲突时暂停合并
  - [ ] 6.2 测试手动触发合并命令
  - [ ] 6.3 测试 TUI 冲突通知显示
  - [ ] 6.4 集成测试完整冲突解决工作流

## Dev Notes

### 架构约束和模式

**模块定位：**
- 涉及 `WorktreeManager`（冲突检测）
- 涉及 `Scheduler`（合并流程控制）
- 涉及 `TUIApp`（冲突通知显示）
- 涉及 `CLI`（手动合并命令）

**技术实现要点：**

1. **合并前冲突检测集成**
   ```python
   def merge_to_main(self, epic_id: str) -> bool:
       """自动合并，带冲突检测"""
       # 1. 检测冲突
       conflicts = self.detect_conflicts([epic_id])
       if conflicts:
           # 暂停合并
           logger.warning(f"Epic {epic_id} has conflicts, merge paused")
           self._store_conflict_details(epic_id, conflicts)
           state_manager.update_epic_status(epic_id, "awaiting_merge")
           return False

       # 2. 继续合并流程（如 Story 4.5）
       # ...
   ```

2. **冲突详情数据结构**
   ```python
   @dataclass
   class EpicState:
       id: str
       status: str
       worktree_path: Optional[str]
       conflict_details: Optional[Dict] = None  # 新增字段

   # 冲突详情格式
   conflict_details = {
       "conflicting_epics": ["3", "5"],
       "files": ["src/parser.py", "src/config.py"],
       "detected_at": "2025-11-24T10:30:00"
   }
   ```

3. **TUI 冲突通知**
   ```python
   def render_epic_panel(self, epic: Epic):
       """渲染 Epic 面板，显示冲突信息"""
       if epic.status == "awaiting_merge":
           conflict_msg = self._format_conflict_message(
               epic.conflict_details
           )
           self.panel.add_notification(conflict_msg, level="warning")
   ```

4. **手动合并 CLI 命令**
   ```python
   @click.command()
   @click.argument('epic_id')
   def merge(epic_id: str):
       """手动触发 Epic 合并"""
       epic = state_manager.get_epic(epic_id)

       if epic.status not in ["awaiting_merge", "ready_to_merge"]:
           click.echo(f"Epic {epic_id} is not ready to merge (status: {epic.status})")
           return

       # 重新检测冲突
       conflicts = worktree_manager.detect_conflicts([epic_id])
       if conflicts:
           click.echo(f"Conflicts still exist: {conflicts}")
           click.echo("Resolve conflicts first or use --force flag")
           return

       # 执行合并
       if worktree_manager.merge_to_main(epic_id):
           click.echo(f"Epic {epic_id} merged successfully")
   ```

5. **状态流转**
   ```
   completed → (冲突检测) → awaiting_merge
   awaiting_merge → (用户解决冲突) → ready_to_merge
   ready_to_merge → (手动触发) → merged
   ```

6. **依赖关系**
   - **前置条件：** Story 4.4 (冲突检测)
   - **前置条件：** Story 4.5 (合并逻辑)
   - **后续：** Story 4.7 (手动解决工作流)

### 从前一个 Story 的学习

**从 Story 4.5 获得的上下文：**
- `merge_to_main()` 方法已实现
- Git 合并异常处理已建立
- Epic 状态更新机制已存在

**复用模式：**
- 在现有 `merge_to_main()` 中集成冲突检测
- 使用现有状态管理 API
- 扩展 Epic 状态数据模型

**从 Story 4.4 获得的上下文：**
- `detect_conflicts()` 返回 `Dict[filename, List[epic_id]]`
- 冲突检测已充分测试

### 项目结构对齐

**预期修改文件：**
```
aedt/
├── infrastructure/
│   └── worktree_manager.py    # 修改：合并前检测冲突
├── application/
│   └── scheduler.py            # 修改：处理 awaiting_merge 状态
├── models/
│   └── epic.py                 # 修改：添加 conflict_details 字段
├── ui/
│   └── tui_app.py              # 修改：显示冲突通知
├── cli/
│   └── commands.py             # 新增：merge 命令
└── tests/
    └── test_conflict_pause.py  # 新增测试
```

**Epic 状态枚举扩展：**
```python
EPIC_STATUS_AWAITING_MERGE = "awaiting_merge"
EPIC_STATUS_READY_TO_MERGE = "ready_to_merge"
```

### 测试策略

**单元测试覆盖：**
- 冲突检测触发暂停合并
- 冲突详情正确存储
- 手动合并命令验证状态
- TUI 通知正确显示

**集成测试场景：**
- 完整冲突检测和暂停流程
- 用户手动解决冲突后继续合并
- 多个 Epic 并行冲突场景

### References

- [Source: docs/epics.md#Epic-4-Story-4.6]
- [Source: docs/architecture.md#3.5-Git-Worktree-管理模块]
- [Source: stories/4-4-detect-file-conflicts-across-parallel-epics.md] (冲突检测)
- [Source: stories/4-5-automatic-merge-to-main-branch-no-conflicts.md] (前一个 story)
- FR Coverage: FR32 (冲突暂停合并)
- 依赖：Story 4.4, Story 4.5

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
