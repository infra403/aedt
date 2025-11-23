# coding - Product Requirements Document

**Author:** BMad
**Date:** 2025-11-23
**Version:** 1.0

---

## Executive Summary

AEDT (AI-Enhanced Delivery Toolkit) 是一个智能 AI 开发编排引擎，专为资深独立开发者和技术创业者设计。它解决了使用 AI 辅助开发工作流（如 BMAD Method、Spec-Kit）时面临的串行执行瓶颈问题，将 MVP 交付速度提升 3-5 倍。

**核心问题：**
当前 AI 工作流强制开发者串行执行 Epic——即使多个 Epic 之间没有依赖关系，也必须等待一个完成才能开始下一个。对于包含 10+ Epic 的项目，手动管理依赖、Git 分支和多 Agent 编排极其复杂，且无法在多个项目间高效切换，导致大量等待时间浪费。

**解决方案：**
AEDT 作为工作流无关的编排层，提供：
- 智能依赖调度：自动识别可并行 Epic，最多同时运行 5 个 Subagent
- 多项目全局管理：统一 Dashboard，智能推荐下一步
- Git 全自动化：Worktrees 隔离、自动分支管理、智能合并
- 实时 TUI Dashboard：终端内可视化所有 Epic 状态和 Agent 进度
- 质量与成本控制：自动化质量门控、冲突检测、API 成本监控

**MVP 目标：**
- 管理多个项目，并行调度 3-5 个 Epic
- TUI 实时 Dashboard
- Git 100% 自动化
- 10 个 Epic 从 10 天压缩到 2-3 天（3-5 倍提速）

### What Makes This Special

**AEDT 的独特价值：将 AI 辅助开发从"单线程串行"升级到"智能并行编排"**

现有 AI 工作流（BMAD、Spec-Kit）都是为单线程、单项目设计的，无法发挥 AI Agent 并行处理的潜力。AEDT 通过智能调度、多项目管理和自动化 Git 操作，让开发者充分利用 AI 的并行能力，实现：

1. **零等待时间**：项目 A 等待时切换到项目 B，最大化人的利用率
2. **降低认知负担**：系统自动编排依赖，不用记住复杂关系
3. **质量保障**：自动化质量门控比手动更可靠
4. **速度提升**：10 个 Epic 从 10 天压缩到 2-3 天

这不是一个简单的任务管理工具，而是一个**AI 开发效能倍增器**。

---

## Project Classification

**Technical Type:** Developer Tool
**Domain:** General Software Development
**Complexity:** Medium

**分类依据：**

AEDT 是一个开发者工具（Developer Tool），专为 AI 辅助开发工作流设计。它的核心用户是技术创业者和资深开发者，需要：

- 高度可定制的编排逻辑
- 与现有工作流（BMAD、Spec-Kit）无缝集成
- TUI 界面（专业开发者偏好）
- 文件系统数据存储（便于调试和版本控制）

**复杂度评估（Medium）：**

- ✅ 技术复杂度中等：多进程管理、Git 自动化、依赖调度
- ✅ 领域知识中等：需要理解 AI 工作流、Git Worktrees、TUI 框架
- ❌ 无高合规要求：不涉及医疗、金融等强监管领域
- ✅ 创新性强：首个 AI 开发编排引擎，需要探索最佳实践

---

## Success Criteria

### MVP 成功定义：Dogfooding 验证

**核心目标：先解决自己的问题**

AEDT 的 MVP 成功不是用户数量，而是**能否让我自己（作为资深开发者）高效管理多个 MVP 项目，速度提升 3-5 倍**。

**具体成功标准：**

1. **真实项目验证**
   - ✅ 使用 AEDT 完成 2-3 个真实 MVP 项目的完整开发周期
   - ✅ 每个项目包含 10+ Epic，能够自动并行调度
   - ✅ 从规划到实现的时间从 10 天压缩到 2-3 天

2. **功能完整性**
   - ✅ 同时管理 3 个项目，无需手动切换上下文
   - ✅ 并行调度 3-5 个 Epic，Subagent 稳定运行
   - ✅ TUI 实时显示所有 Epic 状态和 Agent 进度
   - ✅ Git 操作 100% 自动化（分支、合并、冲突检测）
   - ✅ 质量门控和冲突检测正常工作

3. **性能指标**
   - **开发速度提升**：10 个 Epic 从 10 天 → 2-3 天（3-5 倍提速）
   - **等待时间消除**：多项目切换，零闲置时间（项目 A 等待时切换到项目 B）
   - **错误率降低**：自动化减少手动操作错误 > 80%
   - **TUI 响应性**：界面响应延迟 < 200ms
   - **状态刷新**：Epic 状态实时性 < 5 秒
   - **冲突检测准确率**：> 95%

4. **用户体验（自己的体验）**
   - ✅ 早上启动 3 个项目的并行开发，无需手动编排
   - ✅ Dashboard 一眼看清所有项目状态和下一步
   - ✅ 冲突检测及时提醒，不会在合并时才发现问题
   - ✅ 质量门控自动拦截低质量代码

**MVP 完成的判断标准：**
- ✅ 能够用 AEDT 完成一个 10+ Epic 的真实项目，全程无需手动干预 Git 和依赖管理
- ✅ 速度提升达到 3 倍以上，且质量不下降
- ✅ 自己愿意每天使用它管理所有 MVP 项目

### 长期愿景（Phase 2+）

**6 个月目标：**
- 10+ AI 效能极客使用（早期采用者社区）
- 5+ 开源贡献者
- 支持 3+ 工作流框架（BMAD、Spec-Kit、自定义）

**12 个月目标：**
- 成为 AI 辅助开发的标准编排层
- 主流 AI 编码工具主动集成（Claude Code、Cursor、Windsurf）
- 工作流插件市场（社区贡献工作流）

**成功的终极标志：**
当其他开发者说"我用 AEDT 管理 AI 开发工作流"时，就像说"我用 Git 管理代码"一样自然。

---

## Product Scope

### MVP - Minimum Viable Product

**核心原则：证明核心价值假设 - "并行编排能让 AI 开发提速 3-5 倍"**

**MVP 必须包含的功能（Phase 1 - 4周）：**

**1. 多项目管理中心**
- 项目列表视图（所有 MVP 项目）
- 未完成任务聚合统计
- 智能推荐下一步行动
- 快速项目切换（保持所有项目上下文）

**2. BMAD 工作流深度集成**
- 自动读取 BMAD 生成的 Epic 文档（`docs/epics/` 目录）
- 解析 Epic 依赖关系（从 Epic 元数据提取）
- 提取 Story 列表（每个 Story 作为独立开发任务）
- 监听 BMAD 文件变化，自动刷新状态

**3. 智能并行调度引擎**
- 依赖分析：解析 Epic 间依赖关系，构建 DAG（有向无环图）
- 并行识别：自动识别可并行的 Epic（无依赖或依赖已完成）
- 自动启动：Epic 规划完成后，用户手动确认启动开发
- 队列管理：串行 Epic 自动排队，依赖完成后自动启动
- 并发控制：最多同时运行 3-5 个 Subagent

**4. Git Worktree 自动化**
- 为每个 Epic 自动创建独立 Git Worktree
- 分支命名：`epic-{epic-id}` 或 `feature/{epic-name}`
- 工作目录隔离：`{project-root}/.aedt/worktrees/epic-{id}/`
- 自动清理：Epic 合并后删除 Worktree

**5. Subagent 编排系统**
- 使用 Claude Code Task 工具启动每个 Epic 的 Subagent
- 传递上下文：Epic 描述、Story 列表、依赖信息
- Story 级串行开发：Subagent 逐个 Story 开发并提交
- 进度追踪：监听 Subagent 输出，解析开发进度

**6. 实时 TUI Dashboard**
- 多面板布局：项目列表、Epic 状态、Agent 活动、日志输出
- 实时刷新：异步更新，5 秒自动刷新 + 手动刷新快捷键
- 键盘导航：Vim 风格快捷键（hjkl 导航、/ 搜索、: 命令模式）
- 状态可视化：进度条、状态图标、颜色编码

**7. 自动合并与冲突处理**
- Epic 开发完成 → 自动合并到主分支（无冲突时）
- 冲突检测：合并前检测潜在冲突
- 冲突解决：检测到冲突暂停，通知用户手动解决

**8. 基础质量门控**
- 提交前检查：每个 Story 提交前运行 linter
- Epic 完成检查：运行单元测试
- 合并前检查：运行完整测试套件
- 失败处理：质量检查失败 → 暂停流程 → 通知 TUI → 等待修复

**9. 数据持久化（文件系统）**
- YAML/JSON 文件存储项目状态、Epic 进度、Agent 日志
- 存储结构：`.aedt/projects/{project-name}/`
- 便于调试和版本控制

**MVP 不包含（明确排除）：**
- ❌ Spec-Kit 工作流支持（延后到 Phase 2）
- ❌ Web UI 界面（专注 TUI）
- ❌ AI 自动解决冲突（人工解决）
- ❌ 高级可视化（甘特图、依赖关系图）
- ❌ 多人协作功能
- ❌ Webhook 集成（Slack/Discord 通知）
- ❌ 详细的 API 成本分析（仅基础监控）

**MVP 完成标准：**
能够用 AEDT 管理一个真实项目（10+ Epic），实现 3-5 个 Epic 并行开发，Git 100% 自动化，速度提升 3 倍。

---

### Growth Features (Post-MVP)

**Phase 2（MVP + 1-2 个月）：工作流扩展与高级功能**

**1. 多工作流支持**
- Spec-Kit 工作流适配器
- 自定义工作流插件 API
- 工作流配置文件（YAML 定义依赖和 Story 结构）

**2. 高级冲突解决**
- AI 自动解决简单冲突（格式化、import 顺序）
- 冲突预测：提前警告潜在冲突的 Epic 组合
- 智能合并策略建议

**3. 成本优化与监控**
- API 调用成本追踪（按项目、Epic、Agent 维度）
- 预算预警：超出预算时暂停
- 成本优化建议：识别低效 Agent

**4. 高级可视化**
- 依赖关系图（DAG 可视化）
- Epic 进度甘特图
- 性能仪表盘（速度提升、成本趋势）

**5. 自动化增强**
- 自动生成 PR 描述（基于 Epic 和 Story）
- 自动添加 Reviewer
- CI/CD 集成（自动触发测试和部署）

---

### Vision (Future)

**Phase 3+（12 个月及以后）：生态系统与社区**

**1. 工作流插件市场**
- 社区贡献工作流
- 工作流评分和推荐系统
- 一键安装工作流包

**2. 多人协作**
- 团队共享项目
- 权限管理（只读、编辑、管理员）
- 协作锁（防止多人同时编辑同一 Epic）

**3. 集成生态**
- Cursor、Windsurf、Codeium 等 AI 编码工具集成
- GitHub、GitLab 深度集成
- Slack/Discord/Teams 通知
- Jira/Linear 任务同步

**4. Web UI（可选）**
- 浏览器访问的可视化界面
- 移动端支持（手机查看进度）
- TUI 作为"专业模式"永久保留

**5. AI 驱动的智能优化**
- 自动识别 Epic 依赖关系（无需手动标注）
- 智能推荐最佳并行组合（基于历史数据）
- 自动优化 Subagent 资源分配

**6. 开源社区**
- 成为 AI 辅助开发的标准编排层
- 主流 AI 工具主动集成
- 活跃的贡献者社区

**愿景的终极形态：**
AEDT 成为 AI 开发工作流的"操作系统"，任何 AI 工作流都能无缝接入，任何 AI 编码工具都能通过 AEDT 编排。

---

## Developer Tool Specific Requirements

### 语言与技术栈

**AEDT 核心实现：**
- **语言**：Python 3.10+
  - 选择理由：成熟的 TUI 框架（Textual）、丰富的 YAML/文件处理库、快速迭代
  - 备选方案：Go + Bubble Tea（性能更好，但开发速度慢）

**支持的项目语言：**
- **语言无关** - AEDT 是工作流编排层，不关心项目用什么语言开发
- 只要项目使用 Git，AEDT 就能管理
- 只要工作流生成标准格式（YAML/Markdown），AEDT 就能解析

**依赖库：**
- **TUI**：Textual（终端用户界面框架）
- **YAML 解析**：PyYAML 或 ruamel.yaml
- **Git 操作**：GitPython
- **进程管理**：asyncio + subprocess
- **文件监听**：watchdog

---

### 安装与分发

**MVP 阶段（Phase 1）：**
- **安装方式**：Git clone + `pip install -e .`（本地开发模式）
- **要求**：Python 3.10+、Git、Claude Code（用于 Subagent）
- **平台支持**：macOS、Linux（Windows 支持延后到 Phase 2）

**命令行安装流程：**
```bash
git clone https://github.com/yourusername/aedt.git
cd aedt
pip install -e .
aedt init  # 初始化配置
aedt start # 启动 TUI Dashboard
```

**Phase 2 增强：**
- 发布到 PyPI → `pip install aedt`
- 提供独立二进制（PyInstaller 打包）
- Windows 平台支持

---

### IDE 集成

**MVP 阶段：**
- **无需 IDE 集成** - AEDT 是独立的 TUI 工具，在终端运行
- 开发者在终端运行 `aedt start`，在 IDE 中照常编码
- Subagent 在独立 Worktree 中工作，不影响主工作区

**Phase 2+ 可选集成：**
- **VS Code Extension**：
  - 侧边栏显示 Epic 状态
  - 快速跳转到 Worktree 目录
  - 实时同步 AEDT Dashboard 状态

- **JetBrains 插件**（Phase 3）：
  - 同 VS Code 功能

**设计原则：**
IDE 集成是"锦上添花"，不是核心功能。TUI 必须足够强大，独立使用无障碍。

---

### 文档需求

**MVP 必备文档：**

1. **README.md** - 项目主页和快速开始
   - 什么是 AEDT？（30 秒电梯演讲）
   - 为什么需要 AEDT？（核心问题和解决方案）
   - 5 分钟快速演示（GIF 动图 + 命令行步骤）
   - 安装指南
   - 核心概念解释（Project、Epic、Subagent、Worktree、DAG）

2. **INSTALL.md** - 详细安装指南
   - 系统要求
   - 依赖安装
   - 配置 Claude Code API
   - 验证安装成功

3. **USAGE.md** - 使用指南
   - 初始化项目：`aedt init`
   - 添加项目：`aedt project add <path>`
   - 启动 Dashboard：`aedt start`
   - TUI 快捷键列表
   - 常用工作流

4. **CONFIG.md** - 配置参考
   - `.aedt/config.yaml` 完整配置项说明
   - 质量门控配置示例
   - Subagent 启动参数
   - 工作流适配器配置

5. **TROUBLESHOOTING.md** - 故障排查
   - 常见错误及解决方案
   - 日志位置：`.aedt/logs/`
   - 如何手动清理 Worktree
   - 如何重置项目状态

**Phase 2+ 文档：**
- **API.md** - 插件开发者 API 文档
- **WORKFLOW_ADAPTER.md** - 如何适配新工作流
- **ARCHITECTURE.md** - 系统架构设计
- **CONTRIBUTING.md** - 贡献指南

---

### 示例与演示

**MVP 必备示例：**

1. **示例项目** - `examples/sample-project/`
   - 包含 10 个 Epic 的模拟项目
   - Epic 文档遵循 BMAD 格式：
     ```
     docs/epics/
       epic-001-user-auth.md
       epic-002-dashboard.md
       epic-003-settings.md
       ...
     ```
   - 依赖关系明确：
     - Epic 1-3 无依赖（可并行）
     - Epic 4 依赖 Epic 1
     - Epic 5 依赖 Epic 2, 3
   - 用于演示 AEDT 的并行调度能力

2. **配置示例** - `examples/configs/`
   - **simple.yaml** - 单项目配置
   - **multi-project.yaml** - 多项目配置
   - **custom-quality-gates.yaml** - 自定义质量门控
   - **advanced.yaml** - 高级配置（自定义 Subagent 参数、成本限制）

3. **视频演示**
   - **5 分钟快速演示**（使用 asciinema 录制）：
     1. 初始化 AEDT
     2. 添加示例项目
     3. 启动 Dashboard
     4. 自动并行调度 3 个 Epic
     5. 实时查看 Subagent 进度
     6. 自动合并完成的 Epic
   - 发布到 README 和项目主页

4. **教程项目** - `examples/tutorial/`
   - 逐步引导用户从零开始使用 AEDT
   - 包含详细注释和解释
   - 每一步都有检查点验证

---

### 开发者体验 (DX) 要求

**命令行界面设计：**
```bash
aedt init                    # 初始化配置
aedt project add <path>      # 添加项目
aedt project list            # 列出所有项目
aedt start                   # 启动 TUI Dashboard
aedt status                  # 查看所有项目状态（非交互式）
aedt logs <epic-id>          # 查看特定 Epic 日志
aedt clean                   # 清理所有 Worktree
```

**TUI 快捷键（Vim 风格）：**
- `h/j/k/l` - 导航
- `Enter` - 选择/展开
- `s` - 切换项目 (Switch)
- `r` - 刷新状态 (Refresh)
- `/` - 搜索 Epic
- `:` - 命令模式
- `q` - 退出

**错误处理：**
- 友好的错误提示（不要只显示堆栈跟踪）
- 建议性错误信息："找不到配置文件，是否运行 `aedt init` 初始化？"
- 彩色输出（红色=错误、黄色=警告、绿色=成功）

**日志：**
- 分级日志：DEBUG、INFO、WARNING、ERROR
- 日志文件：`.aedt/logs/aedt.log`
- TUI 内实时日志面板

---

### 代码示例与 API 设计

**插件 API（Phase 2）：**

虽然 MVP 不实现插件系统，但需要预留扩展接口：

```python
# 工作流适配器接口
class WorkflowAdapter:
    def parse_epics(self, project_path: str) -> List[Epic]:
        """解析 Epic 列表"""
        pass

    def parse_dependencies(self, epics: List[Epic]) -> DAG:
        """解析依赖关系，返回 DAG"""
        pass

    def parse_stories(self, epic: Epic) -> List[Story]:
        """解析 Story 列表"""
        pass

# BMAD 适配器实现
class BMADAdapter(WorkflowAdapter):
    def parse_epics(self, project_path: str) -> List[Epic]:
        # 读取 docs/epics/*.md
        # 解析 YAML frontmatter
        # 返回 Epic 对象
        pass
```

**配置文件结构：**
```yaml
# .aedt/config.yaml
version: "1.0"

projects:
  - name: "AEDT"
    path: "/path/to/aedt"
    workflow: "bmad"  # 工作流类型

  - name: "Other Project"
    path: "/path/to/other"
    workflow: "bmad"

subagent:
  max_concurrent: 5
  timeout: 3600  # 秒
  model: "claude-sonnet-4"

quality_gates:
  pre_commit:
    - "lint"
    - "format_check"
  epic_complete:
    - "unit_tests"
  pre_merge:
    - "integration_tests"

git:
  worktree_base: ".aedt/worktrees"
  branch_prefix: "epic"
  auto_cleanup: true
```

---

## User Experience Principles

### TUI 设计哲学

**核心原则：专业工具的极简美学**

AEDT 的用户是资深开发者，他们习惯终端操作，追求效率而非华丽。TUI 设计遵循以下原则：

1. **信息密度优先** - 一屏显示尽可能多的有用信息，减少滚动
2. **快捷键至上** - 所有操作都有快捷键，鼠标可选但非必需
3. **即时反馈** - 操作响应 < 200ms，状态变化实时可见
4. **渐进式披露** - 默认显示摘要，按需展开详情
5. **容错设计** - 危险操作需确认，可撤销的尽量可撤销

---

### 视觉风格

**配色方案（类似 htop/lazygit）：**
- **背景**：深色主题（#1e1e1e）
- **主文本**：浅灰色（#d4d4d4）
- **状态指示**：
  - 🟢 绿色 - 完成/成功
  - 🟡 黄色 - 进行中/警告
  - 🔴 红色 - 失败/错误
  - 🔵 蓝色 - 待处理/信息
- **强调**：青色（#00d7ff）用于高亮选中项
- **边框**：暗灰色（#3a3a3a）

**字体与图标：**
- 使用 Unicode 符号和表情符号增强可读性
- 进度条：`[████████░░] 80%`
- 状态图标：`✓` `✗` `⚙` `⏸` `⏳`

**示例界面风格：**
```
╔═══════════════════════════════════════════════════════╗
║  AEDT - AI Enhanced Delivery Toolkit                 ║
║  Projects: 3 | Active: 5 | Completed: 12             ║
╠═══════════════════════════════════════════════════════╣
║  📁 AEDT                           [5 epics]         ║
║  ├─ Epic 1: 多项目管理          ✓ Complete          ║
║  ├─ Epic 2: BMAD 集成           ⚙ Developing 60%    ║
║  ├─ Epic 3: 调度引擎            ⚙ Developing 30%    ║
║  ├─ Epic 4: TUI Dashboard       ⏳ Queued            ║
║  └─ Epic 5: Git 自动化          ⏳ Queued            ║
╚═══════════════════════════════════════════════════════╝
```

---

### 布局设计

**主界面分为 4 个面板：**

```
┌─────────────────────────────────────────────────────┐
│  Header Bar (固定)                                  │
│  Projects: 3 | Active Epics: 5 | Agents: 3          │
├──────────────────┬──────────────────────────────────┤
│                  │                                  │
│  Project List    │  Epic Details                    │
│  (左侧 30%)      │  (右上 70%)                      │
│                  │  - Epic 描述                     │
│  📁 Project A    │  - Story 列表                    │
│  📁 Project B    │  - 依赖关系                      │
│  📁 Project C    │  - Agent 进度                    │
│                  │                                  │
├──────────────────┼──────────────────────────────────┤
│                  │                                  │
│  Agent Activity  │  Logs                            │
│  (左下 30%)      │  (右下 70%)                      │
│                  │                                  │
│  Agent-1 ⚙ 60%  │  [10:23] Epic 2: Story 2 完成    │
│  Agent-2 ⚙ 30%  │  [10:24] Epic 3: 开始 Story 1    │
│  Agent-3 ⏳ 队列  │  [10:25] 警告: 检测到潜在冲突    │
│                  │                                  │
└──────────────────┴──────────────────────────────────┘
│  Footer (快捷键提示)                                │
│  [s]Switch [r]Refresh [/]Search [:]Cmd [q]Quit      │
└─────────────────────────────────────────────────────┘
```

**响应式调整：**
- 终端宽度 < 120 列时，切换为单列布局
- 终端高度 < 24 行时，隐藏日志面板

---

### Key Interactions

### 核心交互流程

**1. 启动与初始化**
```
$ aedt start

→ 检测配置文件
→ 加载所有项目
→ 显示 Dashboard
→ 自动刷新状态（每 5 秒）
```

**用户看到：**
- 所有项目的 Epic 状态
- 正在运行的 Agent
- 最近的日志输出

---

**2. 启动并行开发（最核心的交互）**

**场景：用户完成了 Epic 规划，想启动并行开发**

```
步骤 1: 在 Project List 中选择项目
  按 j/k 导航 → 按 Enter 展开

步骤 2: 在 Epic 列表中选择要启动的 Epic
  按 Space 多选（支持选择多个 Epic）
  或按 a 全选所有可并行的 Epic

步骤 3: 按 Enter 启动
  → AEDT 分析依赖关系
  → 显示确认对话框：
    ┌───────────────────────────────────┐
    │  启动以下 Epic？                  │
    │  ✓ Epic 1 (无依赖)               │
    │  ✓ Epic 2 (无依赖)               │
    │  ✓ Epic 3 (无依赖)               │
    │  ⏳ Epic 4 (依赖 Epic 1，将排队) │
    │                                   │
    │  预计并发: 3 个 Subagent          │
    │  [y] 确认启动  [n] 取消           │
    └───────────────────────────────────┘

步骤 4: 按 y 确认
  → 创建 Git Worktree
  → 启动 Subagent
  → Epic 状态变为 "⚙ Developing"
  → Agent Activity 面板显示进度
```

**即时反馈：**
- Epic 状态从 `⏳ Queued` → `⚙ Developing 0%`
- 进度条实时更新：`[░░░░░░░░░░] 0%` → `[███░░░░░░░] 30%`
- 日志面板滚动显示 Subagent 输出

---

**3. 监控进度**

**自动刷新（每 5 秒）：**
- Epic 进度百分比更新
- Agent 状态同步（如 Story 2/5 完成）
- 日志自动滚动到最新

**手动操作：**
- 按 `r` 立即刷新
- 按 `Enter` 展开 Epic，查看详细 Story 列表：
  ```
  Epic 2: BMAD 集成 [⚙ 60%]
  ├─ Story 1: 读取 Epic 文档     ✓ 完成
  ├─ Story 2: 解析依赖关系       ✓ 完成
  ├─ Story 3: 提取 Story 列表    ⚙ 进行中
  ├─ Story 4: 监听文件变化       ⏳ 待处理
  └─ Story 5: 测试集成           ⏳ 待处理
  ```

- 按 `l` 查看特定 Epic 的完整日志（打开独立日志视图）

---

**4. 处理冲突（人工介入点）**

**场景：AEDT 检测到 Git 冲突**

```
→ TUI 显示红色警告：
  ┌─────────────────────────────────────┐
  │  🔴 冲突检测                        │
  │  Epic 2 与 Epic 3 有文件冲突：      │
  │  - src/parser.py                    │
  │  - src/utils.py                     │
  │                                     │
  │  Epic 2 已完成，等待合并            │
  │  Epic 3 仍在开发中                  │
  │                                     │
  │  建议操作：                         │
  │  1. 暂停 Epic 3 开发                │
  │  2. 手动解决冲突                    │
  │  3. 恢复 Epic 3 开发                │
  │                                     │
  │  [p] 暂停 Epic 3  [i] 忽略  [h] 帮助│
  └─────────────────────────────────────┘
```

**用户按 `p` 暂停：**
- Epic 3 的 Subagent 暂停
- 用户手动解决冲突（在 IDE 或终端）
- 解决后，在 TUI 中按 `Resume` 恢复

---

**5. 查看和切换项目**

**快速切换：**
- 按 `s` 打开项目选择器
- 按 `1`/`2`/`3` 快速切换到项目 1/2/3
- 或使用 `j`/`k` 导航 + `Enter` 选择

**项目视图：**
- 显示所有项目的未完成 Epic 数量
- 高亮推荐的下一步项目
  ```
  📁 AEDT          [5 epics, 3 active] ⭐ 推荐
  📁 Other Project [2 epics, 0 active]
  📁 Demo App      [8 epics, 2 active]
  ```

---

**6. 搜索与过滤**

**按 `/` 进入搜索模式：**
```
Search: auth_

→ 过滤结果：
  Epic 1: User Authentication
  Epic 4: Auth Token Management
  Story 2-3: Implement auth middleware
```

**按 `f` 进入过滤模式：**
```
Filter by:
  [1] Status (developing/queued/complete)
  [2] Priority (high/medium/low)
  [3] Agent (agent-1/agent-2/...)
```

---

**7. 命令模式（高级操作）**

**按 `:` 进入命令模式（类似 Vim）：**

```
:pause epic-2          # 暂停 Epic 2
:resume epic-2         # 恢复 Epic 2
:logs epic-2           # 查看 Epic 2 日志
:clean                 # 清理所有 Worktree
:status                # 显示全局状态
:help                  # 显示帮助
```

---

### 错误与异常处理

**友好的错误提示：**

```
🔴 错误：找不到配置文件

原因：`.aedt/config.yaml` 不存在

建议：
  1. 运行 `aedt init` 初始化配置
  2. 或从示例复制：`cp examples/configs/simple.yaml .aedt/config.yaml`

[i] 现在初始化？ [y/n]
```

**而不是：**
```
FileNotFoundError: [Errno 2] No such file or directory: '.aedt/config.yaml'
  File "aedt/main.py", line 42, in load_config
    with open(config_path) as f:
```

---

### 性能与响应性

**用户期望：**
- 按键响应 < 100ms
- 状态刷新 < 200ms
- 页面切换无闪烁

**实现策略：**
- 异步加载数据（不阻塞 UI）
- 增量更新（只刷新变化的部分）
- 缓存常用数据（项目列表、Epic 元数据）

---

### 可访问性

**虽然是 TUI，仍需考虑可访问性：**

1. **颜色盲友好**
   - 不依赖颜色区分状态（同时使用图标）
   - 支持高对比度模式

2. **屏幕阅读器支持（有限）**
   - 使用语义化文本标签
   - 避免纯图形化符号

3. **键盘导航**
   - 所有功能都可通过键盘访问
   - Tab 顺序符合逻辑

---

### 帮助与引导

**首次启动提示：**
```
👋 欢迎使用 AEDT！

这是您第一次启动。快速教程：

  [h/j/k/l] 导航项目和 Epic
  [Enter]   选择/展开
  [Space]   多选 Epic
  [s]       切换项目
  [r]       刷新状态
  [?]       显示完整帮助

按任意键开始 →
```

**内置帮助（按 `?`）：**
- 显示所有快捷键
- 常见任务步骤
- 链接到在线文档

---

### 设计验证标准

**TUI 设计成功的标准：**

1. **新用户 5 分钟上手**
   - 无需阅读文档，通过界面提示就能完成基本操作
   - 首次启动引导清晰

2. **专家用户无鼠标操作**
   - 所有操作都有快捷键
   - 命令模式支持批量操作

3. **信息密度高但不拥挤**
   - 一屏显示 3 个项目、10+ Epic 状态、5 个 Agent 活动
   - 但仍然清晰易读

4. **即时反馈**
   - 操作响应 < 200ms
   - 状态变化实时可见
   - 没有"加载中"的等待感

5. **容错性强**
   - 危险操作有确认对话框
   - 错误提示友好且可操作
   - 日志完整，方便排查问题

---

## Functional Requirements

### 功能需求概述

AEDT 的功能需求覆盖 **8 个核心能力领域**，共 **58 个功能需求（FRs）**。每个 FR 定义了用户或系统**能做什么**（WHAT），而不是**如何实现**（HOW）。

---

### 1. 项目管理

**FR1** - 用户可以添加多个项目到 AEDT 管理
- 支持通过 CLI 命令添加：`aedt project add <path>`
- 每个项目独立配置和状态

**FR2** - 用户可以查看所有项目的列表和状态
- 显示项目名称、路径、Epic 数量、活跃 Agent 数量
- 支持快速切换项目视图

**FR3** - 用户可以从项目列表中移除项目
- 移除前提示确认
- 保留项目数据（不删除实际文件）

**FR4** - 系统可以智能推荐下一步应该工作的项目
- 基于未完成 Epic 数量、优先级、等待时间等因素
- 在 TUI 中高亮推荐项目

**FR5** - 用户可以为每个项目配置工作流类型
- 初始支持 BMAD 工作流
- 预留扩展接口支持其他工作流（Spec-Kit、自定义）

---

### 2. Epic 管理与依赖分析

**FR6** - 系统可以自动读取和解析项目的 Epic 文档
- 从 `docs/epics/*.md` 读取 Epic 定义
- 解析 YAML frontmatter 提取元数据（标题、描述、依赖等）

**FR7** - 系统可以提取 Epic 之间的依赖关系
- 从 Epic 元数据中解析 `depends_on` 字段
- 构建依赖关系图（DAG）

**FR8** - 系统可以自动识别可并行的 Epic
- 分析 DAG，识别无依赖或依赖已完成的 Epic
- 标记为"可并行"状态

**FR9** - 系统可以自动排队有依赖的 Epic
- 依赖未完成的 Epic 进入等待队列
- 依赖完成后自动从队列移出，变为"可并行"

**FR10** - 用户可以查看 Epic 的依赖关系
- 在 TUI 中展开 Epic 时显示依赖列表
- 显示依赖状态（已完成/进行中/待处理）

**FR11** - 用户可以手动标记 Epic 的优先级
- 支持高/中/低三级优先级
- 高优先级 Epic 在调度时优先启动

**FR12** - 系统可以监听 Epic 文档变化并自动刷新
- 使用文件监听机制（watchdog）
- Epic 文档更新后自动重新解析

---

### 3. Story 管理

**FR13** - 系统可以解析每个 Epic 中的 Story 列表
- 从 Epic 文档中提取 Story 定义
- 每个 Story 作为独立的开发任务

**FR14** - 用户可以查看 Epic 的所有 Story 及其状态
- 在 TUI 中展开 Epic 时显示 Story 列表
- 显示每个 Story 的状态（完成/进行中/待处理）

**FR15** - 系统可以追踪每个 Story 的开发进度
- Subagent 完成一个 Story 后更新状态
- 计算 Epic 整体进度百分比（已完成 Story 数 / 总 Story 数）

---

### 4. 并行调度与 Subagent 编排

**FR16** - 用户可以选择一个或多个 Epic 启动并行开发
- 支持多选（Space 键）
- 支持全选所有可并行的 Epic（a 键）

**FR17** - 系统可以在启动前显示依赖关系和并发计划
- 确认对话框显示将启动的 Epic、排队的 Epic、预计并发数
- 用户确认后才执行

**FR18** - 系统可以为每个 Epic 创建独立的 Git Worktree
- 自动生成分支名称：`epic-{epic-id}`
- 工作目录：`.aedt/worktrees/epic-{id}/`

**FR19** - 系统可以使用 Claude Code Task 工具启动 Subagent
- 为每个 Epic 启动独立的 Subagent
- 传递 Epic 描述、Story 列表、依赖信息作为上下文

**FR20** - 系统可以控制最大并发 Subagent 数量
- 默认最多 5 个并发
- 可在配置文件中调整：`subagent.max_concurrent`

**FR21** - 系统可以将超出并发限制的 Epic 自动排队
- 当前并发数达到上限时，新 Epic 进入队列
- 有 Subagent 完成后自动启动队列中的下一个

**FR22** - 系统可以监听 Subagent 的输出和进度
- 解析 Subagent 日志，识别 Story 完成事件
- 实时更新 Epic 进度

**FR23** - 用户可以手动暂停正在进行的 Epic
- 停止对应的 Subagent
- 保留 Worktree 和当前进度

**FR24** - 用户可以恢复被暂停的 Epic
- 重新启动 Subagent
- 从暂停点继续开发

**FR25** - 系统可以在 Epic 依赖完成后自动启动等待中的 Epic
- 无需用户手动触发
- 自动调度，充分利用并发能力

---

### 5. Git 自动化

**FR26** - 系统可以自动创建 Epic 分支
- 从主分支（main/master）创建新分支
- 分支命名遵循配置规则

**FR27** - 系统可以自动管理 Git Worktree 的生命周期
- Epic 启动时创建 Worktree
- Epic 合并后删除 Worktree

**FR28** - Subagent 可以在独立 Worktree 中进行开发
- 每个 Subagent 在自己的 Worktree 目录工作
- 相互隔离，避免文件冲突

**FR29** - Subagent 可以在每个 Story 完成后自动提交
- 逐个 Story 提交，不是整个 Epic 一次性提交
- 减少冲突，提高可追溯性

**FR30** - 系统可以在 Epic 完成后自动合并到主分支
- 检测无冲突时自动合并
- 合并后通知用户

**FR31** - 系统可以在合并前检测潜在冲突
- 分析多个 Epic 修改的文件
- 发现重叠时警告用户

**FR32** - 系统可以在检测到冲突时暂停自动合并
- 通知用户手动解决冲突
- 提供冲突文件列表和建议操作

**FR33** - 用户可以手动触发冲突解决流程
- 在 TUI 中选择冲突的 Epic
- 查看冲突详情，暂停相关 Epic

**FR34** - 系统可以在用户解决冲突后恢复合并流程
- 用户标记冲突已解决
- 系统继续合并

**FR35** - 用户可以手动清理所有 Worktree
- CLI 命令：`aedt clean`
- 删除所有 `.aedt/worktrees/` 目录

---

### 6. 质量门控

**FR36** - 系统可以在每个 Story 提交前运行代码检查
- 执行 linter（如 pylint、eslint）
- 执行格式检查（如 black、prettier）

**FR37** - 系统可以在 Epic 完成时运行单元测试
- 执行项目配置的测试命令
- 测试失败时暂停合并

**FR38** - 系统可以在合并前运行完整测试套件
- 包括集成测试、端到端测试（如果配置）
- 测试失败时阻止合并

**FR39** - 用户可以配置自定义质量门控规则
- 在 `.aedt/config.yaml` 中定义检查命令
- 支持多级门控（pre_commit、epic_complete、pre_merge）

**FR40** - 系统可以在质量检查失败时通知用户
- TUI 显示失败原因
- 提供日志查看入口

---

### 7. TUI Dashboard 与可视化

**FR41** - 用户可以启动 TUI Dashboard 查看全局状态
- CLI 命令：`aedt start`
- 实时显示所有项目、Epic、Agent 状态

**FR42** - TUI 可以实时刷新 Epic 和 Agent 状态
- 自动刷新（每 5 秒）
- 手动刷新快捷键（r）

**FR43** - 用户可以在 TUI 中导航项目和 Epic
- Vim 风格快捷键（hjkl）
- 展开/折叠 Epic（Enter）

**FR44** - 用户可以在 TUI 中查看 Epic 详情
- Epic 描述
- Story 列表及状态
- 依赖关系
- Agent 进度

**FR45** - 用户可以在 TUI 中查看实时日志
- 显示所有 Subagent 的输出
- 自动滚动到最新
- 支持查看单个 Epic 的日志（l 键）

**FR46** - 用户可以在 TUI 中查看 Agent 活动面板
- 显示所有活跃 Agent 的 ID、关联 Epic、进度
- 显示队列中的 Agent

**FR47** - 用户可以在 TUI 中搜索 Epic
- 搜索模式（/ 键）
- 支持模糊匹配

**FR48** - 用户可以在 TUI 中过滤 Epic
- 按状态过滤（developing/queued/complete）
- 按优先级过滤
- 按 Agent 过滤

**FR49** - 用户可以在 TUI 中切换项目
- 快捷键（s）打开项目选择器
- 数字键快速切换（1/2/3）

**FR50** - 用户可以通过命令模式执行高级操作
- Vim 风格命令模式（: 键）
- 支持命令：pause、resume、logs、clean、status、help

**FR51** - TUI 可以在首次启动时显示引导教程
- 检测首次使用
- 显示快捷键提示
- 提供跳过选项

**FR52** - 用户可以在 TUI 中查看完整帮助
- 帮助快捷键（?）
- 显示所有快捷键和命令
- 链接到在线文档

---

### 8. 配置与状态管理

**FR53** - 系统可以初始化 AEDT 配置
- CLI 命令：`aedt init`
- 生成默认配置文件：`.aedt/config.yaml`

**FR54** - 系统可以持久化项目和 Epic 状态
- YAML 格式存储：`.aedt/projects/{project-name}/status.yaml`
- 包括 Epic 状态、进度、Agent ID、Worktree 路径等

**FR55** - 系统可以在重启后恢复所有项目状态
- 读取持久化的状态文件
- 恢复 Epic 进度、Agent 状态（但不恢复运行中的 Agent）

**FR56** - 用户可以通过配置文件自定义 AEDT 行为
- Subagent 参数（并发数、超时、模型）
- 质量门控规则
- Git 配置（Worktree 路径、分支前缀）

**FR57** - 系统可以生成结构化日志
- 日志文件：`.aedt/logs/aedt.log`
- 分级日志（DEBUG、INFO、WARNING、ERROR）
- 每个 Epic 的独立日志：`.aedt/projects/{project}/epics/epic-{id}.log`

**FR58** - 用户可以查看非交互式的全局状态摘要
- CLI 命令：`aedt status`
- 输出所有项目的 Epic 状态、Agent 活动、下一步建议

---

### 功能需求完整性验证

**覆盖检查：**
- ✅ MVP 9 大功能模块全部覆盖
- ✅ TUI 7 个核心交互流程全部覆盖
- ✅ Developer Tool 需求全部覆盖
- ✅ 成功标准中的所有能力全部覆盖

**能力领域分布：**
1. 项目管理 - 5 个 FR
2. Epic 管理与依赖分析 - 7 个 FR
3. Story 管理 - 3 个 FR
4. 并行调度与 Subagent 编排 - 10 个 FR
5. Git 自动化 - 10 个 FR
6. 质量门控 - 5 个 FR
7. TUI Dashboard 与可视化 - 12 个 FR
8. 配置与状态管理 - 6 个 FR

**总计：58 个功能需求**

---

### 高度验证（WHAT vs HOW）

**验证每个 FR 是否在正确的高度：**

✅ **正确示例**（WHAT）：
- FR16: "用户可以选择一个或多个 Epic 启动并行开发"
- FR30: "系统可以在 Epic 完成后自动合并到主分支"

❌ **错误示例**（HOW - 如果存在）：
- ~~"系统使用 GitPython 库执行 git worktree add 命令"~~ ← 这是实现细节

**结论：所有 FR 都在正确的高度，定义能力而非实现。**

---

## Non-Functional Requirements

### 非功能需求概述

AEDT 的非功能需求聚焦于**用户体验质量**和**系统可靠性**。作为开发者工具，性能和响应性至关重要。

---

### 1. 性能要求

**NFR1 - TUI 响应性**
- 按键响应延迟 < 100ms
- 用户操作（导航、展开、搜索）必须即时反馈
- 没有明显的卡顿或等待

**NFR2 - 状态刷新性能**
- 自动刷新周期：每 5 秒
- 刷新操作延迟 < 200ms
- 增量更新，不全量重绘界面

**NFR3 - 页面切换流畅性**
- 项目切换无闪烁
- 面板切换无卡顿
- 使用异步加载，不阻塞 UI 主线程

**NFR4 - 日志处理性能**
- 支持实时滚动显示 Subagent 日志
- 日志缓冲区限制：最多保留最近 1000 行（内存中）
- 完整日志写入文件，不影响 TUI 性能

**NFR5 - 文件监听性能**
- Epic 文档变化检测延迟 < 1 秒
- 使用 watchdog 高效监听，不轮询
- 避免重复触发（debounce 机制）

**NFR6 - 大规模项目支持**
- 支持同时管理 5-10 个项目
- 每个项目支持 50+ Epic
- 总计 100+ Epic 时仍保持流畅（TUI 响应 < 200ms）

**NFR7 - Subagent 启动速度**
- Epic 启动到 Subagent 开始工作 < 10 秒
- 包括 Git Worktree 创建、上下文传递、Agent 初始化
- 并行启动多个 Subagent 时，每个独立计时

---

### 2. 可靠性与稳定性

**NFR8 - 崩溃恢复**
- AEDT 主进程崩溃后，重启时自动恢复所有项目状态
- Epic 进度、Worktree 路径、配置不丢失
- Subagent 进程独立，AEDT 崩溃不影响 Subagent 继续运行

**NFR9 - Subagent 异常处理**
- Subagent 崩溃或超时后，AEDT 记录错误并通知用户
- 不自动重启失败的 Subagent（避免无限循环）
- 提供手动重试选项

**NFR10 - Git 操作容错**
- Git Worktree 创建失败时，回滚操作并清理
- 合并冲突检测失败时，暂停合并，不强制执行
- 提供清理命令（`aedt clean`）手动修复异常状态

**NFR11 - 数据持久化可靠性**
- 状态文件每次更新时原子写入（写入临时文件 → 重命名）
- 避免部分写入导致的数据损坏
- 状态文件格式使用 YAML（人类可读，便于手动修复）

**NFR12 - 网络容错**
- Claude Code API 调用失败时，重试 3 次（指数退避）
- 超时设置：单次 API 调用 60 秒
- 失败后通知用户，不静默失败

---

### 3. 可用性与用户体验

**NFR13 - 学习曲线**
- 新用户无需阅读文档，通过首次启动引导 + TUI 提示，5 分钟内完成第一次并行开发
- 界面提示清晰，快捷键在 Footer 显示

**NFR14 - 错误提示友好性**
- 所有错误提示使用自然语言，而非技术堆栈跟踪
- 提供建议操作（"运行 `aedt init` 初始化"）
- 错误可操作，而非只读信息

**NFR15 - 帮助系统完整性**
- TUI 内置帮助（? 键）覆盖所有快捷键和命令
- 每个命令都有简短描述
- 链接到在线文档（README、GitHub Wiki）

**NFR16 - 多语言支持（Phase 2+）**
- MVP 仅支持英文界面
- Phase 2 支持中文界面（配置文件切换）
- 日志和错误信息国际化

---

### 4. 可维护性与扩展性

**NFR17 - 代码模块化**
- 核心模块独立：项目管理、Epic 解析、调度引擎、Git 操作、TUI 渲染
- 每个模块有清晰的接口，便于单元测试
- 依赖注入，避免硬编码

**NFR18 - 插件化架构**
- 工作流适配器使用插件接口（`WorkflowAdapter` 抽象类）
- BMAD 适配器作为内置插件
- Phase 2 支持外部插件（从配置加载）

**NFR19 - 配置驱动**
- 所有行为通过配置文件控制（`.aedt/config.yaml`）
- 不硬编码路径、命令、参数
- 配置文件有清晰的注释和示例

**NFR20 - 日志完整性**
- 分级日志（DEBUG、INFO、WARNING、ERROR）
- 每个关键操作都有日志记录（Epic 启动、Subagent 启动、Git 操作、合并等）
- 日志可追溯，便于排查问题

**NFR21 - 测试覆盖率**
- 核心模块单元测试覆盖率 > 80%
- 集成测试覆盖主要工作流（启动 Epic、合并、冲突检测）
- TUI 交互测试（使用 Textual 测试框架）

---

### 5. 安全性

**NFR22 - 凭证安全**
- Claude Code API 密钥从环境变量读取（不存储在配置文件）
- 配置文件中不包含敏感信息
- `.aedt/` 目录添加到 `.gitignore`，避免意外提交

**NFR23 - 文件系统权限**
- 只读取用户明确添加的项目目录
- 不修改项目根目录外的文件
- Worktree 创建在 `.aedt/worktrees/`，隔离在项目内

**NFR24 - Git 操作安全**
- 不运行 `git push --force`、`git reset --hard` 等危险命令
- 合并前强制检测冲突
- 提供 `aedt clean` 清理命令，不自动删除用户数据

**NFR25 - 依赖安全**
- 使用成熟的第三方库（Textual、GitPython、PyYAML）
- 定期更新依赖，修复安全漏洞
- 依赖锁定（`requirements.txt` 或 `poetry.lock`）

---

### 6. 兼容性

**NFR26 - 平台支持**
- MVP 支持 macOS、Linux
- Python 3.10+ 兼容
- Phase 2 支持 Windows（需测试 Git Worktree 兼容性）

**NFR27 - 终端兼容性**
- 支持主流终端模拟器（iTerm2、Terminal.app、GNOME Terminal、Alacritty）
- 最小终端尺寸：80 列 × 24 行
- 响应式布局适配不同终端尺寸

**NFR28 - Git 版本兼容性**
- 要求 Git 2.25+（Worktree 功能稳定版本）
- 检测 Git 版本，不支持时提示升级

**NFR29 - Claude Code 兼容性**
- 支持 Claude Code Task 工具（当前 API）
- 如果 API 变更，提供适配层
- 预留接口支持其他 AI 编码工具（Cursor、Windsurf）

---

### 7. 性能基准（可测量指标）

**基准测试场景：**

**场景 1：启动 TUI**
- 操作：运行 `aedt start`，加载 3 个项目，每个项目 10 个 Epic
- 期望：TUI 显示 < 2 秒

**场景 2：并行启动 5 个 Epic**
- 操作：选择 5 个无依赖 Epic，启动并行开发
- 期望：5 个 Subagent 全部启动 < 30 秒

**场景 3：状态刷新**
- 操作：自动刷新所有项目状态（30 个 Epic）
- 期望：刷新延迟 < 200ms，TUI 无卡顿

**场景 4：日志滚动**
- 操作：5 个 Subagent 同时输出日志，TUI 实时显示
- 期望：日志滚动流畅，无明显延迟（< 500ms）

**场景 5：搜索 Epic**
- 操作：在 100 个 Epic 中搜索关键词
- 期望：搜索结果显示 < 100ms

---

### 8. 可观测性

**NFR30 - 日志可追溯性**
- 每个操作有唯一 ID（Epic ID、Agent ID）
- 日志包含时间戳、操作类型、结果
- 可根据 Epic ID 过滤日志

**NFR31 - 状态可视化**
- TUI 实时显示所有 Epic 状态、Agent 活动、队列情况
- 提供非交互式状态命令（`aedt status`）便于脚本调用

**NFR32 - 错误追踪**
- 所有异常都记录到日志文件
- 包含完整堆栈跟踪（DEBUG 模式）
- 生产模式仅显示友好错误，堆栈写入日志

---

### 非功能需求总结

**优先级分类：**

**P0（MVP 必须）：**
- 性能：NFR1-7（TUI 响应、刷新、日志处理）
- 可靠性：NFR8-12（崩溃恢复、容错、数据持久化）
- 可用性：NFR13-15（学习曲线、错误提示、帮助）
- 安全性：NFR22-24（凭证安全、文件权限、Git 安全）
- 兼容性：NFR26-28（平台、终端、Git 版本）

**P1（Phase 2）：**
- 可维护性：NFR17-21（模块化、插件化、测试覆盖）
- 可观测性：NFR30-32（日志追溯、状态可视化、错误追踪）
- 多语言支持：NFR16

**总计：32 个非功能需求**

---

---

## PRD 总结

### 文档完整性

本 PRD 完整定义了 AEDT (AI-Enhanced Delivery Toolkit) 的产品需求，包括：

**核心内容：**
- ✅ 愿景与价值主张
- ✅ 项目分类（Developer Tool，General Domain，Medium Complexity）
- ✅ 成功标准（Dogfooding 验证，3-5 倍提速）
- ✅ 产品范围（MVP、Growth、Vision 清晰边界）
- ✅ Developer Tool 特定需求（安装、文档、示例、DX）
- ✅ UX 原则（TUI 设计哲学、7 个核心交互流程）
- ✅ **58 个功能需求（FRs）** - 定义所有能力
- ✅ **32 个非功能需求（NFRs）** - 定义质量属性

**需求统计：**
- 功能需求：58 个，覆盖 8 个能力领域
- 非功能需求：32 个，覆盖 8 个质量维度
- MVP 范围：9 大功能模块
- TUI 交互流程：7 个核心场景

---

### 核心价值重申

**AEDT 要解决的问题：**
AI 辅助开发工作流（BMAD、Spec-Kit）虽然提升了单个 Epic 的开发速度，但强制串行执行导致整体 MVP 交付仍然慢。开发者被迫等待一个 Epic 完成才能启动下一个，即使它们没有依赖关系。

**AEDT 的解决方案：**
智能并行编排引擎，自动识别可并行的 Epic，同时启动多个 Subagent，配合 Git Worktrees 隔离和自动合并，让开发者充分利用 AI 的并行能力。

**MVP 成功标准：**
用 AEDT 完成 2-3 个真实 MVP 项目，每个项目 10+ Epic，开发速度提升 3-5 倍，自己每天都愿意使用。

---

### 下一步行动

**基于本 PRD，后续工作流：**

1. **✅ PRD 验证（可选）**
   - 运行 PM agent 的 `*validate-prd` 工作流
   - 检查 PRD 完整性和质量

2. **UX 设计（推荐）**
   - 运行 UX Designer agent 的 `*create-design` 工作流
   - 设计 TUI 详细界面和交互流程
   - 输出：UX 设计文档

3. **架构设计（必须）**
   - 运行 Architect agent 的 `*create-architecture` 工作流
   - 定义技术架构、模块设计、数据模型
   - 输出：架构文档

4. **Epic 分解（必须）**
   - 运行 PM agent 的 `*create-epics-and-stories` 工作流
   - 将 PRD 的功能需求分解为可实现的 Epic 和 Story
   - 输出：Epic 文档（`docs/epics/epic-*.md`）

5. **实现准备（必须）**
   - 运行 Architect agent 的 `*implementation-readiness` 工作流
   - 验证 PRD + 架构 + Epic 的一致性
   - 输出：准备就绪报告

6. **Sprint 规划（必须）**
   - 运行 Scrum Master agent 的 `*sprint-planning` 工作流
   - 规划第一个 Sprint
   - 输出：Sprint 计划

---

### 关键风险与假设

**技术假设（需要 Phase 0 验证）：**
1. ✅ Claude Code Task 工具能启动 Subagent 并传递足够上下文
2. ✅ Git Worktrees 支持 5 个并发，性能可接受
3. ✅ BMAD Epic 文档包含依赖关系元数据（或可手动标注）
4. ⚠️ Subagent 开发进度可从输出解析（可能需要 Agent 主动报告）

**产品假设：**
1. ✅ 目标用户（资深开发者）习惯 TUI 操作
2. ✅ 并行编排能显著提升开发速度（3-5 倍）
3. ✅ 自动化 Git 操作不会引入过多冲突

**建议 Phase 0 行动（验证假设）：**
- 实验 Claude Code Task 工具启动 Subagent
- 测试 Git Worktrees 并发性能
- 查看 BMAD Epic 文档格式，确认依赖关系
- 搭建 Textual TUI Hello World

---

_本 PRD 捕获了 AEDT 的核心愿景：**将 AI 辅助开发从单线程串行升级到智能并行编排，让 MVP 交付速度提升 3-5 倍**。_

_通过 BMad 与 AI 协作完成，2025-11-23。_
