# Product Brief: AEDT

**Date:** 2025-11-23
**Author:** BMad
**Context:** Enterprise Development Toolkit

---

## Executive Summary

**AEDT (AI-Enhanced Delivery Toolkit)** 是一个智能 AI 开发编排引擎，解决 AI 辅助开发工作流（如 BMAD Method）的串行执行瓶颈，将 MVP 交付速度提升 3-5 倍。

**核心问题**：
使用 BMAD、Spec-Kit 等 AI 工作流开发 MVP 时，开发者面临严重的串行等待问题——即使 Epic 之间没有依赖关系，也必须等待一个完成才能开始下一个。对于有 10+ Epic 的项目，手动管理依赖关系、Git 分支、多 Agent 编排极其复杂，且无法在多个项目间高效切换，导致大量等待时间浪费。

**解决方案**：
AEDT 作为工作流无关的编排层，提供：
- **多项目全局管理**：统一 Dashboard 管理所有 MVP 项目，智能推荐下一步
- **智能依赖调度**：自动解析 Epic 依赖，识别可并行任务，最多同时运行 5 个 Subagent
- **Story 级细粒度开发**：单个 Epic 内逐个 Story 开发，避免上下文膨胀
- **Git 全自动化**：Git Worktrees 隔离、自动分支管理、智能合并
- **实时 TUI Dashboard**：终端内可视化，实时显示所有 Epic 状态和 Agent 进度
- **质量与成本控制**：自动化质量门控、冲突检测、API 成本监控

**目标用户**：
资深独立开发者、技术创业者、AI 效能极客——同时维护 2-5 个 MVP 项目，需要最大化 AI 工具的并行处理能力。

**MVP 目标**：
- 管理多个项目，并行调度 3-5 个 Epic
- TUI 实时 Dashboard
- Git 100% 自动化
- 10 个 Epic 从 10 天压缩到 2-3 天（3-5 倍提速）

**技术栈**：
TUI (Textual/Bubble Tea)、文件系统存储 (YAML)、Claude Code Task 工具、Git Worktrees

**下一步**：
验证 Claude Code Subagent 并发能力 → 构建核心架构 → 实现调度引擎 → TUI Dashboard → 质量测试

---

## Core Vision

### Problem Statement

**当前痛点：AI辅助开发的串行低效问题**

在使用 BMAD Method 等 AI 工作流进行 MVP 开发时，面临严重的串行执行瓶颈：

1. **强制串行等待**：完成 Epic 1 的规划后，必须等待开发完成才能开始 Epic 2 的规划和开发，即使两个 Epic 之间没有依赖关系

2. **手动编排复杂**：
   - 需要手动管理 10+ 个 Epic 的依赖关系
   - 手动创建 Git 分支、切换 Agent、初始化环境
   - 手动追踪哪个 Epic 在开发、哪个可以并行、哪个需要合并

3. **缺乏多项目管理**：
   - 同时维护多个 MVP 项目（项目 A、B、C...）
   - 无法在项目 A 等待时切换到项目 B 继续工作
   - 没有全局视图看到所有项目的未完成任务

4. **上下文膨胀问题**：
   - 一个 Epic 包含多个 Story，一次性开发导致上下文过多
   - Agent 容易迷失在大量代码中，质量下降

5. **质量与速度的权衡**：
   - 多 Agent 并行开发带来 Git 冲突风险
   - 代码质量参差不齐
   - API 调用成本失控

**核心问题**：现有 AI 工作流（BMAD、Spec-Kit 等）都是为单线程、单项目设计的，无法发挥 AI Agent 并行处理的潜力，导致 MVP 交付速度远低于理论极限。

### Proposed Solution

**AEDT：智能 AI 开发编排引擎**

AEDT 是一个工作流无关的 AI 开发编排层，位于工作流框架（BMAD、Spec-Kit 等）与 Git/Claude Code 之间，提供：

**1. 多项目全局视图**
- 统一 Dashboard 管理所有 MVP 项目
- 实时显示每个项目的未完成任务
- 智能推荐："建议从项目 A 的 Epic 3 开始"

**2. 智能依赖调度**
- 自动读取 BMAD 生成的 Epic 依赖关系
- 识别可并行的 Epic，自动启动开发
- 串行 Epic 自动排队等待

**3. 无缝项目切换**
- 项目 A 的 Epic 生成中 → 切换到项目 B 继续工作
- 保持所有项目的上下文和进度
- 最大化人的等待时间利用率

**4. 细粒度 Story 级开发**
- Epic 自动拆分为 Story 级任务
- Agent 逐个 Story 开发，避免上下文膨胀
- 每个 Story 独立提交，减少冲突

**5. 多 Agent 并行编排**
- 自动创建 Git 分支（git worktrees 隔离）
- 每个 Epic 启动独立 Subagent（使用 Claude Code Task 工具）
- 同一 Epic 内的多个 Story 由单个 Agent 串行开发，逐个提交
- 实时监控：10 个 Subagent 同时开发 10 个 Epic

**技术架构考量**：
- 优先使用 Claude Code Task 工具启动 subagent
- 探索 Cursor/Codex 等工具的更优集成方案
- 每个 Subagent 独立上下文，避免干扰

**6. 工作流插件化**
- **MVP**: 原生支持 BMAD Method
- **未来扩展**: GitHub Spec-Kit 工作流（插件化设计，预留扩展接口）
- 可扩展到其他 AI 工作流框架

**7. 质量与成本控制**
- Git 冲突预警和自动检测
- 代码质量门控（AI 预审 + 人工复审）
- API 调用成本监控和预算控制

---

## Target Users

### Primary Users

**资深独立开发者 / Solo Founder（AI效能极客）**

**画像**：
- **角色**：资深开发者、技术创业者、效能工程师
- **技能水平**：对 AI 辅助开发工具有深入理解（Claude Code、Cursor、BMAD Method 等）
- **典型场景**：同时维护 2-5 个 MVP 项目，快速验证想法
- **核心痛点**：
  - 一个人要做 PM、架构师、开发者的所有工作
  - AI 工具虽然提速，但串行流程仍然慢
  - 多个项目来回切换，上下文丢失
  - 10+ Epic 手动编排太累，容易出错

**当前工作流**：
```
早上：项目 A（BMAD Analyst → PM 规划 Epic 1-5）
中午：等待 Epic 1 开发... 无法启动 Epic 2
下午：项目 B（规划阶段）
晚上：回到项目 A，继续 Epic 2...
周末：处理 Git 冲突和合并
```

**AEDT 带来的改变**：
```
早上：项目 A 规划完 Epic 1-5 → 启动 5 个并行开发 Subagent
      切换到项目 B 继续规划（不浪费等待时间）
中午：Dashboard 显示：项目 A 的 Epic 1, 2 已完成
下午：项目 A 的 Epic 3, 4 开发中，处理 Epic 1, 2 的合并
晚上：项目 B 也启动并行开发
周末：玩！（自动化完成大部分工作）
```

**价值主张**：
- **10倍速度提升**：10个Epic从10天压缩到1-2天
- **零等待时间**：多项目并行，最大化人的利用率
- **降低认知负担**：系统自动编排，不用记住依赖关系
- **质量保障**：自动化质量门控，比手动更可靠

---

## MVP Scope

### MVP 定义与成功标准

**MVP 完成标准**：
- ✅ 管理多个项目，自动并行 3-5 个 Epic
- ✅ 基础 TUI Dashboard，实时显示所有 Epic 状态
- ✅ Git 分支和合并完全自动化
- ✅ 质量门控和冲突检测就位

### 核心功能（MVP Phase 1）

#### 1. 多项目管理中心
**功能**：
- 项目列表视图（所有 MVP 项目）
- 未完成任务聚合统计
- 智能推荐："建议从项目 A 的 Epic 3 开始"
- 快速项目切换（保持所有项目上下文）

**交互**：
- 命令：`aedt list` 或 TUI 主界面
- 显示：项目名称、状态、未完成 Epic 数、下一步建议

#### 2. BMAD 工作流深度集成
**功能**：
- 自动读取 BMAD 生成的 Epic 文档（从 `docs/epics/` 目录）
- 解析 Epic 依赖关系（从 Epic 元数据中提取）
- 提取 Story 列表（每个 Story 作为独立开发任务）
- 监听 BMAD 文件变化，自动刷新状态

**数据源**：
- `docs/epics/epic-*.md` - Epic 定义和依赖
- `docs/sprint-status.yaml` - Sprint 状态
- `docs/bmm-workflow-status.yaml` - 工作流进度

#### 3. 智能并行调度引擎
**功能**：
- **依赖分析**：解析 Epic 间依赖关系，构建 DAG（有向无环图）
- **并行识别**：自动识别可并行的 Epic（无依赖或依赖已完成）
- **自动启动**：Epic 规划完成后，用户手动确认启动开发
- **队列管理**：串行 Epic 自动排队，依赖完成后自动启动

**调度逻辑**：
```
规划阶段完成 → 用户确认启动 → 分析依赖关系
  ↓
可并行 Epic 1, 2, 3 → 自动创建分支 → 启动 Subagent
  ↓
Epic 4（依赖 Epic 1）→ 等待队列 → Epic 1 完成后自动启动
```

#### 4. Git Worktree 自动化
**功能**：
- 为每个 Epic 自动创建独立 Git Worktree
- 分支命名：`epic-{epic-id}` 或 `feature/{epic-name}`
- 工作目录隔离：`{project-root}/.aedt/worktrees/epic-{id}/`
- 自动清理：Epic 合并后删除 Worktree

**Git 操作**：
```bash
git worktree add .aedt/worktrees/epic-101 -b epic-101
# Subagent 在独立目录中开发
git worktree remove .aedt/worktrees/epic-101  # 合并后清理
```

#### 5. Subagent 编排系统
**功能**：
- 使用 Claude Code Task 工具启动每个 Epic 的 Subagent
- 传递上下文：Epic 描述、Story 列表、依赖信息
- Story 级串行开发：Subagent 逐个 Story 开发并提交
- 进度追踪：监听 Subagent 输出，解析开发进度

**Subagent 工作流**：
```
启动 Subagent → 加载 Epic 上下文 →
  Story 1 → 开发 → 测试 → git commit →
  Story 2 → 开发 → 测试 → git commit →
  Story 3 → 开发 → 测试 → git commit →
完成 → 通知主系统
```

**并发控制**：
- 最多同时运行 3-5 个 Subagent（MVP 限制）
- 超出限制的 Epic 进入队列等待

#### 6. 实时 TUI Dashboard
**界面布局**：
```
╔═══════════════════════════════════════════════════════╗
║  AEDT - AI Enhanced Delivery Toolkit                 ║
║  Projects: 3 | Active Epics: 5 | Completed: 12       ║
╠═══════════════════════════════════════════════════════╣
║  Project A (AEDT) - 5 Epics                          ║
║  ├─ Epic 1: 多项目管理          [✓ Complete]         ║
║  ├─ Epic 2: BMAD 集成           [⚙ Developing 60%]   ║
║  ├─ Epic 3: 调度引擎            [⚙ Developing 30%]   ║
║  ├─ Epic 4: TUI Dashboard       [⏳ Queued]          ║
║  └─ Epic 5: Git 自动化          [⏳ Queued]          ║
║                                                       ║
║  Project B (Other) - 3 Epics                         ║
║  ├─ Epic 1: Feature X           [⚙ Developing 45%]   ║
║  └─ ...                                              ║
╠═══════════════════════════════════════════════════════╣
║  Active Agents:                                       ║
║  Agent-1 (Epic 2) → Story 2/5: Implementing parser   ║
║  Agent-2 (Epic 3) → Story 1/3: Building scheduler    ║
║  Agent-3 (Project B Epic 1) → Story 3/4: Testing     ║
╠═══════════════════════════════════════════════════════╣
║  Merge Queue: Epic 1 ✓ Ready | Epic 2 ⏳ In Progress ║
╚═══════════════════════════════════════════════════════╝
[s] Switch Project | [r] Refresh | [q] Quit
```

**实时刷新**：
- 监听 Agent 输出文件
- 每 5 秒刷新进度
- 支持手动刷新（快捷键 `r`）

#### 7. 自动合并与冲突处理
**功能**：
- Epic 开发完成 → 自动合并到主分支（无需手动确认）
- 冲突检测：合并前检测潜在冲突
- 冲突解决：
  - **MVP 阶段**：检测到冲突暂停，通知用户手动解决
  - **未来增强**：AI 自动解决简单冲突

**合并流程**：
```
Epic 完成 → 运行测试 → 通过 ✓
  ↓
检测冲突 → 无冲突 ✓
  ↓
自动合并到 main → 删除 Worktree → 通知用户
```

**冲突处理**：
```
检测到冲突 ✗
  ↓
暂停合并 → TUI 显示红色警告
  ↓
用户手动解决 → 标记解决 → 继续合并
```

#### 8. 基础质量门控
**功能**：
- **提交前检查**：每个 Story 提交前运行 linter
- **Epic 完成检查**：运行单元测试
- **合并前检查**：运行完整测试套件

**门控配置**：
```yaml
# .aedt/quality-gates.yaml
pre_commit:
  - lint
  - format_check

epic_complete:
  - unit_tests
  - security_scan

pre_merge:
  - integration_tests
  - e2e_tests (optional)
```

**失败处理**：
- 质量检查失败 → 暂停流程 → 通知 TUI → 等待修复

#### 9. 数据持久化（文件系统）
**存储结构**：
```
{project-root}/
  .aedt/
    config.yaml              # 全局配置
    projects/
      project-a/
        status.yaml          # 项目状态
        epics/
          epic-101.yaml      # Epic 进度和状态
          epic-102.yaml
        agents/
          agent-1.log        # Agent 日志
          agent-2.log
      project-b/
        ...
    worktrees/               # Git Worktrees
      epic-101/
      epic-102/
```

**状态文件示例**：
```yaml
# .aedt/projects/project-a/epics/epic-101.yaml
epic_id: 101
name: "多项目管理中心"
status: "developing"  # planning/queued/developing/complete
progress: 0.6
agent_id: "agent-1"
branch: "epic-101"
worktree: ".aedt/worktrees/epic-101"
stories:
  - id: "101-1"
    name: "项目列表视图"
    status: "complete"
  - id: "101-2"
    name: "任务统计"
    status: "developing"
  - id: "101-3"
    name: "智能推荐"
    status: "pending"
dependencies:
  - epic_id: null  # 无依赖
started_at: "2025-11-23T10:00:00Z"
completed_at: null
```

### 人工介入点（明确定义）

**手动确认点**：
1. ✋ **Epic 规划完成 → 启动开发**
   - 用户在 TUI 中查看 Epic 列表
   - 选择要启动的 Epic（支持多选）
   - 确认后系统自动调度

2. ✋ **冲突检测后手动解决**
   - 系统检测到冲突，暂停合并
   - TUI 显示冲突文件列表
   - 用户手动解决冲突
   - 标记解决后，系统继续合并

**全自动点**：
1. 🤖 **Epic 开发完成 → 合并到主分支**
   - 无冲突情况下自动合并
   - 不需要手动确认

2. 🤖 **依赖 Epic 完成 → 启动等待队列**
   - Epic 1 完成后，自动启动依赖 Epic 1 的其他 Epic

3. 🤖 **Git 分支管理**
   - 自动创建、切换、删除分支

4. 🤖 **质量检查**
   - 自动运行测试和 linter
   - 失败时暂停并通知

### 技术架构决策

**界面**：TUI (Terminal UI) ✅ **已确认**
- **框架选择**：Textual (Python) 或 Bubble Tea (Go)
  - **推荐 Textual (Python)**：
    - 更成熟，文档丰富
    - 与 Python 生态集成好（YAML 解析、文件操作）
    - 开发速度快，适合快速迭代
  - **备选 Bubble Tea (Go)**：
    - 性能更好，单文件部署
    - 适合追求极致性能的场景
- **布局设计**：多面板布局（项目列表、Epic 状态、Agent 活动、日志输出）
- **实时刷新**：异步更新，5 秒自动刷新 + 手动刷新快捷键
- **键盘导航**：Vim 风格快捷键（hjkl 导航、/ 搜索、: 命令模式）

**未来扩展**：
- 保留架构可扩展性，预留 Web API 接口
- TUI 作为"专业模式"永久保留
- Phase 2+ 可选增加 Web UI 作为"可视化模式"
- 两者共享同一数据层（文件系统 YAML）

**数据存储**：文件系统（YAML/JSON）
- 便于调试和版本控制
- 符合 BMAD 文件驱动的设计哲学
- 可读性强，方便手动编辑

**Subagent 启动**：Claude Code Task 工具
- 每个 Epic 一个 Subagent
- 独立上下文，避免干扰
- 探索 Cursor/Codex 更优方案（如果存在）

**Git 隔离**：Git Worktrees
- 完全隔离的工作目录
- 避免分支切换导致的文件冲突
- 支持真正的并行开发

### 未来功能（Phase 2+，MVP后扩展）

#### 延后的功能
- ❌ **Spec-Kit 工作流支持**：插件化架构已预留，Phase 2 实现
- ❌ **高级可视化**：甘特图、依赖关系图、性能仪表盘
- ❌ **AI 成本详细分析**：API 调用成本追踪、预算预警、优化建议
- ❌ **自动化 PR 创建**：自动生成 PR 描述、添加 Reviewer
- ❌ **AI 驱动的冲突解决**：自动解决简单冲突（如格式化、import 顺序）
- ❌ **多人协作**：团队共享项目、权限管理、协作锁
- ❌ **Webhook 集成**：Slack/Discord 通知、CI/CD 触发
- ❌ **Web UI**：浏览器访问的可视化界面
- ❌ **移动端支持**：手机查看进度

---

## 成功指标

### MVP 成功标准（自用验证）

**功能完整性**：
- ✅ 能同时管理 3 个项目
- ✅ 能并行调度 5 个 Epic
- ✅ TUI 实时显示所有状态
- ✅ Git 操作 100% 自动化
- ✅ 质量门控和冲突检测工作正常

**性能指标**：
- **开发速度提升**：10 个 Epic 从 10 天压缩到 2-3 天（3-5倍提速）
- **等待时间消除**：多项目切换，零闲置时间
- **错误率降低**：自动化减少手动操作错误 >80%

**用户体验**：
- TUI 响应延迟 < 200ms
- Epic 状态刷新实时性 < 5 秒
- 冲突检测准确率 > 95%

### 长期愿景（Phase 2+）

**社区目标**（6-12 个月）：
- 10+ 活跃用户（AI 效能极客社区）
- 5+ 贡献者（开源贡献）
- 支持 3+ 工作流框架（BMAD、Spec-Kit、自定义）

**生态目标**（12+ 个月）：
- 成为 AI 辅助开发的标准编排层
- 集成到主流 AI 编码工具（Claude Code、Cursor、Windsurf）
- 工作流插件市场（社区贡献工作流）

---

## 技术风险与假设

### 关键假设

**技术可行性假设**：
1. ✅ **Claude Code Task 工具能启动 Subagent**
   - 假设：Task 工具支持传递足够的上下文
   - 验证：需要实验验证 Subagent 的并发限制和稳定性

2. ✅ **Git Worktrees 支持大规模并行**
   - 假设：5 个 Worktrees 不会显著影响性能
   - 验证：需要测试文件系统和 Git 性能

3. ✅ **BMAD Epic 文档包含依赖关系**
   - 假设：BMAD 生成的文档有结构化的依赖信息
   - 风险：如果没有，需要用户手动标注或 AI 推断

4. ⚠️ **Agent 开发进度可追踪**
   - 假设：能从 Subagent 输出解析进度（如"完成 Story 2/5"）
   - 风险：可能需要 Agent 主动报告进度

### 主要技术风险

**风险 1：Subagent 稳定性**
- **描述**：多个 Subagent 并发可能导致 API 限流、成本失控
- **缓解**：
  - MVP 限制并发数 3-5 个
  - 实现 API 调用成本监控
  - 提供手动暂停功能

**风险 2：Git 冲突复杂性**
- **描述**：自动合并可能遗漏复杂冲突（如逻辑冲突）
- **缓解**：
  - MVP 检测到冲突就暂停
  - Phase 2 再引入 AI 自动解决
  - 合并前强制运行测试

**风险 3：上下文传递复杂**
- **描述**：Epic 描述、Story 列表、依赖关系传递给 Subagent 可能不完整
- **缓解**：
  - 设计结构化的上下文传递格式（JSON/YAML）
  - 每个 Subagent 在独立 Worktree 中有完整代码库

**风险 4：TUI 性能**
- **描述**：实时刷新 10+ Agent 的状态可能卡顿
- **缓解**：
  - 异步更新，避免阻塞主线程
  - 限制刷新频率（5 秒一次）
  - 使用高性能 TUI 框架（Textual/Bubble Tea）

### 开放问题

**待验证问题**：
1. **Claude Code Subagent 的并发限制是多少？**
   - 需要实验：同时启动 10 个 Subagent 是否稳定？

2. **BMAD Epic 依赖关系的格式是什么？**
   - 需要查看实际 BMAD 输出
   - 如果没有，需要设计依赖标注格式

3. **Git Worktree 性能瓶颈？**
   - 大型代码库（>10GB）下 5 个 Worktree 是否可行？

4. **Cursor/Codex 的更优集成方案？**
   - 是否有比 Task 工具更适合的 API？
   - 需要调研这些工具的文档

---

## 下一步行动

### 立即行动（启动 MVP 开发）

**Phase 0：验证关键假设（1-2 天）**
1. 实验 Claude Code Task 工具启动 Subagent
2. 查看 BMAD Epic 文档格式，确认依赖关系
3. 测试 Git Worktrees 并发性能
4. ✅ **TUI 框架已确定：Textual (Python)**
   - 快速搭建 Hello World TUI
   - 验证实时刷新机制
   - 测试多面板布局

**Phase 1：核心架构（MVP 第一周）**
1. 搭建 AEDT 基础架构（CLI 框架、配置管理）
2. 实现 BMAD 文档解析器
3. 实现依赖分析引擎（DAG 构建）
4. 实现 Git Worktree 管理模块

**Phase 2：调度与 Agent 编排（MVP 第二周）**
1. 实现 Subagent 启动和监控
2. 实现并行调度逻辑
3. 实现 Story 级进度追踪
4. 实现自动合并逻辑

**Phase 3：TUI 与用户体验（MVP 第三周）**
1. 实现 TUI Dashboard 基础布局
2. 实现实时状态刷新
3. 实现项目切换和 Epic 选择
4. 实现冲突检测和通知

**Phase 4：质量与测试（MVP 第四周）**
1. 实现质量门控集成
2. 端到端测试（完整工作流）
3. 性能优化（TUI 响应速度）
4. 文档编写（README、使用指南）

### 后续规划（MVP 后）

**Phase 5：Spec-Kit 支持**（MVP + 1-2 周）
- 插件化架构实现
- Spec-Kit 工作流适配器

**Phase 6：高级功能**（MVP + 1-2 个月）
- AI 冲突自动解决
- 成本优化和预算管理
- 高级可视化

**Phase 7：开源与社区**（MVP + 3 个月）
- 开源发布（GitHub）
- 社区文档和示例
- 插件 API 文档

---

_This Product Brief captures the vision and requirements for AEDT._

_It was created through collaborative discovery and reflects the unique needs of this Enterprise Development Toolkit project._
