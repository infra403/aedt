# Epic Technical Specification: Epic Parsing and Dependency Analysis

Date: 2025-11-23
Author: BMad
Epic ID: 3
Status: Draft

---

## Overview

Epic 3 实现了 AEDT 的核心智能调度基础设施，通过自动解析 BMAD Epic 文档、提取元数据和故事列表、构建依赖关系图（DAG），使系统能够智能识别可并行执行的 Epic 和需要排队等待的 Epic。本 Epic 还包括文件监控机制，自动检测 Epic 文档变更并重新解析，确保系统状态始终与文档同步。

该 Epic 直接支持 PRD 中的关键需求（FR6-FR13, FR25），为后续的调度引擎（Epic 5）和 TUI 可视化（Epic 8）提供必要的数据结构和分析能力。通过实现三个核心模块（EpicParser、DependencyAnalyzer、FileWatcher），系统获得了理解项目结构、优化并行执行、自动适应变更的能力。

## Objectives and Scope

### In Scope
- 解析 BMAD Epic 文档的 YAML frontmatter（epic_id, title, depends_on, priority, execution_mode, story_concurrency）
- 从 Epic Markdown 内容中提取 Story 列表和 Prerequisites
- 构建 Epic 级别的依赖关系 DAG
- 构建 Story 级别的依赖关系 DAG（支持 multi 模式）
- 检测循环依赖并拒绝无效 DAG
- 识别可并行执行的 Epics（所有依赖已完成）
- 识别排队等待的 Epics（存在未完成的依赖）
- 使用 watchdog 监控 Epic 文档目录变更
- 自动重新解析修改的 Epic 文件
- 支持 TUI 显示依赖关系和状态

### Out of Scope
- Epic 的实际执行调度（由 Epic 5 负责）
- Subagent 的启动和管理（由 Epic 6 负责）
- Git worktree 的创建和管理（由 Epic 4 负责）
- Quality Gate 检查（由 Epic 7 负责）
- TUI 的完整实现（由 Epic 8 负责，本 Epic 仅提供数据接口）

## System Architecture Alignment

本 Epic 实现的三个核心模块完全符合架构文档中的分层设计：

**Domain Layer（领域层）：**
- `EpicParser` 模块：负责解析 Epic 文档并生成 Epic、Story 领域对象
- `DependencyAnalyzer` 模块：负责 DAG 构建、依赖分析、拓扑排序等领域逻辑
- `DAG` 数据结构：表示依赖关系图，支持循环检测和拓扑排序

**Infrastructure Layer（基础设施层）：**
- `FileWatcher` 模块：使用 watchdog 库监控文件系统变更
- 集成 `ConfigManager`：读取 Epic 文档路径配置
- 集成 `StateManager`：持久化解析后的 Epic 状态

**Presentation Layer（展示层）：**
- 为 TUI 提供依赖查询 API（`get_parallel_epics`, `get_queued_epics`）
- 支持 CLI 命令调用解析和分析功能

**架构约束遵守：**
- NFR17：模块独立性 - EpicParser、DependencyAnalyzer、FileWatcher 三个模块职责清晰，接口明确
- NFR19：配置驱动 - Epic 文档路径通过 config.yaml 配置
- NFR20：完整日志 - 所有解析、分析、监控操作均记录日志

## Detailed Design

### Services and Modules

| 模块名称 | 职责 | 输入 | 输出 | Owner |
|---------|------|------|------|-------|
| **EpicParser** | 解析 BMAD Epic 文档，提取元数据和 Story 列表 | Epic 文档路径（`docs/epics/*.md`） | `List[Epic]`，包含完整元数据和 stories | Domain Layer |
| **DependencyAnalyzer** | 构建 DAG、分析依赖关系、识别可并行/排队的 Epics | `List[Epic]`，已完成的 Epic IDs | `DAG` 对象，可并行 Epic 列表，排队 Epic 列表 | Domain Layer |
| **FileWatcher** | 监控 Epic 文档目录变更，触发自动重新解析 | 监控目录路径，回调函数 | 文件变更事件（通过回调） | Infrastructure Layer |
| **Epic (领域对象)** | 表示单个 Epic 及其属性 | YAML frontmatter + Markdown 内容 | 领域对象实例 | Domain Model |
| **Story (领域对象)** | 表示单个 Story 及其依赖 | Epic 内的 Story 定义 | 领域对象实例 | Domain Model |
| **DAG (数据结构)** | 有向无环图，支持拓扑排序和循环检测 | Nodes（Epics/Stories），Edges（依赖关系） | 拓扑排序结果，并行节点集合 | Domain Data Structure |

#### EpicParser 模块

**关键方法：**
```python
class EpicParser:
    def parse_epics(self, project_path: str) -> List[Epic]:
        """解析项目的所有 Epic 文档"""

    def parse_single_epic(self, file_path: str) -> Optional[Epic]:
        """解析单个 Epic 文件"""

    def parse_stories(self, epic_content: str) -> List[Story]:
        """从 Epic Markdown 内容中提取 Story 列表"""

    def validate_epic_metadata(self, metadata: dict) -> bool:
        """验证 Epic YAML frontmatter 必填字段"""
```

**依赖：**
- `frontmatter` 库：解析 YAML frontmatter
- `markdown-it-py` 或 `mistune`：解析 Markdown 结构
- `ConfigManager`：获取 Epic 文档路径配置
- `Logger`：记录解析结果和错误

#### DependencyAnalyzer 模块

**关键方法：**
```python
class DependencyAnalyzer:
    def build_epic_dag(self, epics: List[Epic]) -> DAG:
        """构建 Epic 级别的依赖 DAG"""

    def build_story_dag(self, stories: List[Story]) -> DAG:
        """构建 Story 级别的依赖 DAG（multi 模式）"""

    def get_parallel_epics(self, dag: DAG, completed_ids: List[str]) -> List[Epic]:
        """返回所有依赖已满足的可并行 Epics"""

    def get_queued_epics(self, dag: DAG, completed_ids: List[str]) -> List[Tuple[Epic, List[str]]]:
        """返回排队的 Epics 及其缺失的依赖列表"""

    def validate_dag(self, dag: DAG) -> Tuple[bool, Optional[str]]:
        """验证 DAG 有效性，检测循环依赖"""
```

**依赖：**
- `DAG` 数据结构
- `Logger`：记录 DAG 构建和验证结果

#### FileWatcher 模块

**关键方法：**
```python
class FileWatcher:
    def __init__(self, watch_path: str, callback: Callable[[str], None]):
        """初始化文件监控器"""

    def start(self):
        """开始监控文件变更"""

    def stop(self):
        """停止监控"""

    def _debounce(self, file_path: str):
        """防抖处理，1秒内多次变更只触发一次回调"""
```

**依赖：**
- `watchdog` 库：跨平台文件监控
- `Logger`：记录文件变更事件

### Data Models and Contracts

#### Epic 领域模型

```python
@dataclass
class Epic:
    id: str                          # Epic ID (如 "3")
    title: str                       # Epic 标题
    description: str                 # 从 Markdown 内容提取的描述
    depends_on: List[str]            # 依赖的 Epic IDs
    priority: str                    # HIGH/MEDIUM/LOW
    execution_mode: str              # single/multi/auto
    story_concurrency: int           # multi 模式下的并发 Story 数
    stories: List[Story]             # Epic 包含的 Story 列表
    status: str                      # backlog/contexted/developing/completed/failed
    progress: float                  # 0.0-1.0
    agent_id: Optional[str]          # 执行该 Epic 的 Subagent ID
    worktree_path: Optional[str]     # Git worktree 路径
    created_at: datetime
    updated_at: datetime

    # 验证方法
    def validate(self) -> Tuple[bool, Optional[str]]:
        """验证 Epic 数据完整性"""
        if not self.id or not self.title:
            return False, "Missing required field: id or title"
        return True, None
```

#### Story 领域模型

```python
@dataclass
class Story:
    id: str                          # Story ID (如 "3.1")
    title: str                       # Story 标题
    description: str                 # Story 描述
    prerequisites: List[str]         # 依赖的其他 Story IDs（同一 Epic 内）
    status: str                      # backlog/drafted/ready-for-dev/in-progress/review/done
    commit_hash: Optional[str]       # 完成后的 Git commit hash
    agent_id: Optional[str]          # 执行该 Story 的 Subagent ID（multi 模式）

    # 验证方法
    def validate(self, epic_stories: List[str]) -> Tuple[bool, Optional[str]]:
        """验证 Story 的 prerequisites 是否都存在于 Epic 内"""
        for prereq in self.prerequisites:
            if prereq not in epic_stories:
                return False, f"Invalid prerequisite: {prereq} not in Epic"
        return True, None
```

#### DAG 数据结构

```python
class DAG:
    """有向无环图（Directed Acyclic Graph）"""

    def __init__(self):
        self.nodes: Dict[str, Any] = {}           # Node ID → Node (Epic or Story)
        self.edges: Dict[str, List[str]] = {}     # Node ID → List of dependency IDs
        self.reverse_edges: Dict[str, List[str]] = {}  # Node ID → List of dependent IDs

    def add_node(self, node_id: str, node: Any):
        """添加节点"""
        self.nodes[node_id] = node
        if node_id not in self.edges:
            self.edges[node_id] = []
        if node_id not in self.reverse_edges:
            self.reverse_edges[node_id] = []

    def add_edge(self, from_id: str, to_id: str):
        """添加边：from_id 依赖 to_id"""
        if from_id not in self.edges:
            self.edges[from_id] = []
        self.edges[from_id].append(to_id)

        if to_id not in self.reverse_edges:
            self.reverse_edges[to_id] = []
        self.reverse_edges[to_id].append(from_id)

    def has_cycle(self) -> bool:
        """使用 DFS 检测循环依赖"""
        visited = set()
        rec_stack = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for dep_id in self.edges.get(node_id, []):
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True  # 发现循环

            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        return False

    def topological_sort(self) -> List[Any]:
        """拓扑排序，返回节点执行顺序"""
        in_degree = {node_id: 0 for node_id in self.nodes}
        for deps in self.edges.values():
            for dep_id in deps:
                in_degree[dep_id] += 1

        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(self.nodes[node_id])

            for dependent_id in self.reverse_edges.get(node_id, []):
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        return result

    def get_parallel_nodes(self, completed_ids: Set[str]) -> List[Any]:
        """返回所有依赖已满足的可并行节点"""
        parallel = []
        for node_id, node in self.nodes.items():
            if node_id in completed_ids:
                continue  # 已完成，跳过

            # 检查所有依赖是否都已完成
            deps = self.edges.get(node_id, [])
            if all(dep_id in completed_ids for dep_id in deps):
                parallel.append(node)

        return parallel
```

#### Epic YAML Frontmatter 格式

```yaml
---
epic_id: 3
title: "Epic Parsing and Dependency Analysis"
depends_on: [1]                    # Epic 依赖列表
priority: HIGH                     # HIGH/MEDIUM/LOW
execution_mode: multi              # single/multi/auto
story_concurrency: 3               # multi 模式下并发 Story 数
---

# Epic 内容（Markdown）
...
```

### APIs and Interfaces

#### EpicParser API

```python
# 主要接口
def parse_epics(project_path: str) -> List[Epic]:
    """
    解析项目的所有 Epic 文档

    Args:
        project_path: 项目根路径

    Returns:
        List[Epic]: 解析成功的 Epic 列表

    Raises:
        InvalidEpicError: 当 Epic 文档格式无效时
    """

def parse_single_epic(file_path: str) -> Optional[Epic]:
    """
    解析单个 Epic 文件

    Args:
        file_path: Epic 文件的绝对路径

    Returns:
        Epic 对象，如果解析失败则返回 None
    """

# 内部方法
def _extract_yaml_frontmatter(content: str) -> dict:
    """提取并解析 YAML frontmatter"""

def _parse_markdown_stories(content: str) -> List[Story]:
    """从 Markdown 中提取 Story 列表"""

def _validate_metadata(metadata: dict) -> Tuple[bool, Optional[str]]:
    """验证 Epic 元数据完整性"""
```

#### DependencyAnalyzer API

```python
# Epic DAG 相关
def build_epic_dag(epics: List[Epic]) -> DAG:
    """
    构建 Epic 依赖 DAG

    Args:
        epics: Epic 列表

    Returns:
        DAG 对象

    Raises:
        CircularDependencyError: 检测到循环依赖时
        InvalidDependencyError: 依赖的 Epic 不存在时
    """

def get_parallel_epics(dag: DAG, completed_epic_ids: List[str]) -> List[Epic]:
    """
    获取可并行执行的 Epics

    Args:
        dag: Epic DAG
        completed_epic_ids: 已完成的 Epic ID 列表

    Returns:
        所有依赖已满足的 Epic 列表
    """

def get_queued_epics(dag: DAG, completed_epic_ids: List[str]) -> List[Tuple[Epic, List[str]]]:
    """
    获取排队等待的 Epics

    Args:
        dag: Epic DAG
        completed_epic_ids: 已完成的 Epic ID 列表

    Returns:
        (Epic, 缺失的依赖 ID 列表) 元组列表
    """

# Story DAG 相关
def build_story_dag(stories: List[Story]) -> DAG:
    """
    构建 Story 依赖 DAG（用于 multi 模式）

    Args:
        stories: Story 列表（来自同一 Epic）

    Returns:
        DAG 对象

    Raises:
        CircularDependencyError: 检测到循环依赖时
        InvalidPrerequisiteError: prerequisites 不存在时
    """

def get_parallel_stories(dag: DAG, completed_story_ids: List[str]) -> List[Story]:
    """获取可并行执行的 Stories"""

# 验证相关
def validate_dag(dag: DAG) -> Tuple[bool, Optional[str]]:
    """
    验证 DAG 有效性

    Returns:
        (是否有效, 错误信息)
    """
```

#### FileWatcher API

```python
class FileWatcher:
    def __init__(self, watch_path: str, callback: Callable[[str], None],
                 debounce_seconds: float = 1.0):
        """
        初始化文件监控器

        Args:
            watch_path: 监控的目录路径
            callback: 文件变更时的回调函数，参数为变更的文件路径
            debounce_seconds: 防抖延迟时间（秒）
        """

    def start(self) -> None:
        """开始监控文件变更"""

    def stop(self) -> None:
        """停止监控"""

    def is_running(self) -> bool:
        """返回监控器是否正在运行"""
```

#### 错误码定义

```python
class EpicParsingError(Exception):
    """Epic 解析错误基类"""
    pass

class InvalidEpicError(EpicParsingError):
    """Epic 文档格式无效"""
    ERROR_CODE = "EP001"

class CircularDependencyError(Exception):
    """循环依赖错误"""
    ERROR_CODE = "DA001"

class InvalidDependencyError(Exception):
    """依赖的 Epic/Story 不存在"""
    ERROR_CODE = "DA002"

class InvalidPrerequisiteError(Exception):
    """Story 的 prerequisite 不存在"""
    ERROR_CODE = "DA003"
```

### Workflows and Sequencing

#### 工作流 1：Epic 文档解析流程

```
用户命令 → CLI
    ↓
EpicParser.parse_epics(project_path)
    ↓
遍历 docs/epics/*.md 文件
    ↓
对每个文件：
    1. 读取文件内容
    2. 提取 YAML frontmatter
    3. 验证必填字段 (epic_id, title)
    4. 解析 Markdown 内容，提取 Story 列表
    5. 创建 Epic 对象
    ↓
返回 List[Epic]
    ↓
StateManager 持久化 Epic 数据
    ↓
日志记录：解析成功的 Epic 数量
```

#### 工作流 2：DAG 构建和依赖分析流程

```
Scheduler.start_epics() 调用
    ↓
DependencyAnalyzer.build_epic_dag(epics)
    ↓
1. 创建 DAG 实例
2. 遍历 Epics：
   - dag.add_node(epic.id, epic)
   - 遍历 epic.depends_on:
     - 验证依赖的 Epic 存在
     - dag.add_edge(epic.id, dep_id)
3. 验证 DAG：
   - 检测循环依赖 (DFS)
   - 如果发现循环，抛出 CircularDependencyError
    ↓
返回 DAG 对象
    ↓
Scheduler 调用 get_parallel_epics(dag, completed_ids)
    ↓
遍历 DAG 节点：
   - 如果所有 depends_on 都在 completed_ids 中
   - 且当前 Epic 状态不是 completed
   - 添加到可并行列表
    ↓
返回可并行 Epic 列表
    ↓
Scheduler 为每个可并行 Epic 创建 Worktree 并启动 Subagent
```

#### 工作流 3：文件监控和自动刷新流程

```
AEDT 启动
    ↓
初始化 FileWatcher(watch_path="docs/epics/", callback=on_epic_changed)
    ↓
FileWatcher.start()
    ↓
watchdog 监听文件系统事件
    ↓
检测到文件变更 (CREATE/MODIFY/DELETE)
    ↓
Debounce 处理（1秒延迟）
    ↓
触发回调：on_epic_changed(file_path)
    ↓
EpicParser.parse_single_epic(file_path)
    ↓
更新 StateManager 中的 Epic 数据
    ↓
通知 TUI 刷新显示
    ↓
日志记录：Epic X updated and re-parsed
```

#### 工作流 4：Story-level DAG 构建（Multi 模式）

```
Epic 执行模式 = multi
    ↓
DependencyAnalyzer.build_story_dag(epic.stories)
    ↓
1. 创建 DAG 实例
2. 遍历 Stories：
   - dag.add_node(story.id, story)
   - 遍历 story.prerequisites:
     - 验证 prerequisite 存在于同一 Epic 内
     - dag.add_edge(story.id, prereq_id)
3. 验证 DAG：
   - 检测循环依赖
   - 验证所有 prerequisites 都存在
    ↓
返回 Story DAG
    ↓
调用 get_parallel_stories(dag, completed_story_ids)
    ↓
返回可并行的 Story 列表
    ↓
为每个可并行 Story 启动独立 Subagent
```

#### 序列图：Epic 解析和调度

```
┌─────┐     ┌──────────┐     ┌────────────────┐     ┌──────────┐     ┌─────────┐
│ CLI │     │ Scheduler│     │DependencyAnalyzer│    │EpicParser│     │StateManager│
└──┬──┘     └────┬─────┘     └────────┬───────┘     └────┬─────┘     └────┬────┘
   │             │                    │                   │                │
   │ start_epics │                    │                   │                │
   │─────────────>                    │                   │                │
   │             │                    │                   │                │
   │             │ parse_epics()      │                   │                │
   │             │────────────────────────────────────────>                │
   │             │                    │                   │                │
   │             │                    │         List[Epic]│                │
   │             │<────────────────────────────────────────                │
   │             │                    │                   │                │
   │             │ build_epic_dag()   │                   │                │
   │             │───────────────────>│                   │                │
   │             │                    │                   │                │
   │             │ validate_dag()     │                   │                │
   │             │───────────────────>│                   │                │
   │             │                    │                   │                │
   │             │           DAG      │                   │                │
   │             │<───────────────────│                   │                │
   │             │                    │                   │                │
   │             │ get_parallel_epics()                   │                │
   │             │───────────────────>│                   │                │
   │             │                    │                   │                │
   │             │      List[Epic]    │                   │                │
   │             │<───────────────────│                   │                │
   │             │                    │                   │                │
   │             │ 为每个 Epic 创建 Worktree 和 Subagent   │                │
   │             │─────────────────────────────────────────────────────────>│
   │             │                    │                   │                │
```

## Non-Functional Requirements

### Performance

**NFR5 - 文件监控性能**
- Epic 文档变更检测延迟 < 1 秒
- 使用 watchdog 高效监控机制（事件驱动，非轮询）
- Debounce 机制：1 秒内多次变更只触发一次解析
- 性能目标：监控 100+ Epic 文件时，CPU 占用 < 5%

**NFR6 - 大项目支持**
- 支持 5-10 个并发项目
- 每个项目支持 50+ Epics
- 100+ 总 Epic 数量时，TUI 响应时间 < 200ms
- DAG 构建时间：100 Epics < 100ms
- 解析性能：单个 Epic 文档解析 < 50ms

**性能优化策略：**
- Epic 解析结果缓存（基于文件修改时间）
- DAG 增量更新（仅重新计算受影响的节点）
- 惰性加载：仅在需要时解析 Story 列表

### Security

**数据安全：**
- Epic 文档仅从本地文件系统读取，不涉及网络传输
- 不存储敏感信息（密码、API 密钥等）
- 文件路径验证：防止路径遍历攻击
  ```python
  def validate_path(file_path: str, base_path: str) -> bool:
      """验证文件路径在允许的目录内"""
      resolved_path = os.path.realpath(file_path)
      resolved_base = os.path.realpath(base_path)
      return resolved_path.startswith(resolved_base)
  ```

**输入验证：**
- YAML frontmatter 验证：防止 YAML 反序列化漏洞
- 使用 `safe_load()` 而非 `load()` 加载 YAML
- Epic ID 格式验证：仅允许数字和字母，长度 < 50 字符
- 依赖关系验证：防止注入恶意 Epic ID

**权限控制：**
- FileWatcher 仅监控配置的目录，不监控系统目录
- 文件读取使用最小权限原则

### Reliability/Availability

**NFR16 - 可靠性要求**

**错误处理：**
- Epic 解析失败不阻塞其他 Epic 的解析
- 单个文件格式错误时记录警告并跳过，继续解析其他文件
- DAG 构建失败时提供清晰的错误消息（指出哪个 Epic 导致循环依赖）

**容错机制：**
- FileWatcher 崩溃时自动重启监控
- 文件读取失败时重试 3 次（间隔 100ms）
- 解析错误不导致系统崩溃

**数据一致性：**
- Epic 状态持久化采用原子写入（来自 Epic 1 的 StateManager）
- 文件监控事件去重，防止重复触发解析
- DAG 构建使用事务性操作（全部成功或全部失败）

**可用性保证：**
- Epic 解析模块独立运行，不依赖外部服务
- 离线可用（不需要网络连接）
- 系统重启后自动恢复监控状态

**回退策略：**
- Epic 文档格式错误时使用上一次成功解析的结果
- 提供手动重新解析命令 `aedt refresh-epics`

### Observability

**NFR20 - 日志完整性**

**日志级别和内容：**
- **DEBUG**：每个 Epic 文件的详细解析过程
- **INFO**：Epic 解析成功、DAG 构建完成、文件监控启动
- **WARNING**：Epic 文档格式错误、缺失必填字段、依赖的 Epic 不存在
- **ERROR**：循环依赖检测、文件读取失败、DAG 构建失败

**关键操作日志示例：**
```
INFO  [EpicParser] Parsing 8 Epic documents from docs/epics/
INFO  [EpicParser] Successfully parsed Epic 3: Epic Parsing and Dependency Analysis
WARN  [EpicParser] Epic 5 missing required field: depends_on
INFO  [DependencyAnalyzer] Building Epic DAG for 8 Epics
ERROR [DependencyAnalyzer] Circular dependency detected: Epic 2 → Epic 3 → Epic 2
INFO  [FileWatcher] Started monitoring docs/epics/ for changes
INFO  [FileWatcher] Detected change in epic-003-parsing.md, re-parsing...
INFO  [EpicParser] Epic 3 updated and re-parsed successfully
```

**监控指标：**
- Epic 解析成功率（成功数/总数）
- DAG 构建时间
- 文件监控事件数量
- 解析错误次数（按错误类型分组）

**追踪能力：**
- 每个 Epic 解析记录时间戳和文件路径
- DAG 构建记录输入 Epic 列表和输出节点数
- 文件监控事件记录触发文件和处理结果

**调试支持：**
- 提供 `--verbose` 模式输出详细解析日志
- Epic 解析失败时输出完整的 YAML frontmatter 内容
- DAG 验证失败时输出完整的依赖关系图

## Dependencies and Integrations

### 外部依赖库

| 依赖库 | 版本要求 | 用途 | 许可证 |
|--------|---------|------|--------|
| **python-frontmatter** | >=1.0.0 | 解析 Markdown 文件的 YAML frontmatter | MIT |
| **markdown-it-py** | >=2.0.0 | 解析 Markdown 内容，提取 Story 列表 | MIT |
| **PyYAML** | >=6.0 | YAML 解析（已存在于项目中） | MIT |
| **watchdog** | >=3.0.0 | 跨平台文件监控（已存在于项目中） | Apache 2.0 |

**新增依赖（Epic 3 引入）：**
```txt
# requirements.txt 需要添加：
python-frontmatter>=1.0.0
markdown-it-py>=2.0.0
```

### 内部模块集成

#### 依赖的 Epic 1 模块

| 模块 | 接口 | 用途 |
|------|------|------|
| **ConfigManager** | `get_config()` | 获取 Epic 文档路径配置 |
| **StateManager** | `save_state()`, `load_state()` | 持久化 Epic 解析结果 |
| **Logger** | `log_info()`, `log_error()`, `log_warning()` | 记录解析和分析日志 |

#### 提供给其他 Epic 的接口

| 接口 | 消费者 | 用途 |
|------|--------|------|
| `EpicParser.parse_epics()` | Epic 5 (Scheduler) | 获取项目的所有 Epic |
| `DependencyAnalyzer.build_epic_dag()` | Epic 5 (Scheduler) | 构建 Epic 依赖图 |
| `DependencyAnalyzer.get_parallel_epics()` | Epic 5 (Scheduler) | 获取可并行执行的 Epics |
| `DependencyAnalyzer.get_queued_epics()` | Epic 8 (TUI) | 显示排队等待的 Epics |
| `DependencyAnalyzer.build_story_dag()` | Epic 6 (Subagent) | 多模式下构建 Story DAG |

### 集成点详细说明

#### 1. 与 ConfigManager 集成

```python
# Epic 3 从 ConfigManager 读取配置
config = ConfigManager.get_config()
epic_docs_path = config.get("epic_docs_path", "docs/epics/")
```

**配置项（需在 .aedt/config.yaml 中定义）：**
```yaml
epic_docs_path: "docs/epics/"          # Epic 文档目录
epic_file_pattern: "epic-*.md"         # Epic 文件名模式
enable_file_watching: true             # 是否启用文件监控
file_watch_debounce: 1.0               # 防抖延迟（秒）
```

#### 2. 与 StateManager 集成

```python
# Epic 3 持久化解析结果
state_manager = StateManager()
state_manager.save_state("parsed_epics", epics)
state_manager.save_state("epic_dag", dag)

# Epic 5 读取 Epic 数据
epics = state_manager.load_state("parsed_epics")
```

**持久化数据结构：**
```yaml
# .aedt/projects/{project-id}/state.yaml
parsed_epics:
  - id: "3"
    title: "Epic Parsing and Dependency Analysis"
    depends_on: ["1"]
    status: "backlog"
    stories: [...]

epic_dag:
  nodes: {...}
  edges: {...}
```

#### 3. 与 Epic 5 (Scheduler) 集成

```python
# Scheduler 调用 Epic 3 的分析能力
from aedt.domain.epic_parser import EpicParser
from aedt.domain.dependency_analyzer import DependencyAnalyzer

# 解析 Epics
parser = EpicParser()
epics = parser.parse_epics(project_path)

# 构建 DAG
analyzer = DependencyAnalyzer()
dag = analyzer.build_epic_dag(epics)

# 获取可并行 Epics
completed_ids = ["1"]
parallel_epics = analyzer.get_parallel_epics(dag, completed_ids)

# Scheduler 为每个并行 Epic 创建 worktree 和 subagent
for epic in parallel_epics:
    scheduler.start_epic(epic)
```

#### 4. 与 Epic 8 (TUI) 集成

```python
# TUI 显示 Epic 依赖关系
from aedt.domain.dependency_analyzer import DependencyAnalyzer

analyzer = DependencyAnalyzer()
queued_epics = analyzer.get_queued_epics(dag, completed_ids)

# 在 TUI 中显示
for epic, missing_deps in queued_epics:
    tui.display(f"Epic {epic.id}: Waiting for {missing_deps}")
```

### 数据流图

```
┌─────────────────┐
│ Epic Documents  │
│ (docs/epics/)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  EpicParser     │◄───── ConfigManager (读取路径配置)
└────────┬────────┘
         │ List[Epic]
         ▼
┌─────────────────┐
│ StateManager    │◄───── 持久化 Epic 数据
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│DependencyAnalyzer│
└────────┬────────┘
         │ DAG
         ├─────────────────────┐
         ▼                     ▼
┌─────────────────┐    ┌─────────────────┐
│ Epic 5          │    │ Epic 8          │
│ (Scheduler)     │    │ (TUI)           │
└─────────────────┘    └─────────────────┘
  创建 Worktree          显示依赖关系
  启动 Subagent          显示排队状态
```

### 版本兼容性

- **Python**: 3.9+（使用了 typing 的新特性）
- **操作系统**: macOS, Linux, Windows（watchdog 跨平台支持）
- **Git**: 2.15+（Epic 4 需要 worktree 功能）

## Acceptance Criteria (Authoritative)

### AC1: Epic 文档解析

**Given** 项目目录下存在 `docs/epics/epic-003-parsing.md` 文件，包含有效的 YAML frontmatter
**When** 调用 `EpicParser.parse_epics(project_path)`
**Then** 返回包含 Epic 对象的列表
**And** Epic 对象包含：id="3", title="Epic Parsing and Dependency Analysis", depends_on=["1"], priority="HIGH"

### AC2: 无效 Epic 文档处理

**Given** Epic 文件的 YAML frontmatter 缺少必填字段 `epic_id`
**When** 解析该文件
**Then** 记录 WARNING 日志："Epic file <path> missing required field: epic_id"
**And** 该 Epic 不被添加到解析结果中
**And** 继续解析其他 Epic 文件

### AC3: Story 列表提取

**Given** Epic 文档包含 "Stories" 章节，有 8 个编号的 Story
**When** 解析该 Epic
**Then** Epic.stories 列表包含 8 个 Story 对象
**And** 每个 Story 包含：id (如 "3.1"), title, description, prerequisites

### AC4: Epic 依赖 DAG 构建

**Given** 4 个 Epics，依赖关系为：Epic 1: [], Epic 2: [1], Epic 3: [1], Epic 4: [2, 3]
**When** 调用 `DependencyAnalyzer.build_epic_dag(epics)`
**Then** 返回的 DAG 包含 4 个节点
**And** DAG.edges 正确表示依赖关系
**And** Epic 1 的 in_degree = 0（无依赖）
**And** Epic 4 的 in_degree = 2（依赖 Epic 2 和 3）

### AC5: 循环依赖检测

**Given** Epic 2 depends_on=[3]，Epic 3 depends_on=[2]（循环依赖）
**When** 调用 `build_epic_dag(epics)`
**Then** 抛出 `CircularDependencyError`
**And** 错误消息包含："Circular dependency detected: Epic 2 ↔ Epic 3"
**And** DAG 不被创建

### AC6: 识别可并行 Epics

**Given** DAG 包含 Epic 1, 2, 3，其中 Epic 1 无依赖，Epic 2 和 3 依赖 Epic 1
**And** Epic 1 已完成 (completed_ids = ["1"])
**When** 调用 `get_parallel_epics(dag, ["1"])`
**Then** 返回 [Epic 2, Epic 3]（都可以并行执行）

### AC7: 识别排队等待的 Epics

**Given** Epic 4 depends_on=[2, 3]
**And** Epic 2 已完成，Epic 3 仍在开发中 (completed_ids = ["2"])
**When** 调用 `get_queued_epics(dag, ["2"])`
**Then** 返回 [(Epic 4, ["3"])]（Epic 4 排队，等待 Epic 3）

### AC8: Story 依赖 DAG 构建

**Given** Epic 包含 3 个 Stories，Story 3.2 prerequisites=["3.1"], Story 3.3 prerequisites=["3.1", "3.2"]
**When** 调用 `build_story_dag(epic.stories)`
**Then** 返回的 Story DAG 正确表示依赖关系
**And** Story 3.1 可立即执行
**And** Story 3.2 必须等待 Story 3.1
**And** Story 3.3 必须等待 Story 3.1 和 3.2

### AC9: 文件监控启动

**Given** AEDT 初始化完成
**When** 调用 `FileWatcher(watch_path="docs/epics/", callback=on_epic_changed).start()`
**Then** watchdog 开始监控 `docs/epics/` 目录
**And** 记录 INFO 日志："Started monitoring docs/epics/ for changes"

### AC10: 文件变更自动解析

**Given** FileWatcher 正在运行
**When** 修改 `docs/epics/epic-003-parsing.md` 文件并保存
**Then** 在 1 秒内检测到变更
**And** 触发回调 `on_epic_changed("docs/epics/epic-003-parsing.md")`
**And** 重新解析该 Epic
**And** 更新 StateManager 中的 Epic 数据
**And** 记录 INFO 日志："Epic 3 updated and re-parsed"

### AC11: Debounce 防抖处理

**Given** FileWatcher 正在运行，debounce_seconds = 1.0
**When** 在 0.5 秒内连续修改同一文件 3 次
**Then** 仅触发 1 次回调（最后一次修改后 1 秒）
**And** 避免重复解析

### AC12: 无效 Story Prerequisites 验证

**Given** Story 3.2 prerequisites=["3.9"]（Story 3.9 不存在于 Epic 3）
**When** 调用 `build_story_dag(epic.stories)`
**Then** 抛出 `InvalidPrerequisiteError`
**And** 错误消息包含："Invalid prerequisite: 3.9 not in Epic"

## Traceability Mapping

| AC# | 规格章节 | 组件/API | 测试策略 | FR 映射 |
|-----|---------|---------|---------|---------|
| AC1 | Detailed Design → EpicParser | `EpicParser.parse_epics()` | 单元测试：解析有效 Epic 文档 | FR6 |
| AC2 | NFR → Reliability → 错误处理 | `EpicParser._validate_metadata()` | 单元测试：缺失必填字段处理 | FR6 |
| AC3 | Detailed Design → EpicParser | `EpicParser.parse_stories()` | 单元测试：提取 Story 列表 | FR13 |
| AC4 | Detailed Design → DependencyAnalyzer | `DependencyAnalyzer.build_epic_dag()` | 单元测试：构建正确的 DAG | FR7 |
| AC5 | NFR → Reliability → 验证 | `DAG.has_cycle()` | 单元测试：循环依赖检测 | FR7 |
| AC6 | Detailed Design → DependencyAnalyzer | `DependencyAnalyzer.get_parallel_epics()` | 单元测试：识别可并行 Epics | FR8 |
| AC7 | Detailed Design → DependencyAnalyzer | `DependencyAnalyzer.get_queued_epics()` | 单元测试：识别排队 Epics | FR9 |
| AC8 | Detailed Design → DependencyAnalyzer | `DependencyAnalyzer.build_story_dag()` | 单元测试：Story DAG 构建 | FR25 |
| AC9 | Detailed Design → FileWatcher | `FileWatcher.start()` | 集成测试：启动文件监控 | FR12 |
| AC10 | Workflows → 文件监控流程 | `FileWatcher` + `EpicParser` | 集成测试：文件变更触发解析 | FR12 |
| AC11 | NFR → Performance → Debounce | `FileWatcher._debounce()` | 单元测试：防抖处理 | NFR5 |
| AC12 | NFR → Reliability → 验证 | `Story.validate()` | 单元测试：Prerequisites 验证 | FR25 |

### FR 覆盖率矩阵

| FR | 描述 | AC 编号 | 实现组件 | 状态 |
|----|------|---------|---------|------|
| FR6 | Epic 文档读取和解析 | AC1, AC2 | EpicParser | ✅ 已规划 |
| FR7 | 依赖关系提取和 DAG 构建 | AC4, AC5 | DependencyAnalyzer | ✅ 已规划 |
| FR8 | 并行 Epic 识别 | AC6 | DependencyAnalyzer.get_parallel_epics | ✅ 已规划 |
| FR9 | Epic 排队管理 | AC7 | DependencyAnalyzer.get_queued_epics | ✅ 已规划 |
| FR10 | 依赖关系查看 | - | 为 TUI 提供数据接口（Epic 8 实现） | 🔄 接口已规划 |
| FR12 | Epic 文档变更监控 | AC9, AC10, AC11 | FileWatcher | ✅ 已规划 |
| FR13 | Story 列表提取 | AC3 | EpicParser.parse_stories | ✅ 已规划 |
| FR25 | 自动调度 Epic 启动 | AC8 | DependencyAnalyzer.build_story_dag | ✅ 已规划 |

### NFR 验证映射

| NFR | AC/测试用例 | 验证方法 |
|-----|------------|---------|
| NFR5 (文件监控性能) | AC10, AC11 | 性能测试：100 个 Epic 文件，监控延迟 < 1s |
| NFR6 (大项目支持) | AC4 | 性能测试：100 Epics DAG 构建 < 100ms |
| NFR16 (可靠性) | AC2, AC5, AC12 | 单元测试：错误处理和验证逻辑 |
| NFR17 (模块独立性) | - | 代码审查：模块接口清晰，无循环依赖 |
| NFR20 (日志完整性) | AC1-AC12 | 集成测试：所有操作都有日志记录 |

## Risks, Assumptions, Open Questions

### 风险 (Risks)

| ID | 风险描述 | 影响 | 可能性 | 缓解措施 |
|----|---------|------|-------|---------|
| R1 | **Epic 文档格式不一致**：用户手动编写 Epic 文档，可能格式不规范 | 中 | 高 | 提供 Epic 模板和验证工具；完善的错误消息指导用户修正 |
| R2 | **大规模 DAG 性能**：100+ Epics 时 DAG 构建可能超时 | 中 | 低 | 性能测试验证；实现缓存和增量更新；如果必要，使用更高效的 DAG 算法 |
| R3 | **文件监控失败**：watchdog 在某些文件系统上可能不稳定 | 低 | 低 | 提供手动刷新命令 `aedt refresh-epics`；监控失败时记录错误并提示用户 |
| R4 | **Markdown 解析库兼容性**：不同 Markdown 格式可能解析失败 | 低 | 中 | 使用广泛支持的 markdown-it-py；提供回退机制（基于正则表达式的简单解析） |
| R5 | **Story prerequisites 复杂度**：复杂的 Story 依赖图可能导致调度困难 | 中 | 中 | 限制 Story prerequisites 深度（建议 < 3 层）；提供可视化工具帮助理解依赖 |

### 假设 (Assumptions)

| ID | 假设内容 | 验证方式 |
|----|---------|---------|
| A1 | **Epic 文档遵循 BMAD 格式**：所有 Epic 文档包含有效的 YAML frontmatter | Story 3.1 单元测试验证各种格式 |
| A2 | **Epic 文档存储在本地文件系统**：不支持远程 URL 或 Git 仓库直接访问 | 架构设计评审确认 |
| A3 | **Epic ID 唯一性**：每个 Epic 的 epic_id 在项目内唯一 | 解析时验证，重复 ID 报错 |
| A4 | **Story ID 格式**：Story ID 格式为 `{epic_id}.{story_num}`（如 "3.1", "3.2"） | Story 3.2 解析逻辑验证 |
| A5 | **文件系统支持 watchdog**：目标操作系统（macOS, Linux, Windows）都支持文件监控 | 集成测试在三个平台上验证 |
| A6 | **Epic 数量规模**：单个项目 Epic 数量 < 100 | PRD 需求和架构设计确认 |
| A7 | **DAG 无环性**：用户不会故意创建循环依赖 | 验证逻辑检测并拒绝循环依赖 |

### 待解决问题 (Open Questions)

| ID | 问题 | 重要性 | 负责人 | 目标日期 |
|----|------|-------|-------|---------|
| Q1 | **Story prerequisites 格式**：是否支持 YAML 列表格式 `prerequisites: [3.1, 3.2]` 还是仅支持 Markdown 文本？ | 高 | Tech Lead | Sprint 开始前 |
| Q2 | **Epic 文档更新冲突**：如果 Epic 正在执行时文档被修改，如何处理？ | 中 | Architect | Story 3.8 实现前 |
| Q3 | **缓存策略**：Epic 解析结果缓存何时失效？仅基于文件修改时间还是内容哈希？ | 低 | Developer | Story 3.1 实现时 |
| Q4 | **多项目支持**：不同项目的 Epic 文档路径配置如何管理？ | 中 | PM | Epic 2 实现时明确 |
| Q5 | **Story 并发限制**：`story_concurrency` 是否应该有上限（如最大 10）？ | 低 | Tech Lead | Story 3.2 实现前 |

## Test Strategy Summary

### 测试层次和覆盖范围

#### 1. 单元测试 (Unit Tests)

**目标覆盖率：** 90%

**关键测试模块：**

- **EpicParser 模块**
  - 测试有效 Epic 文档解析（AC1）
  - 测试无效 YAML frontmatter 处理（AC2）
  - 测试 Story 列表提取（AC3）
  - 测试缺失必填字段的错误处理
  - 测试 Epic ID 格式验证
  - 边界测试：空文件、超大文件（10MB+）

- **DependencyAnalyzer 模块**
  - 测试 Epic DAG 构建（AC4）
  - 测试循环依赖检测（AC5）
  - 测试可并行 Epics 识别（AC6）
  - 测试排队 Epics 识别（AC7）
  - 测试 Story DAG 构建（AC8）
  - 测试无效依赖处理（AC12）
  - 边界测试：空 DAG、单节点 DAG、100+ 节点 DAG

- **DAG 数据结构**
  - 测试节点添加和边添加
  - 测试 has_cycle() 算法正确性
  - 测试 topological_sort() 正确性
  - 测试 get_parallel_nodes() 逻辑

- **FileWatcher 模块**
  - 测试监控启动和停止（AC9）
  - 测试 Debounce 机制（AC11）
  - Mock watchdog 事件验证回调触发

**测试框架：** pytest + pytest-mock + pytest-cov

#### 2. 集成测试 (Integration Tests)

**测试场景：**

- **端到端 Epic 解析流程**
  - 创建真实的 Epic 文档 → 解析 → 构建 DAG → 识别可并行 Epics
  - 验证与 StateManager 的集成
  - 验证日志记录完整性

- **文件监控自动刷新**（AC10）
  - 启动 FileWatcher → 修改 Epic 文件 → 验证自动重新解析
  - 验证多个文件并发修改的处理

- **多 Epic 依赖场景**
  - 创建 8 个 Epics（模拟实际项目）→ 构建完整 DAG → 验证拓扑排序

- **错误恢复测试**
  - Epic 文档格式错误 → 验证系统继续运行
  - DAG 构建失败 → 验证错误消息和状态

#### 3. 性能测试 (Performance Tests)

**性能基准：**

| 测试场景 | 目标性能 | 测试数据 |
|---------|---------|---------|
| Epic 文档解析 | 单个 < 50ms | 10KB Epic 文档，包含 8 个 Stories |
| DAG 构建 | 100 Epics < 100ms | 100 个 Epics，平均依赖度 2 |
| 文件监控延迟 | < 1 秒 | 100 个 Epic 文件监控 |
| 内存占用 | < 100MB | 100 Epics + 500 Stories |

**性能测试工具：** pytest-benchmark

#### 4. 边界和负载测试

**边界条件：**
- 空 Epic 文档（0 Stories）
- 超大 Epic（100+ Stories）
- 深层依赖链（Epic 1 → 2 → 3 → 4 → 5）
- 宽依赖（Epic N 依赖 Epic 1-10）
- 特殊字符在 Epic ID 和 title 中

**负载测试：**
- 100 Epics 并发解析
- 1000 次文件修改事件（压力测试 FileWatcher）

#### 5. 安全测试

**测试用例：**
- 路径遍历攻击：`epic_docs_path: "../../../etc/passwd"`
- YAML 反序列化漏洞：恶意 YAML payload
- Epic ID 注入：`epic_id: "'; DROP TABLE epics; --"`
- 超长字符串：epic_id 长度 > 10000 字符

### 测试数据和 Fixtures

**Fixtures 结构：**
```
tests/
  fixtures/
    epics/
      valid-epic-001.md           # 有效的 Epic 文档
      invalid-missing-id.md       # 缺少 epic_id
      invalid-circular-dep.md     # 循环依赖
      large-epic-100-stories.md   # 大规模 Epic
    expected-dags/
      dag-4-epics.json            # 预期的 DAG 结构
```

### 测试自动化

**CI/CD 集成：**
- 每次提交触发单元测试
- PR 合并前运行集成测试和性能测试
- 每日运行完整测试套件（包括边界测试）

**测试报告：**
- 代码覆盖率报告（pytest-cov）
- 性能基准报告（pytest-benchmark）
- 失败测试的详细日志

### Epic 完成的测试标准

**Definition of Done (测试视角)：**
- ✅ 所有单元测试通过，覆盖率 ≥ 90%
- ✅ 所有集成测试通过
- ✅ 性能测试达到目标基准
- ✅ 安全测试无高危漏洞
- ✅ 所有 AC (AC1-AC12) 都有对应的自动化测试
- ✅ 代码审查通过（重点：错误处理、日志记录、模块独立性）

### 回归测试策略

**Epic 3 作为基础设施，后续 Epic（5, 6, 8）都依赖它：**
- 建立回归测试套件，每次修改 Epic 3 代码时运行
- 监控 Epic 5, 8 集成后的兼容性测试
- 版本化测试数据，确保向后兼容
