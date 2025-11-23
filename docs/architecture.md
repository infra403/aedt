# AEDT 系统架构文档

**项目：** AEDT (AI-Enhanced Delivery Toolkit)
**作者：** BMad
**日期：** 2025-11-23
**版本：** 1.0

---

## 1. 架构概览

### 1.1 系统定位和目标

AEDT 是一个智能 AI 开发编排引擎，专为资深独立开发者和技术创业者设计。它将 AI 辅助开发工作流从"单线程串行"升级到"智能并行编排"，通过自动化依赖调度、Git Worktree 隔离和实时 TUI Dashboard，实现 MVP 交付速度提升 3-5 倍。

**核心目标：**
- 自动识别可并行的 Epic，最多同时运行 5 个 Subagent
- 提供统一的多项目管理 Dashboard，智能推荐下一步行动
- 实现 Git 操作 100% 自动化（分支管理、自动合并、冲突检测）
- 通过终端 TUI 实时可视化所有 Epic 状态和 Agent 进度
- 自动化质量门控，确保代码质量

**系统定位：**
- **类型：** 开发者工具（Developer Tool）
- **领域：** 通用软件开发（AI 辅助开发工作流编排）
- **复杂度：** 中等（Medium）- 涉及多进程管理、Git 自动化、依赖调度
- **部署模式：** 本地命令行工具（CLI + TUI）

### 1.2 架构原则

**1. 模块化与职责分离**
- 每个核心模块职责单一，接口清晰
- 使用依赖注入，避免硬编码
- 便于单元测试和独立演进

**2. 可靠性优先**
- 崩溃恢复：主进程崩溃后自动恢复所有项目状态
- 数据持久化：状态文件原子写入，避免数据损坏
- 容错设计：Git 操作失败时自动回滚，提供清理命令

**3. 性能与响应性**
- TUI 响应延迟 < 200ms
- 异步处理，不阻塞 UI 主线程
- 增量更新，只刷新变化的部分

**4. 可扩展性**
- 工作流适配器插件化，预留扩展接口
- 配置驱动，所有行为通过配置文件控制
- 支持自定义质量门控规则

**5. 用户友好**
- 友好的错误提示，而非技术堆栈跟踪
- 内置帮助系统，快捷键提示
- 5 分钟上手，无需阅读完整文档

**6. 安全性**
- API 密钥从环境变量读取，不存储在配置文件
- 只读取用户明确添加的项目目录
- 不运行危险 Git 命令（force push、hard reset）

### 1.3 技术栈总览

**编程语言：** Python 3.10+
- 成熟的 TUI 框架（Textual）
- 丰富的 YAML/文件处理库
- 快速迭代，适合 MVP 开发

**核心依赖：**
```python
textual>=6.6.0           # TUI 框架
GitPython>=3.1.0         # Git 操作
PyYAML>=6.0              # YAML 配置解析
watchdog>=3.0.0          # 文件监听
pytest>=7.0.0            # 测试框架
```

**运行环境：**
- **平台：** macOS、Linux（MVP），Windows（Phase 2）
- **Git 版本：** Git 2.25+（Worktree 功能稳定版本）
- **终端：** iTerm2、Terminal.app、GNOME Terminal、Alacritty
- **最小终端尺寸：** 80 列 × 24 行

**外部工具：**
- **Claude Code Task 工具：** 启动 Subagent
- **Git CLI：** 通过 GitPython 调用 git worktree 命令
- **Linter/Formatter：** 项目配置的代码检查工具（pylint、black 等）
- **测试框架：** 项目配置的测试命令（pytest、unittest 等）

---

## 2. 系统架构

### 2.1 高层架构图（文字描述）

AEDT 采用**分层架构 + 模块化设计**，包含以下层次：

```
┌─────────────────────────────────────────────────────────────┐
│                     用户交互层 (User Interface Layer)          │
│  - TUI Dashboard (Textual)                                   │
│  - CLI 命令 (aedt init/start/status/clean)                   │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    应用逻辑层 (Application Layer)              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ 项目管理     │  │ Epic 解析    │  │ 调度引擎     │          │
│  │ ProjectMgr  │  │ EpicParser  │  │ Scheduler   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Subagent    │  │ 质量门控     │  │ 状态管理     │          │
│  │ Orchestrator│  │ QualityGate │  │ StateMgr    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                   基础设施层 (Infrastructure Layer)            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Git Worktree│  │ 文件监听     │  │ 日志系统     │          │
│  │ Manager     │  │ FileWatcher │  │ Logger      │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────┐  ┌─────────────┐                           │
│  │ 配置管理     │  │ 数据持久化   │                           │
│  │ ConfigMgr   │  │ DataStore   │                           │
│  └─────────────┘  └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    外部系统 (External Systems)                 │
│  - Claude Code Task 工具                                      │
│  - Git CLI (git worktree)                                     │
│  - 项目测试框架 (pytest/unittest)                              │
│  - 代码检查工具 (pylint/black)                                 │
└─────────────────────────────────────────────────────────────┘
```

**架构特点：**
- **分层清晰：** UI 层、应用逻辑层、基础设施层各司其职
- **模块独立：** 每个模块可独立测试和替换
- **异步驱动：** 使用 asyncio 处理并发，不阻塞 UI
- **事件驱动：** 文件监听、状态变化触发事件，模块间解耦

### 2.2 核心模块划分

AEDT 包含以下 9 个核心模块：

| 模块名称 | 职责 | 主要类/接口 |
|---------|------|------------|
| **ProjectManager** | 项目管理 | `ProjectManager`, `Project` |
| **EpicParser + DependencyAnalyzer** | Epic 解析与依赖分析 | `EpicParser`, `DependencyAnalyzer`, `Epic`, `Story` |
| **Scheduler** | 调度引擎 | `Scheduler`, `DAG`, `ScheduleQueue` |
| **SubagentOrchestrator** | Subagent 编排 | `SubagentOrchestrator`, `Subagent`, `TaskRunner` |
| **WorktreeManager** | Git Worktree 管理 | `WorktreeManager`, `Worktree` |
| **QualityGate** | 质量门控 | `QualityGate`, `GateRule`, `TestRunner` |
| **TUIApp** | TUI Dashboard | `TUIApp`, `ProjectPanel`, `EpicPanel`, `LogPanel` |
| **StateManager** | 状态管理 | `StateManager`, `ProjectState`, `EpicState` |
| **FileWatcher** | 文件监听 | `FileWatcher`, `ChangeHandler` |

### 2.3 模块交互关系

**核心工作流：启动并行开发**

```
用户在 TUI 中选择 Epic → TUIApp
                          ↓
TUIApp 调用 Scheduler.start_epics(epic_ids)
                          ↓
Scheduler 分析依赖 → DependencyAnalyzer.get_parallel_epics()
                          ↓
Scheduler 为每个 Epic 调用 WorktreeManager.create_worktree()
                          ↓
Scheduler 调用 SubagentOrchestrator.start_agent(epic)
                          ↓
SubagentOrchestrator 启动 Claude Code Task
                          ↓
Subagent 在 Worktree 中开发 → 每个 Story 提交
                          ↓
SubagentOrchestrator 监听进度 → 更新 StateManager
                          ↓
StateManager 通知 TUIApp → 实时刷新界面
                          ↓
Epic 完成 → QualityGate 运行测试
                          ↓
测试通过 → WorktreeManager.merge_to_main()
                          ↓
合并成功 → WorktreeManager.cleanup_worktree()
                          ↓
StateManager 持久化最终状态
```

**模块依赖关系：**

```
TUIApp
  ├── ProjectManager
  ├── Scheduler
  │   ├── DependencyAnalyzer
  │   ├── SubagentOrchestrator
  │   ├── WorktreeManager
  │   └── QualityGate
  ├── StateManager
  └── FileWatcher

StateManager
  └── DataStore (YAML 文件)

SubagentOrchestrator
  └── Claude Code Task 工具

WorktreeManager
  └── GitPython

QualityGate
  └── 项目测试框架
```

---

## 3. 核心模块设计

### 3.1 项目管理模块 (ProjectManager)

**职责：**
- 管理多个项目的生命周期（添加、移除、列出）
- 提供项目切换和智能推荐功能
- 维护项目配置（工作流类型、路径、设置）

**主要类/接口：**

```python
class Project:
    """项目数据模型"""
    id: str                    # 项目唯一 ID
    name: str                  # 项目名称
    path: str                  # 项目根目录路径
    workflow_type: str         # 工作流类型（bmad/spec-kit/custom）
    config: dict               # 项目特定配置
    epics: List[Epic]          # Epic 列表
    created_at: datetime
    updated_at: datetime

class ProjectManager:
    """项目管理器"""

    def add_project(self, path: str, workflow: str) -> Project:
        """添加项目"""
        pass

    def remove_project(self, project_id: str) -> bool:
        """移除项目"""
        pass

    def list_projects(self) -> List[Project]:
        """列出所有项目"""
        pass

    def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        pass

    def recommend_next_project(self) -> Optional[Project]:
        """智能推荐下一步工作的项目"""
        # 基于未完成 Epic 数量、优先级、等待时间等因素
        pass
```

**与其他模块的交互：**
- **TUIApp:** 提供项目列表给 UI 显示
- **EpicParser:** 为每个项目解析 Epic 文档
- **StateManager:** 持久化项目配置和状态
- **FileWatcher:** 监听项目目录变化

**关键技术决策：**
- 项目使用唯一 ID（基于路径 hash），避免路径变化导致的问题
- 工作流类型可配置，预留插件化接口
- 推荐算法基于简单规则（MVP），Phase 2 可引入机器学习

---

### 3.2 Epic 解析与依赖分析模块 (EpicParser + DependencyAnalyzer)

**职责：**
- 从项目目录读取和解析 Epic 文档
- 提取 Epic 元数据（标题、描述、依赖、优先级）
- 解析 Story 列表
- 构建 Epic 依赖关系图（DAG）
- 识别可并行的 Epic

**主要类/接口：**

```python
class Epic:
    """Epic 数据模型"""
    id: str                    # Epic ID
    title: str                 # 标题
    description: str           # 描述
    depends_on: List[str]      # 依赖的 Epic ID 列表
    priority: str              # 优先级（high/medium/low）
    stories: List[Story]       # Story 列表
    status: str                # 状态（queued/developing/completed/failed）
    progress: float            # 进度百分比（0-100）
    agent_id: Optional[str]    # 关联的 Subagent ID
    worktree_path: Optional[str]  # Worktree 路径
    created_at: datetime
    updated_at: datetime

class Story:
    """Story 数据模型"""
    id: str                    # Story ID
    title: str                 # 标题
    description: str           # 描述
    status: str                # 状态（pending/in_progress/completed/failed）
    commit_hash: Optional[str] # 提交哈希

class EpicParser:
    """Epic 文档解析器"""

    def parse_epics(self, project: Project) -> List[Epic]:
        """解析项目的所有 Epic"""
        # 从 docs/epics/*.md 读取
        # 解析 YAML frontmatter 提取元数据
        pass

    def parse_stories(self, epic: Epic) -> List[Story]:
        """解析 Epic 的 Story 列表"""
        # 从 Epic 文档中提取 Story
        pass

    def watch_epic_changes(self, project: Project, callback: Callable):
        """监听 Epic 文档变化"""
        pass

class DependencyAnalyzer:
    """依赖关系分析器"""

    def build_epic_dag(self, epics: List[Epic]) -> DAG:
        """构建 Epic 依赖关系图（有向无环图）"""
        pass

    def build_story_dag(self, stories: List[Story]) -> DAG:
        """构建 Story 依赖关系图（multi 模式）"""
        # 基于 Story.prerequisites 字段构建 DAG
        pass

    def get_parallel_epics(self, dag: DAG, completed: List[str]) -> List[Epic]:
        """获取可并行的 Epic"""
        # 无依赖或依赖已完成的 Epic
        pass

    def get_parallel_stories(self, dag: DAG, completed: List[str]) -> List[Story]:
        """获取可并行的 Story（multi 模式）"""
        # 无依赖或依赖已完成的 Story
        pass

    def get_queued_epics(self, dag: DAG, completed: List[str]) -> List[Epic]:
        """获取排队等待的 Epic"""
        # 依赖未完成的 Epic
        pass

    def validate_dag(self, dag: DAG) -> bool:
        """验证 DAG（检测循环依赖）"""
        pass
```

**与其他模块的交互：**
- **ProjectManager:** 从项目路径读取 Epic 文档
- **Scheduler:** 提供依赖分析结果用于调度
- **FileWatcher:** 接收 Epic 文档变化事件
- **StateManager:** 持久化 Epic 状态

**关键技术决策：**
- **Epic 格式扩展：** 在 BMAD Epic frontmatter 中添加 `depends_on` 字段
  ```yaml
  ---
  epic_id: 2
  title: "BMAD 工作流集成"
  depends_on: [1]  # 依赖 Epic 1
  priority: high
  ---
  ```
- **DAG 实现：** 使用字典存储邻接表，支持拓扑排序
- **循环依赖检测：** 使用 DFS（深度优先搜索）检测循环
- **Story 解析：** 从 Epic Markdown 文档中提取列表项或章节

---

### 3.3 调度引擎模块 (Scheduler)

**职责：**
- 管理 Epic 的启动、暂停、恢复、完成
- 控制最大并发 Subagent 数量（Epic-level 和 Story-level）
- 管理队列，依赖完成后自动启动等待的 Epic/Story
- 协调 Worktree 创建、Subagent 启动、质量门控
- 根据 Epic 规模自动选择执行模式（single/multi）

**主要类/接口：**

```python
class DAG:
    """依赖关系图"""
    nodes: Dict[str, Epic]        # 节点（Epic ID → Epic）
    edges: Dict[str, List[str]]   # 边（Epic ID → 依赖的 Epic ID 列表）

    def topological_sort(self) -> List[Epic]:
        """拓扑排序"""
        pass

    def has_cycle(self) -> bool:
        """检测循环依赖"""
        pass

class ScheduleQueue:
    """调度队列"""
    running: List[str]            # 运行中的 Epic ID
    queued: List[str]             # 排队的 Epic ID
    max_concurrent: int           # 最大并发数

    def can_start(self) -> bool:
        """是否可以启动新 Epic"""
        return len(self.running) < self.max_concurrent

    def next_epic(self) -> Optional[str]:
        """获取下一个可启动的 Epic"""
        pass

class Scheduler:
    """调度引擎"""

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.queue = ScheduleQueue()
        self.dag: Optional[DAG] = None

    def determine_execution_mode(self, epic: Epic) -> str:
        """自动判断 Epic 执行模式"""
        if epic.execution_mode != "auto":
            return epic.execution_mode

        # 自动判断：Story 数量 <= 5 使用 single，否则 multi
        return "single" if len(epic.stories) <= 5 else "multi"

    def start_epics(self, epic_ids: List[str]) -> Dict[str, str]:
        """启动 Epic（批量）"""
        # 1. 分析依赖关系
        # 2. 识别可并行 Epic
        # 3. 为每个 Epic 判断执行模式
        # 4. 创建 Worktree
        # 5. 根据模式启动 Subagent
        # 6. 排队剩余 Epic
        pass

    def start_epic_single_mode(self, epic: Epic):
        """Single 模式：1 个 Subagent 完成整个 Epic"""
        # 1. 创建 Worktree
        # 2. 启动 Epic-level Subagent
        # 3. 监听进度
        pass

    def start_epic_multi_mode(self, epic: Epic):
        """Multi 模式：每个 Story 启动独立 Subagent"""
        # 1. 创建 Worktree
        # 2. 分析 Story 依赖关系（DAG）
        # 3. 启动可并行的 Story（最多 epic.story_concurrency 个）
        # 4. Story 完成后自动启动下一个
        pass

    def on_story_completed(self, story_id: str, epic_id: str):
        """Story 完成回调（multi 模式）"""
        # 1. 更新 Story 状态
        # 2. 更新 Epic 进度
        # 3. 启动等待中的 Story
        # 4. 如果所有 Story 完成，触发 Epic 完成
        pass

    def pause_epic(self, epic_id: str) -> bool:
        """暂停 Epic"""
        pass

    def resume_epic(self, epic_id: str) -> bool:
        """恢复 Epic"""
        pass

    def on_epic_completed(self, epic_id: str):
        """Epic 完成回调"""
        # 1. 运行质量门控
        # 2. 自动合并
        # 3. 清理 Worktree
        # 4. 启动等待中的 Epic
        pass

    def auto_start_queued(self):
        """自动启动队列中的 Epic"""
        # 依赖完成后自动启动
        pass
```

**与其他模块的交互：**
- **DependencyAnalyzer:** 获取 DAG 和可并行 Epic
- **SubagentOrchestrator:** 启动/暂停 Subagent
- **WorktreeManager:** 创建/合并/清理 Worktree
- **QualityGate:** 运行质量检查
- **StateManager:** 更新 Epic 状态
- **TUIApp:** 接收用户启动命令，返回调度结果

**关键技术决策：**
- **并发控制：** 使用队列 + 计数器，配置最大并发数（默认 5）
- **自动调度：** Epic 完成后触发 `auto_start_queued()`，无需用户干预
- **依赖检查：** 启动前验证所有依赖已完成
- **失败处理：** Epic 失败后不自动重试，通知用户

---

### 3.4 Subagent 编排模块 (SubagentOrchestrator)

**职责：**
- 使用 Claude Code Task 工具启动 Subagent（Epic-level 或 Story-level）
- 传递 Epic/Story 上下文（描述、依赖信息）
- 监听 Subagent 输出，解析开发进度
- 追踪 Subagent 状态（运行中/完成/失败）
- 支持两种模式：Epic-level Agent 和 Story-level Agent

**主要类/接口：**

```python
class Subagent:
    """Subagent 数据模型"""
    id: str                    # Agent 唯一 ID
    epic_id: str               # 关联的 Epic ID
    story_id: Optional[str]    # 关联的 Story ID（multi 模式）
    mode: str                  # 模式（epic/story）
    status: str                # 状态（running/completed/failed/timeout）
    started_at: datetime
    completed_at: Optional[datetime]
    output_log: List[str]      # 输出日志
    current_story: Optional[str]  # 当前 Story ID（single 模式）

class TaskRunner:
    """Claude Code Task 工具封装"""

    async def run_task(self, prompt: str, context: dict) -> str:
        """启动 Task"""
        # 调用 Claude Code Task 工具
        pass

class SubagentOrchestrator:
    """Subagent 编排器"""

    def __init__(self, task_runner: TaskRunner):
        self.task_runner = task_runner
        self.agents: Dict[str, Subagent] = {}

    async def start_epic_agent(self, epic: Epic, worktree_path: str) -> Subagent:
        """启动 Epic-level Subagent（single 模式）"""
        # 1. 构建 Task prompt（包含 Epic 描述、所有 Story 列表）
        # 2. 传递 worktree_path 作为工作目录
        # 3. 启动 Task
        # 4. 创建 Subagent 记录（mode="epic"）
        pass

    async def start_story_agent(self, story: Story, epic: Epic, worktree_path: str) -> Subagent:
        """启动 Story-level Subagent（multi 模式）"""
        # 1. 构建 Task prompt（只包含单个 Story 描述和前置条件）
        # 2. 传递 worktree_path 作为工作目录
        # 3. 启动 Task
        # 4. 创建 Subagent 记录（mode="story", story_id=story.id）
        pass

    def build_epic_prompt(self, epic: Epic) -> str:
        """构建 Epic-level prompt"""
        return f"""
        你是一个 AI 开发 Agent，负责完成以下 Epic：

        Epic: {epic.title}
        描述: {epic.description}

        Story 列表（请逐个完成并提交）：
        {self._format_stories(epic.stories)}

        要求：
        - 每完成一个 Story 后立即提交（git commit）
        - 提交信息格式："Story X: {{story.title}}"
        - 完成后输出 "Story X completed"
        """

    def build_story_prompt(self, story: Story, epic: Epic) -> str:
        """构建 Story-level prompt"""
        return f"""
        你是一个 AI 开发 Agent，负责完成以下 Story：

        Epic: {epic.title}
        Story: {story.title}
        描述: {story.description}
        前置条件: {story.prerequisites}

        要求：
        - 完成 Story 后立即提交（git commit）
        - 提交信息格式："Story {story.id}: {story.title}"
        - 完成后输出 "Story {story.id} completed"
        """

    async def monitor_agent(self, agent_id: str, callback: Callable):
        """监听 Subagent 输出"""
        # 解析 Story 完成事件
        # 更新 Epic/Story 进度
        pass

    def pause_agent(self, agent_id: str) -> bool:
        """暂停 Subagent"""
        # 发送暂停信号（如果 Task 工具支持）
        pass

    def get_agent_status(self, agent_id: str) -> Optional[Subagent]:
        """获取 Agent 状态"""
        pass

    def parse_progress(self, output: str) -> Dict[str, Any]:
        """解析 Subagent 输出，提取进度"""
        # 识别 "Story X completed" 等关键信息
        pass
```

**与其他模块的交互：**
- **Scheduler:** 接收启动/暂停命令
- **WorktreeManager:** 获取 Worktree 路径传递给 Subagent
- **StateManager:** 更新 Epic 进度和 Subagent 状态
- **TUIApp:** 提供 Agent 活动信息给 UI 显示

**关键技术决策：**
- **Task Prompt 格式：**
  ```
  你是一个 AI 开发 Agent，负责完成以下 Epic：

  Epic: {epic.title}
  描述: {epic.description}

  Story 列表（请逐个完成并提交）：
  1. {story_1.title} - {story_1.description}
  2. {story_2.title} - {story_2.description}
  ...

  工作目录: {worktree_path}

  要求：
  - 每完成一个 Story 后立即提交（git commit）
  - 提交信息格式："Story X: {story.title}"
  - 完成后输出 "Story X completed"
  ```
- **进度解析：** 使用正则表达式匹配 "Story X completed"
- **异步处理：** 使用 asyncio 并发监听多个 Subagent
- **超时设置：** 单个 Epic 超时 3600 秒（可配置）

---

### 3.5 Git Worktree 管理模块 (WorktreeManager)

**职责：**
- 为每个 Epic 创建独立的 Git Worktree
- 管理 Worktree 生命周期（创建、清理）
- 执行自动合并（无冲突时）
- 检测文件冲突，提供冲突解决建议

**主要类/接口：**

```python
class Worktree:
    """Worktree 数据模型"""
    epic_id: str               # 关联的 Epic ID
    branch_name: str           # 分支名称
    path: str                  # Worktree 路径
    created_at: datetime

class WorktreeManager:
    """Worktree 管理器"""

    def __init__(self, project_path: str, worktree_base: str = ".aedt/worktrees"):
        self.project_path = project_path
        self.worktree_base = worktree_base
        self.repo = git.Repo(project_path)

    def create_worktree(self, epic_id: str, branch_prefix: str = "epic") -> Worktree:
        """创建 Worktree"""
        # 1. 生成分支名称：{branch_prefix}-{epic_id}
        # 2. 创建 Worktree：git worktree add {path} -b {branch}
        # 3. 返回 Worktree 对象
        pass

    def merge_to_main(self, epic_id: str, main_branch: str = "main") -> bool:
        """合并到主分支"""
        # 1. 切换到主分支
        # 2. 执行 git merge {epic_branch}
        # 3. 检测冲突，冲突时返回 False
        pass

    def detect_conflicts(self, epic_ids: List[str]) -> Dict[str, List[str]]:
        """检测多个 Epic 的文件冲突"""
        # 分析每个 Epic 修改的文件
        # 返回冲突的文件列表
        pass

    def cleanup_worktree(self, epic_id: str):
        """清理 Worktree"""
        # git worktree remove {path}
        pass

    def list_worktrees(self) -> List[Worktree]:
        """列出所有 Worktree"""
        pass

    def cleanup_all(self):
        """清理所有 Worktree"""
        pass
```

**与其他模块的交互：**
- **Scheduler:** 接收创建/合并/清理命令
- **SubagentOrchestrator:** 提供 Worktree 路径给 Subagent
- **StateManager:** 持久化 Worktree 信息
- **TUIApp:** 提供冲突检测结果给 UI 显示

**关键技术决策：**
- **Git 库选择：** 使用 GitPython（成熟、文档完善）
- **分支命名：** `{prefix}-{epic-id}`，默认 `epic-001`
- **Worktree 路径：** `.aedt/worktrees/epic-{id}/`
- **冲突检测策略：**
  - 比较每个 Epic 分支的 `git diff --name-only main..epic-branch`
  - 识别修改相同文件的 Epic 组合
- **合并策略：**
  - 无冲突时自动合并
  - 有冲突时暂停，通知用户手动解决
- **清理时机：** Epic 合并成功后自动清理
- **安全性：** 不使用 `git reset --hard`、`git push --force` 等危险命令

---

### 3.6 质量门控模块 (QualityGate)

**职责：**
- 在不同阶段运行代码检查（pre_commit, epic_complete, pre_merge）
- 执行 linter、formatter、测试
- 质量检查失败时阻止流程继续
- 提供详细的失败报告

**主要类/接口：**

```python
class GateRule:
    """质量门控规则"""
    name: str                  # 规则名称
    command: str               # 执行命令
    stage: str                 # 阶段（pre_commit/epic_complete/pre_merge）
    required: bool             # 是否必须通过
    timeout: int               # 超时时间（秒）

class TestResult:
    """测试结果"""
    rule: GateRule
    passed: bool               # 是否通过
    output: str                # 输出
    error: Optional[str]       # 错误信息
    duration: float            # 执行时间

class QualityGate:
    """质量门控"""

    def __init__(self, rules: List[GateRule]):
        self.rules = rules

    def run_checks(self, stage: str, worktree_path: str) -> List[TestResult]:
        """运行指定阶段的检查"""
        # 1. 过滤出该阶段的规则
        # 2. 在 worktree_path 中执行命令
        # 3. 收集结果
        pass

    def validate(self, results: List[TestResult]) -> bool:
        """验证所有必需规则是否通过"""
        pass

    def get_failed_rules(self, results: List[TestResult]) -> List[GateRule]:
        """获取失败的规则"""
        pass
```

**与其他模块的交互：**
- **Scheduler:** Epic 完成后触发质量检查
- **WorktreeManager:** 在 Worktree 路径中执行检查
- **StateManager:** 记录质量检查结果
- **TUIApp:** 显示失败报告

**关键技术决策：**
- **配置驱动：** 质量门控规则从配置文件加载
  ```yaml
  quality_gates:
    pre_commit:
      - name: "lint"
        command: "pylint src/"
        required: true
        timeout: 60
    epic_complete:
      - name: "unit_tests"
        command: "pytest tests/unit"
        required: true
        timeout: 300
    pre_merge:
      - name: "integration_tests"
        command: "pytest tests/integration"
        required: true
        timeout: 600
  ```
- **执行环境：** 在 Worktree 路径中执行命令（使用 `subprocess`）
- **失败策略：**
  - `required: true` 规则失败 → 阻止流程
  - `required: false` 规则失败 → 警告但不阻止
- **并行执行：** 多个规则可并行执行（asyncio）

---

### 3.7 TUI Dashboard 模块 (TUIApp)

**职责：**
- 提供实时可视化界面（项目列表、Epic 状态、Agent 活动、日志）
- 处理用户输入（快捷键、命令模式）
- 异步刷新状态（自动刷新 + 手动刷新）
- 实现响应式布局

**主要类/接口：**

```python
from textual.app import App
from textual.containers import Container
from textual.widgets import Header, Footer, Static, ListView

class ProjectPanel(Static):
    """项目列表面板"""

    def __init__(self, project_manager: ProjectManager):
        super().__init__()
        self.project_manager = project_manager

    def render(self) -> str:
        """渲染项目列表"""
        pass

    def on_select(self, project_id: str):
        """项目选择事件"""
        pass

class EpicPanel(Static):
    """Epic 详情面板"""

    def render_epic_list(self, epics: List[Epic]) -> str:
        """渲染 Epic 列表"""
        pass

    def render_story_list(self, epic: Epic) -> str:
        """渲染 Story 列表"""
        pass

class AgentPanel(Static):
    """Agent 活动面板"""

    def render(self, agents: List[Subagent]) -> str:
        """渲染 Agent 列表"""
        pass

class LogPanel(Static):
    """日志面板"""

    def __init__(self, max_lines: int = 1000):
        super().__init__()
        self.log_buffer = []
        self.max_lines = max_lines

    def append_log(self, message: str):
        """追加日志"""
        # 保留最近 max_lines 行
        pass

    def render(self) -> str:
        """渲染日志"""
        pass

class TUIApp(App):
    """TUI 主应用"""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("s", "switch_project", "Switch Project"),
        ("/", "search", "Search"),
        (":", "command_mode", "Command"),
        ("?", "help", "Help"),
    ]

    def __init__(self, scheduler: Scheduler, project_manager: ProjectManager):
        super().__init__()
        self.scheduler = scheduler
        self.project_manager = project_manager

    def compose(self):
        """布局组件"""
        yield Header()
        yield Container(
            ProjectPanel(self.project_manager),
            EpicPanel(),
            AgentPanel(),
            LogPanel(),
        )
        yield Footer()

    async def on_mount(self):
        """启动时初始化"""
        # 启动自动刷新定时器
        self.set_interval(5.0, self.auto_refresh)

    async def auto_refresh(self):
        """自动刷新"""
        # 更新所有面板
        pass

    async def action_refresh(self):
        """手动刷新"""
        pass

    async def action_switch_project(self):
        """切换项目"""
        pass

    async def action_search(self):
        """搜索模式"""
        pass

    async def action_command_mode(self):
        """命令模式"""
        pass
```

**与其他模块的交互：**
- **ProjectManager:** 获取项目列表
- **Scheduler:** 启动/暂停 Epic
- **SubagentOrchestrator:** 获取 Agent 活动信息
- **StateManager:** 获取实时状态
- **FileWatcher:** 接收变化事件，触发刷新

**关键技术决策：**
- **TUI 框架：** 使用 Textual（已验证）
- **布局方案：**
  - 4 面板布局（Header、ProjectPanel、EpicPanel、AgentPanel、LogPanel、Footer）
  - 响应式：终端 < 120 列时切换单列布局
- **刷新策略：**
  - 自动刷新：每 5 秒
  - 手动刷新：r 键
  - 增量更新：只刷新变化的组件
- **快捷键设计：** Vim 风格（hjkl 导航、/ 搜索、: 命令）
- **性能优化：**
  - 日志缓冲区限制 1000 行（内存）
  - 异步加载数据，不阻塞 UI
  - 虚拟滚动（长列表）

---

### 3.8 状态管理模块 (StateManager)

**职责：**
- 持久化项目、Epic、Subagent 状态
- 原子写入，避免数据损坏
- 崩溃恢复：重启时自动加载状态
- 提供状态查询接口

**主要类/接口：**

```python
class ProjectState:
    """项目状态"""
    project_id: str
    epics: Dict[str, EpicState]  # Epic ID → EpicState
    last_updated: datetime

class EpicState:
    """Epic 状态"""
    epic_id: str
    status: str                # queued/developing/completed/failed
    progress: float            # 0-100
    agent_id: Optional[str]
    worktree_path: Optional[str]
    completed_stories: List[str]  # 已完成的 Story ID
    quality_checks: Optional[Dict[str, bool]]  # 质量检查结果
    last_updated: datetime

class DataStore:
    """数据持久化（YAML 文件）"""

    def __init__(self, base_path: str = ".aedt"):
        self.base_path = base_path

    def save(self, key: str, data: dict):
        """保存数据（原子写入）"""
        # 1. 写入临时文件
        # 2. 重命名到目标文件（原子操作）
        pass

    def load(self, key: str) -> Optional[dict]:
        """加载数据"""
        pass

    def delete(self, key: str):
        """删除数据"""
        pass

class StateManager:
    """状态管理器"""

    def __init__(self, data_store: DataStore):
        self.data_store = data_store
        self.states: Dict[str, ProjectState] = {}

    def load_all_states(self) -> Dict[str, ProjectState]:
        """加载所有项目状态"""
        pass

    def save_project_state(self, project_id: str, state: ProjectState):
        """保存项目状态"""
        pass

    def update_epic_state(self, project_id: str, epic_id: str, updates: dict):
        """更新 Epic 状态"""
        pass

    def get_epic_state(self, project_id: str, epic_id: str) -> Optional[EpicState]:
        """获取 Epic 状态"""
        pass

    def recover_from_crash(self) -> List[Project]:
        """崩溃恢复"""
        # 加载所有状态文件
        # 重建项目、Epic 对象
        pass
```

**与其他模块的交互：**
- **ProjectManager:** 持久化项目配置
- **Scheduler:** 持久化 Epic 调度状态
- **SubagentOrchestrator:** 持久化 Subagent 状态
- **TUIApp:** 提供状态查询接口

**关键技术决策：**
- **存储格式：** YAML（人类可读，便于调试和手动修复）
- **文件结构：**
  ```
  .aedt/
  ├── config.yaml                # 全局配置
  ├── projects/
  │   ├── project-1/
  │   │   ├── state.yaml         # 项目状态
  │   │   └── epics/
  │   │       ├── epic-1.log     # Epic 日志
  │   │       └── epic-2.log
  │   └── project-2/
  │       └── state.yaml
  └── logs/
      └── aedt.log               # 主日志
  ```
- **原子写入：**
  ```python
  temp_file = f"{target_file}.tmp"
  with open(temp_file, 'w') as f:
      yaml.dump(data, f)
  os.rename(temp_file, target_file)  # 原子操作
  ```
- **崩溃恢复策略：**
  - 重启时加载所有 state.yaml
  - 恢复 Epic 状态，但不恢复运行中的 Subagent（需要用户手动重启）
  - 标记运行中的 Epic 为 "interrupted"

---

### 3.8.1 混合执行模式设计（重要）

**背景：**
为了避免大 Epic 导致的上下文爆炸和失败风险，AEDT 支持两种执行模式：
- **Single 模式**：1 个 Epic-level Subagent 完成所有 Story（适合小 Epic）
- **Multi 模式**：每个 Story 启动独立 Subagent（适合大 Epic）

**模式选择策略：**

```python
def determine_execution_mode(epic: Epic, config: dict) -> str:
    """自动判断 Epic 执行模式"""
    # 1. 用户显式指定（frontmatter）
    if epic.execution_mode in ["single", "multi"]:
        return epic.execution_mode

    # 2. 自动判断（基于 Story 数量）
    threshold = config["subagent"]["execution"]["auto_mode_threshold"]  # 默认 5
    return "single" if len(epic.stories) <= threshold else "multi"
```

**Single 模式工作流：**

```
1. 用户启动 Epic 1（5 个 Story）
     ↓
2. Scheduler 判断 execution_mode = "single"
     ↓
3. 创建 Worktree (.aedt/worktrees/epic-1/)
     ↓
4. SubagentOrchestrator.start_epic_agent(epic)
     - 构建包含所有 Story 的 prompt
     - 启动 1 个 Subagent
     ↓
5. Subagent 逐个完成 Story（自动提交）
     - Story 1 → git commit
     - Story 2 → git commit
     - ...
     ↓
6. Epic 完成 → 质量门控 → 合并到 main
```

**Multi 模式工作流：**

```
1. 用户启动 Epic 2（10 个 Story）
     ↓
2. Scheduler 判断 execution_mode = "multi"
     ↓
3. 创建 Worktree (.aedt/worktrees/epic-2/)
     ↓
4. DependencyAnalyzer.build_story_dag(epic.stories)
     - 分析 Story.prerequisites 字段
     - 构建 Story 依赖关系图
     ↓
5. Scheduler.start_epic_multi_mode(epic)
     - 识别可并行的 Story（Story 1, 2 无依赖）
     - 启动 Story 1 和 Story 2 的 Subagent（并发数 = 2）
     ↓
6. Story 1 完成 → git commit → 自动启动 Story 3
   Story 2 完成 → git commit → 自动启动 Story 4
     ↓
7. 所有 Story 完成 → Epic 完成 → 质量门控 → 合并到 main
```

**并发控制：**

```python
# 全局并发限制（Epic + Story 总数）
max_concurrent = 5

# 示例：2 个 Epic 并发
# - Epic 1 (single 模式): 1 个 Subagent
# - Epic 2 (multi 模式): 2 个 Story 并发
# 总并发数 = 1 + 2 = 3（< 5，允许）

# Epic 2 内部：story_concurrency = 2
# 最多同时运行 2 个 Story 的 Subagent
```

**优势对比：**

| 维度 | Single 模式 | Multi 模式 |
|------|-------------|-----------|
| **上下文大小** | 大（所有 Story） | 小（单个 Story） |
| **失败粒度** | Epic 级别 | Story 级别 |
| **恢复能力** | Epic 失败需重启整个 Epic | Story 失败只重启该 Story |
| **Story 并发** | 不支持 | 支持（可配置） |
| **API 成本** | 低（1 个 Subagent） | 中（N 个 Subagent） |
| **适用场景** | 小 Epic（≤5 Story） | 大 Epic（>5 Story） |

**配置示例：**

```yaml
# Epic frontmatter
---
epic_id: 2
execution_mode: multi        # 显式指定 multi 模式
story_concurrency: 3         # 最多 3 个 Story 并发
---

# 全局配置 (.aedt/config.yaml)
subagent:
  execution:
    auto_mode_threshold: 5   # 阈值：≤5 用 single，>5 用 multi
    default_story_concurrency: 2  # 默认并发数
```

---

### 3.9 文件监听模块 (FileWatcher)

**职责：**
- 监听项目目录的 Epic 文档变化
- 检测新增、修改、删除的 Epic 文件
- 触发 Epic 重新解析
- 避免重复触发（debounce）

**主要类/接口：**

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    """文件变化处理器"""

    def __init__(self, callback: Callable):
        self.callback = callback
        self.debounce_timer = {}

    def on_modified(self, event):
        """文件修改事件"""
        if event.src_path.endswith('.md'):
            self.debounce_callback(event.src_path)

    def on_created(self, event):
        """文件创建事件"""
        if event.src_path.endswith('.md'):
            self.debounce_callback(event.src_path)

    def debounce_callback(self, path: str, delay: float = 1.0):
        """防抖处理"""
        # 延迟触发，避免频繁事件
        pass

class FileWatcher:
    """文件监听器"""

    def __init__(self):
        self.observer = Observer()
        self.handlers = {}

    def watch_directory(self, path: str, callback: Callable):
        """监听目录"""
        handler = ChangeHandler(callback)
        self.observer.schedule(handler, path, recursive=True)
        self.handlers[path] = handler

    def start(self):
        """启动监听"""
        self.observer.start()

    def stop(self):
        """停止监听"""
        self.observer.stop()
        self.observer.join()
```

**与其他模块的交互：**
- **ProjectManager:** 监听项目 `docs/epics/` 目录
- **EpicParser:** 触发 Epic 重新解析
- **TUIApp:** 通知 UI 刷新

**关键技术决策：**
- **监听库：** watchdog（成熟、跨平台）
- **监听路径：** `{project_path}/docs/epics/`
- **防抖机制：** 1 秒延迟，避免频繁触发
- **事件过滤：** 只监听 `.md` 文件变化
- **性能考虑：** 使用 `recursive=False` 避免监听整个项目

---

## 4. 数据模型

### 4.1 核心数据结构

**项目 (Project)**
```python
@dataclass
class Project:
    id: str                    # 项目唯一 ID（路径 hash）
    name: str                  # 项目名称
    path: str                  # 项目根目录路径
    workflow_type: str         # 工作流类型（bmad/spec-kit/custom）
    config: dict               # 项目特定配置
    epics: List[Epic]          # Epic 列表
    created_at: datetime
    updated_at: datetime
```

**Epic**
```python
@dataclass
class Epic:
    id: str                    # Epic ID（从文档提取）
    project_id: str            # 所属项目 ID
    title: str                 # 标题
    description: str           # 描述
    depends_on: List[str]      # 依赖的 Epic ID 列表
    priority: str              # 优先级（high/medium/low）
    stories: List[Story]       # Story 列表
    status: str                # 状态（queued/developing/completed/failed/interrupted）
    progress: float            # 进度百分比（0-100）
    agent_id: Optional[str]    # 关联的 Subagent ID（single 模式）
    worktree_path: Optional[str]  # Worktree 路径
    branch_name: Optional[str]    # Git 分支名
    execution_mode: str = "auto"  # 执行模式（single/multi/auto）
    story_concurrency: int = 2    # Story 并发数（multi 模式）
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
```

**Story**
```python
@dataclass
class Story:
    id: str                    # Story ID
    epic_id: str               # 所属 Epic ID
    title: str                 # 标题
    description: str           # 描述
    prerequisites: List[str]   # 前置 Story ID
    status: str                # 状态（pending/in_progress/completed/failed）
    commit_hash: Optional[str] # Git 提交哈希
    agent_id: Optional[str]    # 关联的 Subagent ID（multi 模式）
    completed_at: Optional[datetime]
```

**Subagent**
```python
@dataclass
class Subagent:
    id: str                    # Agent 唯一 ID
    epic_id: str               # 关联的 Epic ID
    project_id: str            # 所属项目 ID
    status: str                # 状态（running/completed/failed/timeout/paused）
    started_at: datetime
    completed_at: Optional[datetime]
    output_log: List[str]      # 输出日志（内存）
    current_story: Optional[str]  # 当前 Story ID
    timeout: int               # 超时时间（秒）
```

**Worktree**
```python
@dataclass
class Worktree:
    epic_id: str               # 关联的 Epic ID
    branch_name: str           # Git 分支名称
    path: str                  # Worktree 绝对路径
    created_at: datetime
    merged: bool               # 是否已合并
```

### 4.2 YAML 配置结构

**全局配置 (.aedt/config.yaml)**
```yaml
version: "1.0"

# 项目列表
projects:
  - id: "aedt-main"
    name: "AEDT"
    path: "/path/to/aedt"
    workflow: "bmad"

  - id: "other-project"
    name: "Other Project"
    path: "/path/to/other"
    workflow: "bmad"

# Subagent 配置
subagent:
  max_concurrent: 5            # 最大并发数（Epic + Story 总数）
  timeout: 3600                # 超时时间（秒）
  model: "claude-sonnet-4"     # Claude 模型

  # 执行模式配置
  execution:
    auto_mode_threshold: 5     # Story 数量阈值（≤5 用 single，>5 用 multi）
    default_story_concurrency: 2  # multi 模式默认 Story 并发数

# 质量门控
quality_gates:
  pre_commit:
    - name: "lint"
      command: "pylint src/"
      required: true
      timeout: 60
    - name: "format_check"
      command: "black --check src/"
      required: true
      timeout: 30

  epic_complete:
    - name: "unit_tests"
      command: "pytest tests/unit"
      required: true
      timeout: 300

  pre_merge:
    - name: "integration_tests"
      command: "pytest tests/integration"
      required: true
      timeout: 600

# Git 配置
git:
  worktree_base: ".aedt/worktrees"  # Worktree 根目录
  branch_prefix: "epic"              # 分支前缀
  auto_cleanup: true                 # 自动清理 Worktree
  main_branch: "main"                # 主分支名

# 日志配置
logging:
  level: "INFO"                      # DEBUG/INFO/WARNING/ERROR
  file: ".aedt/logs/aedt.log"
  max_size: 10485760                 # 10MB
  backup_count: 5

# TUI 配置
tui:
  auto_refresh_interval: 5           # 自动刷新间隔（秒）
  log_buffer_size: 1000              # 日志缓冲区大小
  theme: "dark"                      # 主题（dark/light）
```

**项目状态 (.aedt/projects/{project-id}/state.yaml)**
```yaml
project_id: "aedt-main"
project_name: "AEDT"
last_updated: "2025-11-23T10:30:00"

epics:
  "1":
    epic_id: "1"
    title: "多项目管理中心"
    status: "completed"
    progress: 100.0
    agent_id: "agent-001"
    worktree_path: ".aedt/worktrees/epic-1"
    branch_name: "epic-1"
    completed_stories: ["1-1", "1-2", "1-3"]
    quality_checks:
      lint: true
      unit_tests: true
      integration_tests: true
    completed_at: "2025-11-23T09:45:00"

  "2":
    epic_id: "2"
    title: "BMAD 工作流集成"
    status: "developing"
    progress: 60.0
    agent_id: "agent-002"
    worktree_path: ".aedt/worktrees/epic-2"
    branch_name: "epic-2"
    completed_stories: ["2-1", "2-2", "2-3"]
    last_updated: "2025-11-23T10:30:00"

  "3":
    epic_id: "3"
    title: "调度引擎"
    status: "queued"
    progress: 0.0
    depends_on: ["1"]
```

**Epic 文档格式扩展 (docs/epics/epic-002.md)**
```markdown
---
epic_id: 2
title: "BMAD 工作流集成"
depends_on: [1]              # 依赖 Epic 1
priority: high               # 优先级
execution_mode: multi        # 执行模式（single/multi/auto，默认 auto）
story_concurrency: 2         # Story 并发数（仅 multi 模式，默认 2）
estimated_hours: 8           # 估算时间
---

# Epic 2: BMAD 工作流集成

## 描述
实现 AEDT 与 BMAD 工作流的深度集成...

## Story 列表

### Story 2.1: 读取 Epic 文档
**描述:** 从 `docs/epics/*.md` 读取 Epic 定义...
**Prerequisites:** None

### Story 2.2: 解析依赖关系
**描述:** 从 Epic frontmatter 提取 `depends_on` 字段...
**Prerequisites:** 2.1

### Story 2.3: 提取 Story 列表
**描述:** 解析 Epic Markdown 文档中的 Story...
**Prerequisites:** 2.1

...
```

**执行模式说明：**
- `execution_mode: single` - 小 Epic（≤5 Story），1 个 Subagent 完成所有 Story
- `execution_mode: multi` - 大 Epic（>5 Story），每个 Story 启动独立 Subagent
- `execution_mode: auto` - 自动判断（默认），根据 Story 数量自动选择
- `story_concurrency` - multi 模式下的 Story 并发数（默认 2）

### 4.3 状态文件格式

**Epic 日志 (.aedt/projects/{project-id}/epics/epic-{id}.log)**
```
[2025-11-23 10:00:00] [INFO] Epic 2 started
[2025-11-23 10:00:05] [INFO] Worktree created: .aedt/worktrees/epic-2
[2025-11-23 10:00:10] [INFO] Subagent agent-002 started
[2025-11-23 10:05:30] [INFO] Story 2.1 completed (commit: abc123)
[2025-11-23 10:15:45] [INFO] Story 2.2 completed (commit: def456)
[2025-11-23 10:30:20] [INFO] Story 2.3 in progress
[2025-11-23 10:30:25] [ERROR] Lint check failed: src/parser.py:42:10: E501 line too long
```

**主日志 (.aedt/logs/aedt.log)**
```
[2025-11-23 09:00:00] [INFO] AEDT started
[2025-11-23 09:00:01] [INFO] Loaded 3 projects
[2025-11-23 09:00:02] [INFO] TUI Dashboard initialized
[2025-11-23 09:05:00] [INFO] User started 3 epics: [1, 2, 3]
[2025-11-23 09:05:01] [INFO] Dependency analysis: [1, 2] parallel, [3] queued
[2025-11-23 09:05:05] [INFO] Epic 1 started (agent-001)
[2025-11-23 09:05:06] [INFO] Epic 2 started (agent-002)
[2025-11-23 09:45:00] [INFO] Epic 1 completed
[2025-11-23 09:45:05] [INFO] Quality checks passed for Epic 1
[2025-11-23 09:45:10] [INFO] Epic 1 merged to main
[2025-11-23 09:45:15] [INFO] Epic 3 started (agent-003) - auto-scheduled
```

---

## 5. 关键技术决策

### 5.1 Python 版本和依赖管理

**决策：Python 3.10+ + pip**

**理由：**
- Python 3.10 引入了更好的类型提示（PEP 604 Union 语法）
- 兼容性好，主流 Linux/macOS 都支持
- pip 简单直接，适合 MVP 快速迭代

**备选方案：**
- **Poetry:** 依赖管理更强大，但增加复杂度（Phase 2 考虑）
- **Python 3.11+:** 性能更好，但兼容性略差

**实施：**
```bash
# requirements.txt
textual>=6.6.0
GitPython>=3.1.0
PyYAML>=6.0
watchdog>=3.0.0
pytest>=7.0.0
```

### 5.2 TUI 框架选择

**决策：Textual**

**理由：**
- Phase 0 验证通过，成熟稳定
- 支持响应式布局、快捷键、CSS 样式
- 文档完善，社区活跃
- 性能良好，适合实时刷新

**备选方案：**
- **Rich:** 功能简单，不支持交互式 TUI
- **Urwid:** 成熟但学习曲线陡峭
- **py-cui:** 功能有限

### 5.3 异步 vs 多线程（Subagent 管理）

**决策：asyncio（异步）**

**理由：**
- Subagent 是 I/O 密集型任务（等待 API 响应）
- asyncio 更轻量，易于管理多个并发任务
- Textual 原生支持 asyncio
- 避免 GIL 问题

**实施：**
```python
async def start_agent(self, epic: Epic) -> Subagent:
    task = await self.task_runner.run_task(prompt, context)
    agent = Subagent(id=task.id, epic_id=epic.id)
    asyncio.create_task(self.monitor_agent(agent.id))
    return agent

async def monitor_agent(self, agent_id: str):
    while True:
        output = await self.get_agent_output(agent_id)
        progress = self.parse_progress(output)
        await self.update_state(agent_id, progress)
        await asyncio.sleep(5)
```

**备选方案：**
- **多线程（threading）:** 更复杂，GIL 限制性能
- **多进程（multiprocessing）:** 过度设计，通信复杂

### 5.4 Git 操作库

**决策：GitPython**

**理由：**
- 成熟稳定，文档完善
- 高级 API + 低级 CLI 调用都支持
- 社区活跃，问题容易解决

**实施：**
```python
import git

repo = git.Repo(project_path)
worktree_path = f".aedt/worktrees/epic-{epic_id}"
branch_name = f"epic-{epic_id}"

# 创建 Worktree
repo.git.worktree('add', worktree_path, '-b', branch_name)

# 合并
repo.git.checkout('main')
repo.git.merge(branch_name)

# 清理
repo.git.worktree('remove', worktree_path)
```

**备选方案：**
- **dulwich:** 纯 Python 实现，但功能有限
- **直接调用 git CLI:** 更灵活，但错误处理复杂

### 5.5 YAML 解析库

**决策：PyYAML**

**理由：**
- 简单易用，标准库
- 足够满足配置文件解析需求
- 轻量级

**实施：**
```python
import yaml

# 读取配置
with open('.aedt/config.yaml') as f:
    config = yaml.safe_load(f)

# 写入状态
with open(state_file, 'w') as f:
    yaml.safe_dump(state, f, default_flow_style=False)
```

**备选方案：**
- **ruamel.yaml:** 保留注释和格式，但更复杂（Phase 2 考虑）

### 5.6 文件监听库

**决策：watchdog**

**理由：**
- 跨平台（macOS/Linux/Windows）
- 成熟稳定，文档完善
- 支持防抖（debounce）

**实施：**
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class EpicChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.md'):
            self.parser.reload_epic(event.src_path)

observer = Observer()
observer.schedule(handler, 'docs/epics', recursive=False)
observer.start()
```

**备选方案：**
- **inotify (Linux 专用):** 不跨平台
- **轮询:** 性能差，延迟高

### 5.7 日志框架

**决策：Python logging（标准库）**

**理由：**
- 标准库，无需额外依赖
- 功能完善（分级、格式化、文件轮转）
- 易于配置

**实施：**
```python
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        RotatingFileHandler('.aedt/logs/aedt.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()  # 控制台输出
    ]
)

logger = logging.getLogger('aedt')
logger.info("Epic 1 started")
logger.error("Merge conflict detected")
```

**备选方案：**
- **loguru:** 更现代，但增加依赖

### 5.8 测试框架

**决策：pytest**

**理由：**
- 简洁易用，断言直观
- 插件丰富（pytest-asyncio、pytest-cov）
- 社区标准

**实施：**
```python
# tests/test_scheduler.py
import pytest
from aedt.scheduler import Scheduler

@pytest.fixture
def scheduler():
    return Scheduler(max_concurrent=5)

def test_start_parallel_epics(scheduler):
    epics = [Epic(id="1"), Epic(id="2"), Epic(id="3")]
    result = scheduler.start_epics(epics)
    assert len(result["running"]) == 3
    assert len(result["queued"]) == 0

@pytest.mark.asyncio
async def test_subagent_monitor():
    orchestrator = SubagentOrchestrator()
    agent = await orchestrator.start_agent(epic)
    assert agent.status == "running"
```

**备选方案：**
- **unittest:** 标准库，但代码冗长

### 5.9 配置管理策略

**决策：YAML 配置文件 + 环境变量**

**理由：**
- YAML 人类可读，易于编辑
- 环境变量管理敏感信息（API 密钥）
- 分离配置和代码

**实施：**
```python
import os
import yaml

class ConfigManager:
    def __init__(self, config_path: str = ".aedt/config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # API 密钥从环境变量读取
        self.api_key = os.getenv('CLAUDE_API_KEY')
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY not set")

    def get(self, key: str, default=None):
        return self.config.get(key, default)
```

**备选方案：**
- **JSON:** 不支持注释，可读性差
- **.env 文件:** 适合环境变量，但不适合复杂配置

### 5.10 错误处理策略

**决策：分层错误处理 + 友好提示**

**理由：**
- 不同层次的错误需要不同处理方式
- 用户友好的错误提示提升体验

**实施：**
```python
class AEDTError(Exception):
    """AEDT 基础异常"""
    pass

class ConfigNotFoundError(AEDTError):
    """配置文件未找到"""
    def __init__(self):
        super().__init__(
            "配置文件未找到。\n"
            "建议：运行 `aedt init` 初始化配置。"
        )

class GitConflictError(AEDTError):
    """Git 冲突"""
    def __init__(self, files: List[str]):
        super().__init__(
            f"检测到 Git 冲突：\n" +
            "\n".join(f"  - {f}" for f in files) +
            "\n建议：手动解决冲突后运行 `aedt resume <epic-id>`"
        )

# TUI 错误处理
try:
    scheduler.start_epics(epic_ids)
except GitConflictError as e:
    self.show_error_dialog(str(e))
except Exception as e:
    logger.exception("Unexpected error")
    self.show_error_dialog(
        "未知错误，请查看日志：.aedt/logs/aedt.log"
    )
```

---

## 6. 部署架构

### 6.1 安装方式

**MVP 阶段：**
```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/aedt.git
cd aedt

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装 AEDT（开发模式）
pip install -e .

# 4. 验证安装
aedt --version

# 5. 初始化配置
aedt init
```

**Phase 2：**
```bash
# PyPI 安装
pip install aedt

# 或独立二进制（PyInstaller）
curl -sSL https://aedt.dev/install.sh | bash
```

### 6.2 配置文件位置

**全局配置：**
```
~/.aedt/
├── config.yaml          # 全局配置
└── logs/
    └── aedt.log         # 全局日志
```

**项目配置：**
```
{project-root}/
├── .aedt/
│   ├── config.yaml      # 项目配置（可选，覆盖全局）
│   ├── projects/
│   │   └── {project-id}/
│   │       ├── state.yaml     # 项目状态
│   │       └── epics/
│   │           ├── epic-1.log
│   │           └── epic-2.log
│   ├── worktrees/
│   │   ├── epic-1/
│   │   └── epic-2/
│   └── logs/
│       └── aedt.log     # 项目日志
└── docs/
    └── epics/           # Epic 文档
        ├── epic-001.md
        └── epic-002.md
```

**优先级：**
1. 项目配置 `.aedt/config.yaml`（如果存在）
2. 全局配置 `~/.aedt/config.yaml`
3. 默认配置（代码内置）

### 6.3 数据存储结构

**目录结构：**
```
.aedt/
├── config.yaml                    # 配置文件
├── projects/
│   ├── aedt-main/
│   │   ├── state.yaml             # 项目状态
│   │   └── epics/
│   │       ├── epic-1.log         # Epic 日志
│   │       └── epic-2.log
│   └── other-project/
│       └── state.yaml
├── worktrees/
│   ├── epic-1/                    # Epic 1 的 Worktree
│   │   ├── src/
│   │   └── tests/
│   └── epic-2/
│       ├── src/
│       └── tests/
└── logs/
    └── aedt.log                   # 主日志
```

**存储策略：**
- **配置：** YAML 文件（人类可读，可版本控制）
- **状态：** YAML 文件（原子写入，防止损坏）
- **日志：** 文本文件（轮转，最大 10MB，保留 5 个备份）
- **Worktree：** Git 管理（自动清理）

### 6.4 日志文件位置

**日志层次：**

1. **主日志：** `.aedt/logs/aedt.log`
   - 记录全局事件（启动、项目添加、调度决策）
   - 分级：DEBUG/INFO/WARNING/ERROR
   - 轮转：10MB，保留 5 个备份

2. **Epic 日志：** `.aedt/projects/{project-id}/epics/epic-{id}.log`
   - 记录单个 Epic 的开发过程
   - Subagent 输出
   - Story 完成事件
   - 质量检查结果

3. **控制台输出：**
   - TUI 内实时日志面板
   - 缓冲区 1000 行（内存）
   - 完整日志写入文件

**日志格式：**
```
[2025-11-23 10:30:25] [INFO] Epic 2 started
[2025-11-23 10:30:30] [DEBUG] Worktree created: .aedt/worktrees/epic-2
[2025-11-23 10:30:35] [ERROR] Lint check failed: src/parser.py:42:10: E501
```

---

## 7. 非功能需求实现

### 7.1 性能

**NFR1-7：TUI 响应、状态刷新、日志处理**

**实现策略：**

1. **TUI 响应 < 200ms**
   - 异步处理：所有耗时操作（文件读取、Git 操作）使用 asyncio
   - 增量更新：只刷新变化的组件，而非全屏重绘
   - 缓存：项目列表、Epic 元数据缓存在内存

2. **状态刷新 < 200ms**
   - 自动刷新周期：5 秒（可配置）
   - 只更新变化的 Epic 状态（比较哈希）
   - 异步加载，不阻塞 UI

3. **日志处理性能**
   - 内存缓冲区：1000 行（循环队列）
   - 异步写入文件：不阻塞 UI
   - 日志过滤：仅显示相关 Epic 的日志

4. **文件监听性能**
   - watchdog 高效监听，延迟 < 1 秒
   - 防抖：1 秒内多次变化只触发一次
   - 只监听 `docs/epics/` 目录

5. **大规模项目支持**
   - 虚拟滚动：长列表（100+ Epic）使用虚拟滚动
   - 分页加载：Epic 详情按需加载
   - 索引优化：Epic ID 建立索引，O(1) 查询

6. **Subagent 启动速度**
   - 并行创建 Worktree：asyncio.gather()
   - 预热连接：Claude API 连接池
   - 超时控制：启动超时 10 秒

**性能基准测试：**
```python
# tests/performance/test_tui_responsiveness.py
import pytest
import time

def test_tui_startup_time(tui_app):
    start = time.time()
    tui_app.load_projects(count=3, epics_per_project=10)
    elapsed = time.time() - start
    assert elapsed < 2.0  # < 2 秒

@pytest.mark.asyncio
async def test_refresh_performance(tui_app):
    start = time.time()
    await tui_app.refresh_all()
    elapsed = time.time() - start
    assert elapsed < 0.2  # < 200ms
```

### 7.2 可靠性

**NFR8-12：崩溃恢复、异常处理、数据持久化**

**实现策略：**

1. **崩溃恢复**
   ```python
   class StateManager:
       def recover_from_crash(self) -> List[Project]:
           """崩溃恢复"""
           # 1. 加载所有 state.yaml
           states = self.load_all_states()

           # 2. 重建项目、Epic 对象
           projects = []
           for state in states:
               project = self.rebuild_project(state)

               # 3. 标记运行中的 Epic 为 "interrupted"
               for epic in project.epics:
                   if epic.status == "developing":
                       epic.status = "interrupted"
                       logger.warning(f"Epic {epic.id} was interrupted, please resume manually")

               projects.append(project)

           return projects
   ```

2. **数据持久化（原子写入）**
   ```python
   def atomic_save(self, file_path: str, data: dict):
       """原子写入"""
       temp_file = f"{file_path}.tmp"

       # 1. 写入临时文件
       with open(temp_file, 'w') as f:
           yaml.safe_dump(data, f)

       # 2. 原子重命名（POSIX 保证原子性）
       os.rename(temp_file, file_path)
   ```

3. **Subagent 异常处理**
   ```python
   async def monitor_agent(self, agent_id: str):
       try:
           while agent.status == "running":
               output = await self.get_output(agent_id)
               await asyncio.sleep(5)
       except asyncio.TimeoutError:
           agent.status = "timeout"
           logger.error(f"Agent {agent_id} timeout")
           self.notify_user(f"Epic {agent.epic_id} timeout, please check")
       except Exception as e:
           agent.status = "failed"
           logger.exception(f"Agent {agent_id} failed")
           self.notify_user(f"Epic {agent.epic_id} failed: {e}")
   ```

4. **Git 操作容错**
   ```python
   def create_worktree(self, epic_id: str) -> Worktree:
       worktree_path = f".aedt/worktrees/epic-{epic_id}"
       branch_name = f"epic-{epic_id}"

       try:
           # 创建 Worktree
           self.repo.git.worktree('add', worktree_path, '-b', branch_name)
           return Worktree(epic_id=epic_id, path=worktree_path, branch_name=branch_name)
       except git.GitCommandError as e:
           # 回滚：删除可能创建的目录
           if os.path.exists(worktree_path):
               shutil.rmtree(worktree_path)
           raise GitWorktreeError(f"Failed to create worktree: {e}")
   ```

5. **网络容错（API 调用重试）**
   ```python
   async def call_api_with_retry(self, prompt: str, max_retries: int = 3):
       for attempt in range(max_retries):
           try:
               result = await self.api_client.call(prompt, timeout=60)
               return result
           except asyncio.TimeoutError:
               if attempt == max_retries - 1:
                   raise
               wait = 2 ** attempt  # 指数退避
               logger.warning(f"API timeout, retry {attempt+1}/{max_retries} after {wait}s")
               await asyncio.sleep(wait)
   ```

### 7.3 安全性

**NFR22-25：凭证安全、文件权限、Git 安全**

**实现策略：**

1. **凭证安全**
   ```python
   # 从环境变量读取 API 密钥
   api_key = os.getenv('CLAUDE_API_KEY')
   if not api_key:
       raise ConfigError(
           "CLAUDE_API_KEY not set.\n"
           "Please set: export CLAUDE_API_KEY=your_key"
       )

   # .gitignore 自动添加
   def ensure_gitignore(project_path: str):
       gitignore_path = os.path.join(project_path, '.gitignore')
       if os.path.exists(gitignore_path):
           with open(gitignore_path, 'a') as f:
               f.write("\n# AEDT\n.aedt/\n")
   ```

2. **文件系统权限**
   ```python
   def validate_project_path(path: str):
       """验证项目路径"""
       # 只读取用户明确添加的项目
       if not os.path.isabs(path):
           raise ValueError("Project path must be absolute")

       if not os.path.exists(path):
           raise ValueError(f"Project path not found: {path}")

       # 检查是否在用户目录内
       user_home = os.path.expanduser("~")
       if not path.startswith(user_home):
           logger.warning(f"Project {path} outside user directory")
   ```

3. **Git 操作安全**
   ```python
   class SafeGitOperations:
       """安全的 Git 操作"""

       # 黑名单：禁止的危险命令
       FORBIDDEN_COMMANDS = ['push --force', 'reset --hard', 'clean -fd']

       def run_git_command(self, cmd: str):
           if any(forbidden in cmd for forbidden in self.FORBIDDEN_COMMANDS):
               raise SecurityError(f"Forbidden Git command: {cmd}")

           return self.repo.git.execute(cmd)
   ```

4. **依赖安全**
   ```bash
   # requirements.txt 锁定版本
   textual==6.6.0
   GitPython==3.1.40
   PyYAML==6.0
   watchdog==3.0.0

   # 定期安全扫描
   pip install safety
   safety check
   ```

### 7.4 可维护性

**NFR17-21：模块化、插件化、测试覆盖**

**实现策略：**

1. **代码模块化**
   ```
   aedt/
   ├── __init__.py
   ├── cli.py                   # CLI 入口
   ├── core/
   │   ├── project.py           # ProjectManager
   │   ├── epic.py              # Epic, Story 数据模型
   │   ├── scheduler.py         # Scheduler
   │   └── state.py             # StateManager
   ├── parsers/
   │   ├── base.py              # WorkflowAdapter 抽象类
   │   ├── bmad.py              # BMADAdapter
   │   └── epic_parser.py       # EpicParser
   ├── git/
   │   └── worktree.py          # WorktreeManager
   ├── agent/
   │   └── orchestrator.py      # SubagentOrchestrator
   ├── quality/
   │   └── gate.py              # QualityGate
   ├── tui/
   │   ├── app.py               # TUIApp
   │   └── panels.py            # 各种面板组件
   └── utils/
       ├── config.py            # ConfigManager
       ├── logger.py            # 日志工具
       └── watcher.py           # FileWatcher
   ```

2. **插件化架构**
   ```python
   # parsers/base.py
   class WorkflowAdapter(ABC):
       """工作流适配器抽象类"""

       @abstractmethod
       def parse_epics(self, project_path: str) -> List[Epic]:
           """解析 Epic 列表"""
           pass

       @abstractmethod
       def parse_dependencies(self, epics: List[Epic]) -> DAG:
           """解析依赖关系"""
           pass

   # parsers/bmad.py
   class BMADAdapter(WorkflowAdapter):
       """BMAD 工作流适配器"""

       def parse_epics(self, project_path: str) -> List[Epic]:
           # 读取 docs/epics/*.md
           # 解析 YAML frontmatter
           pass

   # 插件注册（Phase 2）
   WORKFLOW_ADAPTERS = {
       'bmad': BMADAdapter,
       'spec-kit': SpecKitAdapter,  # Phase 2
   }

   def load_adapter(workflow_type: str) -> WorkflowAdapter:
       adapter_class = WORKFLOW_ADAPTERS.get(workflow_type)
       if not adapter_class:
           raise ValueError(f"Unknown workflow: {workflow_type}")
       return adapter_class()
   ```

3. **测试覆盖率**
   ```bash
   # 运行测试 + 覆盖率
   pytest --cov=aedt --cov-report=html tests/

   # 目标：核心模块 > 80%
   ```

   **测试结构：**
   ```
   tests/
   ├── unit/
   │   ├── test_scheduler.py
   │   ├── test_epic_parser.py
   │   ├── test_worktree.py
   │   └── test_quality_gate.py
   ├── integration/
   │   ├── test_end_to_end.py
   │   └── test_git_operations.py
   └── performance/
       └── test_tui_responsiveness.py
   ```

---

## 8. 风险与缓解

### 8.1 Subagent 并发限制

**风险描述：**
- Phase 0 只验证了 3 个 Subagent 并发
- 5+ 个 Subagent 的稳定性未知
- 可能遇到 API 限流、成本失控

**影响：**
- 高并发时 Subagent 失败率增加
- API 成本超预算
- 系统稳定性下降

**缓解策略：**

1. **并发限制**
   ```python
   # config.yaml
   subagent:
     max_concurrent: 5          # 限制最大并发数
     timeout: 3600              # 超时时间
     retry_on_failure: false    # 不自动重试
   ```

2. **API 监控**
   ```python
   class APIMonitor:
       def __init__(self, budget: float = 100.0):
           self.total_cost = 0.0
           self.budget = budget

       def track_call(self, cost: float):
           self.total_cost += cost
           if self.total_cost > self.budget:
               raise BudgetExceededError(
                   f"API cost {self.total_cost} exceeded budget {self.budget}"
               )
   ```

3. **用户控制**
   - TUI 显示当前并发数和成本
   - 提供手动暂停功能
   - 成本预警提示

**验证计划：**
- MVP 阶段：限制并发数为 3，逐步测试 5 个
- Phase 2：实现成本监控和自动暂停

### 8.2 Epic 依赖关系扩展

**风险描述：**
- BMAD Epic 模板默认不包含 Epic 级别依赖
- 需要用户手动标注 `depends_on` 字段
- 用户可能忘记或标注错误

**影响：**
- 依赖关系不准确，导致调度错误
- 用户体验下降（需要手动维护）

**缓解策略：**

1. **清晰的文档和示例**
   ```markdown
   # docs/EPIC_FORMAT.md

   ## Epic Frontmatter 格式

   ```yaml
   ---
   epic_id: 2
   title: "BMAD 工作流集成"
   depends_on: [1]              # 依赖 Epic 1
   priority: high
   ---
   ```

   **依赖关系说明：**
   - `depends_on`: 依赖的 Epic ID 列表
   - 如果没有依赖，设置为 `[]`
   - 如果依赖多个，使用 `[1, 2, 3]`
   ```

2. **验证工具**
   ```python
   def validate_dependencies(epics: List[Epic]) -> List[str]:
       """验证依赖关系"""
       errors = []
       epic_ids = {e.id for e in epics}

       for epic in epics:
           for dep in epic.depends_on:
               if dep not in epic_ids:
                   errors.append(f"Epic {epic.id} depends on non-existent Epic {dep}")

       return errors

   # 启动前验证
   errors = validate_dependencies(epics)
   if errors:
       raise DependencyError("\n".join(errors))
   ```

3. **Phase 2：AI 自动推断**
   ```python
   class AIDependencyAnalyzer:
       """使用 AI 自动分析依赖关系"""

       def infer_dependencies(self, epics: List[Epic]) -> Dict[str, List[str]]:
           # 将 Epic 描述传递给 AI
           # AI 分析哪些 Epic 可能有依赖关系
           # 返回建议的依赖关系
           pass
   ```

**验证计划：**
- MVP：手动标注 + 验证工具
- Phase 2：AI 自动推断

### 8.3 Git 冲突复杂性

**风险描述：**
- 自动合并可能遗漏复杂冲突
- 冲突检测不准确（只检测文件级别）
- 人工解决冲突后，流程恢复复杂

**影响：**
- 合并失败导致手动介入
- 用户需要理解 Git Worktree 机制
- 影响自动化程度

**缓解策略：**

1. **保守的合并策略**
   ```python
   def merge_to_main(self, epic_id: str) -> bool:
       """保守的合并策略"""
       # 1. 检测冲突
       conflicts = self.detect_conflicts([epic_id])
       if conflicts:
           logger.warning(f"Conflicts detected: {conflicts}")
           return False

       # 2. 运行测试
       test_result = self.quality_gate.run_checks("pre_merge", worktree_path)
       if not test_result.passed:
           logger.error("Tests failed, merge aborted")
           return False

       # 3. 执行合并
       try:
           self.repo.git.merge(branch_name)
           return True
       except git.GitCommandError as e:
           logger.error(f"Merge failed: {e}")
           return False
   ```

2. **详细的冲突报告**
   ```python
   def generate_conflict_report(self, epic_ids: List[str]) -> str:
       """生成冲突报告"""
       conflicts = self.detect_conflicts(epic_ids)

       report = "## Git 冲突检测报告\n\n"
       for epic_pair, files in conflicts.items():
           report += f"### Epic {epic_pair[0]} vs Epic {epic_pair[1]}\n"
           report += "冲突文件：\n"
           for file in files:
               report += f"  - {file}\n"
           report += "\n建议：暂停其中一个 Epic，或手动解决冲突\n\n"

       return report
   ```

3. **冲突解决指导**
   ```
   TUI 显示：

   ┌─────────────────────────────────────┐
   │  🔴 Git 冲突检测                     │
   │  Epic 2 与 Epic 3 有文件冲突：       │
   │  - src/parser.py                    │
   │  - src/utils.py                     │
   │                                     │
   │  建议操作：                         │
   │  1. 暂停 Epic 3：aedt pause 3       │
   │  2. 手动解决冲突：                  │
   │     cd .aedt/worktrees/epic-2       │
   │     # 编辑冲突文件                  │
   │     git add .                       │
   │     git commit -m "Resolve conflict"│
   │  3. 恢复 Epic 3：aedt resume 3      │
   │                                     │
   │  [p] 暂停 Epic 3  [i] 忽略          │
   └─────────────────────────────────────┘
   ```

4. **Phase 2：AI 自动解决简单冲突**
   ```python
   class AIConflictResolver:
       """使用 AI 自动解决简单冲突"""

       def resolve_conflict(self, file_path: str, conflict_content: str) -> Optional[str]:
           # 识别简单冲突（格式化、import 顺序）
           # 使用 AI 生成解决方案
           # 返回修复后的内容
           pass
   ```

**验证计划：**
- MVP：保守合并 + 详细报告 + 手动解决
- Phase 2：AI 自动解决简单冲突

---

## 9. 总结

### 9.1 架构亮点

1. **模块化设计**
   - 9 个核心模块，职责清晰，接口明确
   - 易于单元测试和独立演进

2. **可靠性优先**
   - 崩溃恢复、原子写入、容错设计
   - 确保数据不丢失

3. **性能优化**
   - TUI 响应 < 200ms
   - 异步处理，不阻塞 UI
   - 大规模项目支持（100+ Epic）

4. **可扩展性**
   - 工作流适配器插件化
   - 配置驱动，易于定制
   - 预留 Phase 2 扩展接口

5. **用户友好**
   - 友好的错误提示
   - 内置帮助系统
   - 5 分钟上手

### 9.2 技术栈成熟度

| 技术 | 成熟度 | 风险 | 备注 |
|------|--------|------|------|
| Python 3.10+ | ✅ 高 | 低 | 标准技术栈 |
| Textual TUI | ✅ 高 | 低 | Phase 0 验证通过 |
| GitPython | ✅ 高 | 低 | 成熟稳定 |
| Git Worktree | ✅ 高 | 低 | Phase 0 验证通过 |
| Claude Code Task | ⚠️ 中 | 中 | 并发限制未知 |
| PyYAML | ✅ 高 | 低 | 标准库 |
| watchdog | ✅ 高 | 低 | 成熟稳定 |

### 9.3 MVP 准备就绪

**✅ 所有关键技术假设已验证**
- Claude Code Task 启动 Subagent：✅ 通过
- Git Worktrees 并发性能：✅ 通过
- Textual TUI Framework：✅ 通过

**✅ 架构设计完整**
- 9 个核心模块定义清晰
- 数据模型完整
- 技术决策明确

**✅ 非功能需求覆盖**
- 性能：TUI 响应、状态刷新
- 可靠性：崩溃恢复、容错
- 安全性：凭证管理、文件权限
- 可维护性：模块化、插件化

**下一步行动：**
1. **Epic 分解** - 将架构转化为可实现的 Epic 和 Story
2. **Sprint 规划** - 规划第一个 Sprint（MVP Phase 1）
3. **开始实现** - 按 Epic 优先级开始开发

---

_本架构文档基于 PRD 和 Phase 0 验证报告编写，2025-11-23。_
