# Story 4.1: 为 Epic 创建 Git Worktree

Status: drafted

## Story

作为用户，
我希望 AEDT 为每个 Epic 创建隔离的 Git Worktree，
以便多个 Epic 可以并行开发而不产生冲突。

## Acceptance Criteria

1. **AC1: 创建 Worktree 和分支**
   - 当 Epic 2 准备启动时
   - AEDT 从主分支创建 Git 分支 "epic-2"
   - 在 `.aedt/worktrees/epic-2/` 创建 Worktree
   - Epic 2 的状态中保存 Worktree 路径

2. **AC2: 分支已存在时的错误处理**
   - 当分支 "epic-2" 已存在时
   - AEDT 尝试创建 Worktree
   - CLI 显示错误："Branch 'epic-2' already exists. Clean up with `aedt clean` or delete manually."
   - Epic 启动被中止

## Tasks / Subtasks

- [ ] **任务 1：实现 WorktreeManager 核心功能** (AC: 1)
  - [ ] 1.1 创建 `WorktreeManager` 类和基础结构
  - [ ] 1.2 实现 `create_worktree(epic_id, branch_prefix="epic")` 方法
  - [ ] 1.3 添加分支存在性验证逻辑
  - [ ] 1.4 实现 Worktree 路径生成逻辑

- [ ] **任务 2：集成 GitPython 实现 Git 操作** (AC: 1)
  - [ ] 2.1 安装并配置 GitPython 依赖
  - [ ] 2.2 实现分支创建：`repo.git.worktree('add', path, '-b', branch_name)`
  - [ ] 2.3 添加 Git 操作错误处理和日志记录
  - [ ] 2.4 验证 Worktree 创建成功

- [ ] **任务 3：状态持久化** (AC: 1)
  - [ ] 3.1 定义 Worktree 状态数据结构：`{epic_id, branch_name, path, created_at}`
  - [ ] 3.2 在 Epic 状态中保存 Worktree 信息
  - [ ] 3.3 通过 StateManager 持久化到 `.aedt/projects/<project>/status.yaml`

- [ ] **任务 4：错误处理和验证** (AC: 2)
  - [ ] 4.1 实现分支已存在检测逻辑
  - [ ] 4.2 显示用户友好的错误消息
  - [ ] 4.3 实现 Epic 启动中止机制
  - [ ] 4.4 记录错误到日志系统

- [ ] **任务 5：单元测试** (AC: 1, 2)
  - [ ] 5.1 测试 Worktree 成功创建场景
  - [ ] 5.2 测试分支已存在错误场景
  - [ ] 5.3 测试状态持久化
  - [ ] 5.4 测试并发 Worktree 创建

## Dev Notes

### 架构约束和模式

**模块定位：**
- 属于**基础设施层 (Infrastructure Layer)**
- 与 `Scheduler` 和 `StateManager` 交互
- 为 `SubagentOrchestrator` 提供隔离的工作目录

**技术实现要点：**

1. **Git Worktree 命令模式**
   ```python
   # 使用 GitPython 执行 worktree 操作
   repo.git.worktree('add', path, '-b', branch_name)
   ```

2. **分支命名规范**
   - 格式：`{branch_prefix}-{epic_id}`
   - 示例：`epic-2`, `epic-5`
   - 可通过配置文件自定义 `branch_prefix`

3. **Worktree 路径结构**
   - 基础路径：`.aedt/worktrees/`
   - Epic Worktree：`.aedt/worktrees/epic-{epic_id}/`
   - 路径应使用绝对路径存储

4. **错误处理策略**
   - 分支冲突：友好提示用户清理，不强制覆盖
   - Git 操作失败：记录完整错误，建议用户手动检查 Git 状态
   - 权限问题：提示检查目录权限

5. **依赖管理**
   - 需要 Git 2.25+ 版本（稳定的 worktree 支持）
   - 需要 GitPython >= 3.1.0
   - 前置条件：Epic 1 完成（状态管理必须存在）

### 项目结构对齐

**预期文件位置：**
```
aedt/
├── infrastructure/
│   └── worktree_manager.py    # WorktreeManager 实现
├── models/
│   └── worktree.py             # Worktree 数据模型
└── tests/
    └── test_worktree_manager.py
```

**数据模型：**
```python
@dataclass
class Worktree:
    epic_id: str
    branch_name: str
    path: str
    created_at: datetime
```

### 测试策略

**单元测试覆盖：**
- Worktree 创建成功路径
- 分支已存在错误处理
- Git 操作失败恢复
- 并发创建场景

**集成测试场景：**
- Scheduler 调用 WorktreeManager 创建 Worktree
- 状态持久化到 StateManager
- Worktree 清理（Story 4.8 实现）

### References

- [Source: docs/epics.md#Epic-4-Story-4.1]
- [Source: docs/architecture.md#3.5-Git-Worktree-管理模块]
- [GitPython Documentation](https://gitpython.readthedocs.io/)
- FR Coverage: FR18 (Git Worktree 隔离), FR26 (分支管理)
- NFR Coverage: NFR10 (Git 操作容错)

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
