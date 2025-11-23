# Story 4.4: 检测并行 Epic 间的文件冲突

Status: drafted

## Story

作为用户，
我希望 AEDT 检测多个 Epic 何时修改相同的文件，
以便我可以在合并前解决冲突。

## Acceptance Criteria

1. **AC1: 检测文件冲突**
   - 当 Epic 2 修改 `src/parser.py` 和 `src/config.py` 时
   - Epic 3 修改 `src/parser.py` 和 `src/utils.py`
   - AEDT 检查冲突
   - 系统报告："Conflict detected: Epic 2 and Epic 3 both modify src/parser.py"

2. **AC2: 无冲突场景**
   - 当 Epic 2 和 Epic 3 修改完全不同的文件时
   - AEDT 检查冲突
   - 不报告冲突

## Tasks / Subtasks

- [ ] **任务 1：实现冲突检测算法** (AC: 1)
  - [ ] 1.1 在 `WorktreeManager` 中添加 `detect_conflicts(epic_ids)` 方法
  - [ ] 1.2 为每个 Epic 运行 `git diff --name-only main..epic-{id}`
  - [ ] 1.3 收集每个 Epic 修改的文件列表
  - [ ] 1.4 比较文件列表，识别重叠文件

- [ ] **任务 2：构建冲突报告数据结构** (AC: 1)
  - [ ] 2.1 设计返回格式：`Dict[str, List[int]]` (文件名 → Epic ID 列表)
  - [ ] 2.2 示例：`{"src/parser.py": [2, 3], "src/config.py": [2]}`
  - [ ] 2.3 仅报告有多个 Epic 修改的文件

- [ ] **任务 3：集成到 Scheduler 工作流** (AC: 1)
  - [ ] 3.1 在合并前自动运行冲突检测
  - [ ] 3.2 支持通过 TUI 按需检测冲突
  - [ ] 3.3 在 Epic 完成时触发冲突检测

- [ ] **任务 4：生成用户友好的冲突报告** (AC: 1)
  - [ ] 4.1 格式化输出："Conflict detected: Epic X and Epic Y both modify <file>"
  - [ ] 4.2 支持多个 Epic 冲突同一文件的场景
  - [ ] 4.3 提供冲突文件的完整列表

- [ ] **任务 5：处理无冲突场景** (AC: 2)
  - [ ] 5.1 返回空字典或 None 表示无冲突
  - [ ] 5.2 记录日志："No conflicts detected between epics"

- [ ] **任务 6：单元和集成测试** (AC: 1, 2)
  - [ ] 6.1 测试单文件冲突场景
  - [ ] 6.2 测试多文件冲突场景
  - [ ] 6.3 测试无冲突场景
  - [ ] 6.4 测试 3 个以上 Epic 冲突同一文件

## Dev Notes

### 架构约束和模式

**模块定位：**
- 属于**基础设施层 (Infrastructure Layer)**
- 扩展 `WorktreeManager` 功能
- 为 `Scheduler` 提供冲突检测能力

**技术实现要点：**

1. **冲突检测算法**
   ```python
   def detect_conflicts(self, epic_ids: List[str]) -> Dict[str, List[str]]:
       """检测多个 Epic 间的文件冲突

       Returns:
           Dict[filename, List[epic_id]]: 冲突文件 → 修改它的 Epic 列表
       """
       file_to_epics = {}  # filename → list of epic_ids

       for epic_id in epic_ids:
           # 获取该 Epic 修改的文件
           repo = Repo(self.repo_path)
           modified_files = repo.git.diff(
               '--name-only',
               f'main..epic-{epic_id}'
           ).split('\n')

           # 记录每个文件被哪些 Epic 修改
           for file in modified_files:
               if file not in file_to_epics:
                   file_to_epics[file] = []
               file_to_epics[file].append(epic_id)

       # 只返回有冲突的文件（多个 Epic 修改）
       conflicts = {
           file: epics
           for file, epics in file_to_epics.items()
           if len(epics) > 1
       }

       return conflicts
   ```

2. **冲突报告格式化**
   ```python
   def format_conflict_report(self, conflicts: Dict[str, List[str]]) -> str:
       """生成用户友好的冲突报告"""
       if not conflicts:
           return "No conflicts detected"

       report = ["Conflicts detected:"]
       for file, epic_ids in conflicts.items():
           epic_list = ", ".join([f"Epic {id}" for id in epic_ids])
           report.append(f"  - {file}: modified by {epic_list}")

       return "\n".join(report)
   ```

3. **集成点**
   - **合并前检测：** Story 4.5 在自动合并前调用
   - **按需检测：** TUI 提供手动触发按钮
   - **Epic 完成时：** Scheduler 自动检查与其他进行中 Epic 的冲突

4. **性能考虑**
   - 对于大量 Epic，`git diff` 可能较慢
   - 考虑缓存修改文件列表
   - 仅在 Epic 状态变化时更新缓存

5. **依赖关系**
   - **前置条件：** Story 4.1 (Worktree 必须存在)
   - **后续：** Story 4.5 (自动合并，需要先检测冲突)
   - **关联：** Story 4.6 (合并暂停)

### 从前一个 Story 的学习

**从 Story 4.1-4.3 获得的上下文：**
- Worktree 位于 `.aedt/worktrees/epic-{id}/`
- 分支命名为 `epic-{id}`
- GitPython 已用于 Worktree 管理
- Epic 状态包含 `worktree_path` 和 `branch_name`

**复用模式：**
- 继续使用 `GitPython` 执行 Git 命令
- 使用 `WorktreeManager` 作为 Git 操作的统一接口
- 日志记录遵循现有模式

### 项目结构对齐

**预期修改文件：**
```
aedt/
├── infrastructure/
│   └── worktree_manager.py    # 修改：添加 detect_conflicts() 方法
├── application/
│   └── scheduler.py            # 使用：集成冲突检测到工作流
└── tests/
    └── test_conflict_detection.py  # 新增测试
```

**接口设计：**
```python
class WorktreeManager:
    def detect_conflicts(
        self,
        epic_ids: List[str]
    ) -> Dict[str, List[str]]:
        """检测文件冲突"""
        pass

    def format_conflict_report(
        self,
        conflicts: Dict[str, List[str]]
    ) -> str:
        """格式化冲突报告"""
        pass
```

### 测试策略

**单元测试覆盖：**
- 两个 Epic 冲突一个文件
- 两个 Epic 冲突多个文件
- 三个 Epic 冲突同一文件
- 无冲突场景
- 空 Epic 列表处理

**集成测试场景：**
- 实际创建 Worktree 并提交更改
- 检测真实的文件修改冲突
- 验证与 Scheduler 集成

**测试数据：**
```python
# 测试场景 1: 单文件冲突
epic_2_files = ["src/parser.py", "src/config.py"]
epic_3_files = ["src/parser.py", "src/utils.py"]
expected = {"src/parser.py": ["2", "3"]}

# 测试场景 2: 无冲突
epic_2_files = ["src/parser.py"]
epic_3_files = ["src/utils.py"]
expected = {}
```

### References

- [Source: docs/epics.md#Epic-4-Story-4.4]
- [Source: docs/architecture.md#3.5-Git-Worktree-管理模块]
- [Source: stories/4-1-create-git-worktree-for-epic.md] (Worktree 基础)
- FR Coverage: FR31 (冲突检测)
- NFR Coverage: NFR10 (Git 操作容错)
- 依赖：Story 4.1

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
