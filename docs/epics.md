# AEDT Project Epics

**Project:** AEDT (AI-Enhanced Delivery Toolkit)
**Author:** BMad + Claude (BMAD Methodology)
**Date:** 2025-11-23
**Version:** 1.0
**Total Epics:** 8
**Total Stories:** 53

---

## Epic Overview

This document contains all Epics for the AEDT project, decomposed from 58 functional requirements in the PRD. Each Epic delivers user value and is structured as a vertical slice containing all necessary layers (CLI, logic, infrastructure).

**Epic Execution Strategy:**
- **Phase 1 (Foundation):** Epic 1 → (parallel) Epic 2, Epic 3, Epic 4
- **Phase 2 (Core Engine):** Epic 5, Epic 6 → (parallel) Epic 7
- **Phase 3 (User Interface):** Epic 8

**FR Coverage:** All 58 functional requirements are mapped to Epics and Stories (see FR Coverage Matrix at end).

---

## Epic 1: Project Initialization and Foundation

```yaml
epic_id: 1
title: "Project Initialization and Foundation"
depends_on: []
priority: HIGH
execution_mode: single
story_concurrency: 1
estimated_stories: 5
```

### Description

As a developer using AEDT, I need to initialize the toolkit and establish the foundational infrastructure, so that I can start managing AI-enhanced development projects with persistent configuration and reliable logging.

**User Value:** Users can install AEDT, initialize configuration, and have a robust foundation for project management with automatic state persistence and crash recovery.

**Scope:**
- CLI framework and command structure
- Configuration management system
- File-based state persistence (YAML)
- Structured logging system
- Crash recovery mechanism

### Stories

#### Story 1.1: Project Initialization and CLI Framework

**As a** developer
**I want** to run `aedt init` to initialize AEDT configuration
**So that** I can start using AEDT with proper setup

**Acceptance Criteria:**

```gherkin
Given I am in a directory where I want to use AEDT
When I run `aedt init`
Then a `.aedt/` directory is created
And a `config.yaml` file is generated with default settings
And the CLI displays "AEDT initialized successfully"
And the config includes default settings for max_concurrent, quality_gates, git settings

Given AEDT is already initialized
When I run `aedt init` again
Then the CLI prompts "AEDT already initialized. Overwrite? [y/N]"
And if I choose 'N', the existing config is preserved
```

**Prerequisites:** None (Story 1.1 must be first)

**Technical Notes:**
- 使用 Click 框架创建 CLI 命令（`aedt init`）
- 创建以下目录结构时需验证每个目录创建是否成功：
  - `~/.aedt/` - 全局配置目录
  - `~/.aedt/logs/` - 全局日志目录
  - `{project-root}/.aedt/` - 项目配置目录
  - `{project-root}/.aedt/projects/` - 项目状态目录
  - `{project-root}/.aedt/worktrees/` - Worktree 根目录
  - `{project-root}/.aedt/logs/` - 项目日志目录
- **目录创建验证逻辑：**
  ```python
  def ensure_directory(path: str) -> bool:
      """确保目录存在，失败时返回 False 并记录错误"""
      try:
          os.makedirs(path, exist_ok=True)
          if not os.path.isdir(path):
              logger.error(f"Failed to create directory: {path}")
              return False
          logger.info(f"Directory ready: {path}")
          return True
      except PermissionError:
          logger.error(f"Permission denied: {path}")
          return False
      except Exception as e:
          logger.error(f"Error creating {path}: {e}")
          return False
  ```
- 初始化失败时提供清晰的错误提示：
  - 权限问题 → "请检查目录权限：{path}"
  - 磁盘空间 → "磁盘空间不足，请清理后重试"
  - 其他错误 → 显示具体异常信息
- Default config template includes: max_concurrent=5, quality_gates (pre_commit, epic_complete, pre_merge), git (branch_prefix="epic", auto_cleanup=true)
- Affected components: CLI framework, ConfigManager
- Config validation: ensure YAML is valid and contains required fields
- 覆盖 FR53（配置管理）、NFR16（可靠性）
- 架构决策：使用友好的错误提示，而非技术堆栈跟踪

---

#### Story 1.2: Configuration Management System

**As a** user
**I want** to customize AEDT behavior through a configuration file
**So that** I can adjust settings like max concurrency, quality gates, and Git preferences

**Acceptance Criteria:**

```gherkin
Given AEDT is initialized
When I edit `.aedt/config.yaml` and change max_concurrent to 3
And I run any AEDT command
Then the system reads the updated configuration
And applies the max_concurrent limit of 3

Given the config file has invalid YAML syntax
When I run any AEDT command
Then the CLI displays a friendly error: "Config file has invalid YAML syntax"
And suggests running `aedt init` to regenerate

Given a required field is missing from config
When I run any AEDT command
Then the CLI displays: "Missing required config field: <field_name>"
And provides the expected format
```

**Prerequisites:** Story 1.1 (initialization must exist first)

**Technical Notes:**
- Implement ConfigManager class with schema validation
- Support hot-reload: detect config changes and reload without restart
- Config schema: version, projects[], subagent{max_concurrent, timeout, model}, quality_gates{pre_commit[], epic_complete[], pre_merge[]}, git{worktree_base, branch_prefix, auto_cleanup}
- Use PyYAML or ruamel.yaml for parsing
- Affected components: ConfigManager, all modules that read config

---

#### Story 1.3: File-based State Persistence with Atomic Writes

**As a** user
**I want** AEDT to reliably save project and Epic states to disk
**So that** my progress is never lost, even if the system crashes

**Acceptance Criteria:**

```gherkin
Given an Epic is in "developing" status
When the state is updated (e.g., Story completed)
Then the state file `.aedt/projects/<project>/status.yaml` is atomically written
And the file contains the updated Epic status and progress
And if a crash occurs during write, the previous state remains intact

Given AEDT is restarted after a crash
When the system initializes
Then all project states are loaded from `.aedt/projects/*/status.yaml`
And Epic statuses reflect the last saved state
And Worktree paths are validated (cleaned up if invalid)
```

**Prerequisites:** Story 1.1 (directory structure must exist)

**Technical Notes:**
- Implement DataStore class with atomic write: write to temp file → rename to target (atomic on POSIX)
- State schema per project: project_id, epics{epic_id, status, progress, agent_id, worktree_path, completed_stories[], quality_checks{}, last_updated}
- State files: `.aedt/projects/<project-name>/status.yaml`
- On load: validate all Worktree paths exist, clean up stale references
- Affected components: StateManager, DataStore
- NFR compliance: NFR11 (data persistence reliability), NFR8 (crash recovery)

---

#### Story 1.4: Structured Logging System

**As a** developer troubleshooting issues
**I want** AEDT to generate structured logs with different severity levels
**So that** I can debug problems and trace operations

**Acceptance Criteria:**

```gherkin
Given AEDT is running
When any operation occurs (Epic start, Git operation, quality check, etc.)
Then a log entry is written to `.aedt/logs/aedt.log`
And the entry includes: timestamp, level (DEBUG/INFO/WARNING/ERROR), module, message

Given an Epic is started
When the Epic-level operations occur
Then a separate log file `.aedt/projects/<project>/epics/epic-<id>.log` is created
And contains all Epic-specific operations

Given the log level is set to INFO in config
When a DEBUG message is logged
Then it is not written to the file (filtered by level)
```

**Prerequisites:** Story 1.1 (log directory must exist)

**Technical Notes:**
- Use Python logging module with custom formatters
- Log levels: DEBUG (verbose), INFO (key operations), WARNING (potential issues), ERROR (failures)
- Log rotation: use RotatingFileHandler, max 10MB per file, keep 5 backups
- Format: `[2025-11-23 10:23:45] [INFO] [Scheduler] Epic 2 started with 5 stories`
- Epic-specific logs: `.aedt/projects/<project>/epics/epic-<id>.log`
- Affected components: Logger (new module), all components log operations
- NFR compliance: NFR20 (log completeness), NFR30 (log traceability)

---

#### Story 1.5: Crash Recovery and State Validation

**As a** user
**I want** AEDT to automatically recover from crashes
**So that** I can resume work without manual cleanup

**Acceptance Criteria:**

```gherkin
Given AEDT crashed while an Epic was developing
When I restart AEDT
Then the system loads all project states from disk
And marks crashed Epics as "paused" (not "running")
And displays: "Recovered from crash. 2 Epics were paused. Resume with `aedt resume epic-<id>`"

Given a Worktree path in state file no longer exists
When AEDT loads the state
Then the Worktree reference is marked as "invalid"
And the Epic status is set to "requires_cleanup"
And the user is prompted to run `aedt clean` or manually fix

Given the state file is corrupted (invalid YAML)
When AEDT starts
Then the CLI displays: "State file corrupted: <path>. Backup exists at <path>.backup"
And offers to restore from backup or reinitialize
```

**Prerequisites:** Story 1.3 (state persistence must exist)

**Technical Notes:**
- On startup: StateManager.load_all_states() validates all state files
- Validation checks: Worktree paths exist, Git branches exist, Agent IDs are valid (not running)
- Crashed Agent detection: check if Agent process still exists (via PID tracking or API query)
- State backup: create `.backup` file before each write, keep latest 3 backups
- Cleanup prompt: suggest `aedt clean` to remove invalid Worktrees
- Affected components: StateManager, WorktreeManager
- NFR compliance: NFR8 (crash recovery), NFR10 (Git operation fault tolerance)

---

### Epic 1 Complete Criteria

- All 5 Stories implemented and tested
- User can run `aedt init` and get a working configuration
- Config changes are applied without restart
- States are persisted reliably with atomic writes
- Logs are structured and traceable
- System recovers gracefully from crashes
- Unit tests cover ConfigManager, StateManager, DataStore, Logger
- Integration test: init → crash → restart → state recovered

---

## Epic 2: Multi-Project Management Center

```yaml
epic_id: 2
title: "Multi-Project Management Center"
depends_on: [1]
priority: HIGH
execution_mode: single
story_concurrency: 1
estimated_stories: 6
```

### Description

As a developer managing multiple MVP projects, I need a unified dashboard to view, add, remove, and switch between projects, so that I can efficiently manage all my AI-assisted development work from a single interface.

**User Value:** Users can manage 3-5 concurrent MVP projects, get intelligent recommendations on which project to work on next, and seamlessly switch contexts without losing progress.

**Scope:**
- Project CRUD operations (add, remove, list)
- Project metadata management
- Intelligent next-step recommendation
- Project switching with context preservation
- Non-interactive status summary

### Stories

#### Story 2.1: Add Project to AEDT

**As a** user
**I want** to add a project directory to AEDT
**So that** AEDT can manage its Epics and development workflow

**Acceptance Criteria:**

```gherkin
Given I have a project at `/path/to/my-project` with a `docs/epics/` directory
When I run `aedt project add /path/to/my-project`
Then the project is added to `.aedt/config.yaml` under projects[]
And a unique project_id is generated (hash of path)
And a project state directory is created: `.aedt/projects/<project-name>/`
And the CLI displays: "Project 'my-project' added successfully"

Given I add a project without specifying workflow type
When the project is added
Then the default workflow type is set to "bmad"

Given I add a project with a custom workflow
When I run `aedt project add /path/to/project --workflow=spec-kit`
Then the project is added with workflow_type="spec-kit"
```

**Prerequisites:** Epic 1 complete (config and state management must exist)

**Technical Notes:**
- Implement ProjectManager.add_project(path, workflow="bmad")
- Project model: {id (hash), name (dirname), path, workflow_type, config{}, created_at, updated_at}
- Validation: check if path exists, has `docs/epics/` directory (for bmad workflow)
- Project ID: use hashlib.sha256(path.encode()).hexdigest()[:8]
- Update config.yaml: append to projects[] array
- Affected components: ProjectManager, ConfigManager
- FR coverage: FR1

---

#### Story 2.2: List All Projects with Status

**As a** user
**I want** to see a list of all my projects with their current status
**So that** I can quickly understand the state of all my work

**Acceptance Criteria:**

```gherkin
Given I have added 3 projects to AEDT
When I run `aedt project list`
Then the CLI displays a table with columns: Name, Path, Workflow, Epics, Active, Completed
And each row shows: project name, truncated path, workflow type, total Epic count, active Epic count, completed Epic count

Given a project has 5 Epics (2 completed, 1 developing, 2 queued)
When I run `aedt project list`
Then the row shows: Epics=5, Active=1, Completed=2
```

**Prerequisites:** Story 2.1 (projects must exist)

**Technical Notes:**
- Implement ProjectManager.list_projects() → List[Project]
- For each project: read state file, count Epics by status
- CLI output: use Rich library for formatted tables
- Truncate paths: show `~/projects/...` instead of full path
- Affected components: ProjectManager, StateManager, CLI
- FR coverage: FR2

---

#### Story 2.3: Remove Project from AEDT

**As a** user
**I want** to remove a project from AEDT management
**So that** I can clean up completed or abandoned projects

**Acceptance Criteria:**

```gherkin
Given a project "my-project" is managed by AEDT
When I run `aedt project remove my-project`
Then the CLI prompts: "Remove 'my-project'? This will not delete files, only AEDT management. [y/N]"
And if I confirm 'y', the project is removed from config.yaml
And the project state directory `.aedt/projects/my-project/` is preserved (not deleted)
And the CLI displays: "Project removed. State preserved at .aedt/projects/my-project/"

Given I remove a project with active Epics
When I confirm removal
Then the CLI warns: "Warning: 2 Epics are still developing. Remove anyway? [y/N]"
```

**Prerequisites:** Story 2.1 (projects must exist)

**Technical Notes:**
- Implement ProjectManager.remove_project(project_id, preserve_state=True)
- Confirmation prompt: use Click.confirm()
- Warning if active Epics: check state file for status="developing"
- Remove from config.yaml, but keep `.aedt/projects/<name>/` intact
- Affected components: ProjectManager, ConfigManager
- FR coverage: FR3

---

#### Story 2.4: Intelligent Project Recommendation

**As a** user
**I want** AEDT to recommend which project I should work on next
**So that** I can maximize my productivity by working on the right thing

**Acceptance Criteria:**

```gherkin
Given I have 3 projects with different states:
  - Project A: 5 queued Epics, 0 developing
  - Project B: 2 queued Epics, 3 developing
  - Project C: 0 queued Epics, 5 completed
When I run `aedt recommend`
Then the CLI displays: "Recommended: Project A (5 Epics ready to start)"
And suggests: "Run `aedt project switch A` to activate"

Given all projects have developing Epics
When I run `aedt recommend`
Then the system recommends the project with the most queued Epics
And displays: "Recommended: Project X (Y queued Epics waiting)"
```

**Prerequisites:** Story 2.2 (must read project states)

**Technical Notes:**
- Implement ProjectManager.recommend_next_project() → Optional[Project]
- Recommendation algorithm (MVP version):
  1. Prefer projects with queued Epics and no developing Epics (ready to start)
  2. Else prefer projects with most queued Epics (highest backlog)
  3. Else prefer projects with oldest updated_at (least recently worked)
- Phase 2 can use ML-based recommendation
- Affected components: ProjectManager, StateManager
- FR coverage: FR4

---

#### Story 2.5: Configure Project Workflow Type

**As a** user
**I want** to specify which workflow framework a project uses
**So that** AEDT can correctly parse Epics and Stories

**Acceptance Criteria:**

```gherkin
Given I add a project with default settings
When the project is added
Then the workflow_type is set to "bmad" by default

Given I want to use a different workflow
When I run `aedt project add /path --workflow=spec-kit`
Then the project is added with workflow_type="spec-kit"
And a warning displays: "Note: spec-kit workflow support is experimental (Phase 2)"

Given I want to change a project's workflow type
When I edit `.aedt/config.yaml` and change workflow_type to "custom"
And I run any AEDT command
Then the updated workflow type is applied
```

**Prerequisites:** Story 2.1 (project addition must support workflow parameter)

**Technical Notes:**
- Supported workflow types (MVP): "bmad" (default)
- Planned workflow types (Phase 2): "spec-kit", "custom"
- Workflow validation: check if workflow adapter exists
- If workflow != "bmad", display warning: "Only 'bmad' is supported in MVP. Other workflows coming in Phase 2."
- Affected components: ProjectManager, ConfigManager
- FR coverage: FR5
- Architecture: Workflow adapters are pluggable (interface defined, only BMAD implemented in MVP)

---

#### Story 2.6: Non-interactive Global Status Summary

**As a** user
**I want** to run `aedt status` to get a quick overview of all projects
**So that** I can see the big picture without launching the TUI

**Acceptance Criteria:**

```gherkin
Given I have 3 projects with various Epic states
When I run `aedt status`
Then the CLI displays:
  - Total projects: 3
  - Total Epics: 15 (5 completed, 3 developing, 7 queued)
  - Active Agents: 3
  - Recommended next step: "Start Project A Epic 2"

Given no projects are added
When I run `aedt status`
Then the CLI displays: "No projects managed by AEDT. Add a project with `aedt project add <path>`"
```

**Prerequisites:** Story 2.2 (must read all project states)

**Technical Notes:**
- Implement CLI command `aedt status` (non-interactive, suitable for scripts)
- Aggregate data across all projects: count Epics by status, count active Agents
- Include recommendation from Story 2.4
- Output format: plain text, suitable for parsing or piping
- Affected components: CLI, ProjectManager, StateManager
- FR coverage: FR58

---

### Epic 2 Complete Criteria

- All 6 Stories implemented and tested
- User can add, remove, and list projects
- Intelligent recommendation works correctly
- Workflow types are configurable
- Non-interactive status provides useful overview
- Unit tests cover ProjectManager methods
- Integration test: add 3 projects → list → remove → status

---

## Epic 3: Epic Parsing and Dependency Analysis

```yaml
epic_id: 3
title: "Epic Parsing and Dependency Analysis"
depends_on: [1]
priority: HIGH
execution_mode: multi
story_concurrency: 3
estimated_stories: 8
```

### Description

As a user following the BMAD workflow, I need AEDT to automatically read Epic documents, extract metadata, parse dependencies, and identify which Epics can be developed in parallel, so that the system can intelligently schedule work.

**User Value:** Users no longer manually track Epic dependencies. AEDT automatically builds a dependency graph (DAG), identifies parallelizable Epics, and monitors changes to Epic files.

**Scope:**
- BMAD Epic document parsing (YAML frontmatter + Markdown)
- Story extraction from Epic documents
- Dependency relationship extraction
- DAG (Directed Acyclic Graph) construction
- Parallel Epic identification
- File watching for automatic updates

### Stories

#### Story 3.1: Parse BMAD Epic Documents and Extract Metadata

**As a** user
**I want** AEDT to read Epic files from `docs/epics/*.md`
**So that** the system knows what Epics exist and their properties

**Acceptance Criteria:**

```gherkin
Given a project has Epic files in `docs/epics/epic-001-foundation.md`
And the file has YAML frontmatter with: epic_id, title, depends_on, priority
When AEDT parses the project
Then an Epic object is created with: id="1", title="Foundation", depends_on=[], priority="HIGH"

Given an Epic file has invalid YAML frontmatter
When AEDT parses the file
Then a warning is logged: "Epic file <path> has invalid frontmatter. Skipping."
And the Epic is not added to the project

Given an Epic file is missing required fields (epic_id or title)
When AEDT parses the file
Then a warning is logged: "Epic file <path> missing required field: <field>"
And the Epic is not added
```

**Prerequisites:** Epic 1 complete (config and logging must exist)

**Technical Notes:**
- Implement EpicParser.parse_epics(project_path) → List[Epic]
- Use frontmatter library to extract YAML metadata from Markdown
- Required fields: epic_id (int), title (str)
- Optional fields: depends_on (List[int]), priority (str, default="MEDIUM"), execution_mode (str, default="auto"), story_concurrency (int, default=2)
- Epic model: {id, title, description (from Markdown body), depends_on, priority, stories[], status, progress, agent_id, worktree_path, created_at, updated_at}
- Affected components: EpicParser (new module)
- FR coverage: FR6

---

#### Story 3.2: Extract Story List from Epic Documents

**As a** user
**I want** AEDT to parse the Story list within each Epic document
**So that** Subagents know what tasks to complete

**Acceptance Criteria:**

```gherkin
Given an Epic document contains a "Stories" section with numbered items:
  1. Story 1.1: Initialize CLI
  2. Story 1.2: Config Management
When AEDT parses the Epic
Then the Epic.stories array contains 2 Story objects
And Story 1 has: id="1.1", title="Initialize CLI", status="pending"

Given a Story has a "Prerequisites" subsection listing dependencies
When AEDT parses the Story
Then the Story.prerequisites field is populated
And can be used for Story-level DAG construction (multi mode)

Given an Epic has no Stories section
When AEDT parses the Epic
Then the Epic.stories array is empty
And a warning is logged: "Epic <id> has no Stories defined"
```

**Prerequisites:** Story 3.1 (Epic parsing must exist)

**Technical Notes:**
- Implement EpicParser.parse_stories(epic_content) → List[Story]
- Parse Markdown: look for sections like "### Story 1.1" or numbered lists under "## Stories"
- Story model: {id, title, description, status ("pending"), commit_hash, prerequisites (List[str])}
- Extract prerequisites from subsections or YAML blocks within Story
- Use Markdown parser (e.g., markdown-it-py or mistune)
- Affected components: EpicParser
- FR coverage: FR13

---

#### Story 3.3: Build Epic Dependency DAG

**As a** user
**I want** AEDT to construct a dependency graph from Epic metadata
**So that** the system can determine execution order

**Acceptance Criteria:**

```gherkin
Given 4 Epics with dependencies:
  - Epic 1: depends_on=[]
  - Epic 2: depends_on=[1]
  - Epic 3: depends_on=[1]
  - Epic 4: depends_on=[2, 3]
When AEDT builds the DAG
Then the DAG structure shows:
  - Epic 1 has no incoming edges
  - Epic 2 and 3 depend on Epic 1
  - Epic 4 depends on Epic 2 and Epic 3

Given Epic 2 depends on Epic 3, and Epic 3 depends on Epic 2 (circular)
When AEDT builds the DAG
Then a validation error is raised: "Circular dependency detected: Epic 2 ↔ Epic 3"
And the system refuses to proceed
```

**Prerequisites:** Story 3.1 (Epic metadata must be parsed)

**Technical Notes:**
- Implement DependencyAnalyzer.build_epic_dag(epics) → DAG
- DAG structure: {nodes: Dict[int, Epic], edges: Dict[int, List[int]]} (adjacency list)
- Validate DAG: detect cycles using DFS (depth-first search)
- DAG.has_cycle() returns True if circular dependency found
- Affected components: DependencyAnalyzer (new module), Scheduler
- FR coverage: FR7
- Architecture: DAG is the foundation for scheduling decisions

---

#### Story 3.4: Build Story Dependency DAG (Multi 模式支持)

**User Story:**
As a developer,
I want the system to analyze Story-level dependencies (prerequisites),
So that Story-level Subagents can be scheduled in the correct order during multi-mode execution.

**Acceptance Criteria:**

**Given** an Epic with multiple Stories and prerequisites defined
**When** the system parses the Epic in multi-mode
**Then** it should:
- Extract `prerequisites` field from each Story
- Build a Story-level DAG (Directed Acyclic Graph)
- Detect circular dependencies at Story level
- Return a list of Stories that can run in parallel
- Return a list of Stories that must wait for prerequisites

**And** the system should validate Story prerequisites:
- All prerequisite Story IDs exist within the same Epic
- No forward dependencies (only backward or parallel)
- No circular dependencies detected

**Prerequisites:**
- Story 3.1 (Read Epic Documents)
- Story 3.2 (Parse Epic Metadata)

**Technical Notes:**
- 实现 `DependencyAnalyzer.build_story_dag(stories: List[Story]) -> DAG` 方法
- DAG 数据结构：
  ```python
  class DAG:
      nodes: Dict[str, Story]        # Story ID → Story
      edges: Dict[str, List[str]]    # Story ID → 依赖的 Story ID 列表

      def get_parallel_stories(self, completed: List[str]) -> List[Story]:
          """获取可并行的 Story（无依赖或依赖已完成）"""
          pass

      def topological_sort(self) -> List[Story]:
          """拓扑排序"""
          pass
  ```
- Story prerequisites 解析：从 Story Markdown 的 `Prerequisites:` 字段提取
- 循环依赖检测：使用 DFS（深度优先搜索）
- 覆盖 FR12（依赖分析）、FR25（Story 并发支持）、NFR16（可靠性）
- 架构决策：支持 multi 模式下的 Story-level 并发调度

---

#### Story 3.5: Identify Parallelizable Epics

**As a** user
**I want** AEDT to automatically identify which Epics can run in parallel
**So that** I can start multiple Epics at once

**Acceptance Criteria:**

```gherkin
Given a DAG with Epic 1, 2, 3 where:
  - Epic 1: no dependencies
  - Epic 2: depends on Epic 1
  - Epic 3: no dependencies
And Epic 1 is completed
When I query for parallel Epics
Then the system returns [Epic 2, Epic 3] (both can start)

Given no Epics have completed yet
When I query for parallel Epics
Then the system returns only Epics with no dependencies [Epic 1, Epic 3]
```

**Prerequisites:** Story 3.3 (DAG must exist)

**Technical Notes:**
- Implement DependencyAnalyzer.get_parallel_epics(dag, completed_epic_ids) → List[Epic]
- Algorithm: for each Epic, check if all depends_on Epics are in completed_epic_ids
- Return Epics where all dependencies are satisfied and status != "completed"
- Affected components: DependencyAnalyzer, Scheduler
- FR coverage: FR8

---

#### Story 3.6: Identify Queued Epics Waiting for Dependencies

**As a** user
**I want** to see which Epics are waiting for dependencies to complete
**So that** I understand the execution pipeline

**Acceptance Criteria:**

```gherkin
Given Epic 4 depends on Epic 2 and Epic 3
And Epic 2 is completed, but Epic 3 is still developing
When I query for queued Epics
Then Epic 4 is returned with status "queued" and reason "Waiting for: Epic 3"

Given Epic 2 and Epic 3 both complete
When I query for queued Epics
Then Epic 4 is no longer queued (it's now parallelizable)
```

**Prerequisites:** Story 3.5 (parallel Epic logic must exist)

**Technical Notes:**
- Implement DependencyAnalyzer.get_queued_epics(dag, completed_epic_ids) → List[Tuple[Epic, List[int]]]
- Return: Epic + list of missing dependency IDs
- Algorithm: for each Epic, check if any depends_on Epics are NOT in completed_epic_ids
- Affected components: DependencyAnalyzer, Scheduler
- FR coverage: FR9

---

#### Story 3.7: View Epic Dependencies in TUI

**As a** user
**I want** to see which Epics an Epic depends on and their status
**So that** I understand why an Epic is queued

**Acceptance Criteria:**

```gherkin
Given Epic 4 depends on Epic 2 (completed) and Epic 3 (developing)
When I view Epic 4 details in the TUI
Then the dependencies section shows:
  - Epic 2: Foundation (✓ Completed)
  - Epic 3: Parser (⚙ Developing)

Given an Epic has no dependencies
When I view its details
Then the dependencies section shows: "None"
```

**Prerequisites:** Story 3.6 (dependency queries must exist), Epic 8 (TUI must exist)

**Technical Notes:**
- Extend Epic details view in TUI to show depends_on with status
- Query StateManager for status of each dependency Epic
- Display status icons: ✓ (completed), ⚙ (developing), ⏳ (queued), ✗ (failed)
- Affected components: TUIApp (EpicPanel)
- FR coverage: FR10

---

#### Story 3.8: Monitor Epic File Changes and Auto-refresh

**As a** user
**I want** AEDT to automatically detect when I modify Epic files
**So that** changes are reflected without restarting

**Acceptance Criteria:**

```gherkin
Given AEDT is running and monitoring `docs/epics/`
When I edit `epic-002-parser.md` and add a new Story
And I save the file
Then within 5 seconds, AEDT re-parses the Epic
And the new Story appears in the Epic details
And a log message is written: "Epic 2 updated: re-parsed"

Given I add a new Epic file `epic-009-new.md`
When I save the file
Then AEDT detects the new Epic
And parses it automatically
And adds it to the project's Epic list
```

**Prerequisites:** Story 3.1, 3.2 (Epic parsing must exist)

**Technical Notes:**
- Implement FileWatcher using watchdog library
- Watch directory: `<project-path>/docs/epics/`
- On file change event: trigger EpicParser.parse_epics() for changed file
- Debounce: wait 1 second after last change before re-parsing (avoid multiple triggers)
- Update StateManager with refreshed Epic data
- Notify TUI to refresh display
- Affected components: FileWatcher (new module), EpicParser, StateManager
- FR coverage: FR12
- NFR compliance: NFR5 (file monitoring performance)

---

### Epic 3 Complete Criteria

- All 8 Stories implemented and tested
- AEDT parses BMAD Epic documents with YAML frontmatter
- Stories are extracted from Epic content
- DAG is built correctly and circular dependencies are detected
- Story-level DAG supports multi-mode execution
- Parallel and queued Epics are identified accurately
- File watching triggers automatic re-parsing
- Unit tests cover EpicParser, DependencyAnalyzer, FileWatcher
- Integration test: create Epic files → parse → modify → auto-refresh

---

## Epic 4: Git Worktree Automation and Management

```yaml
epic_id: 4
title: "Git Worktree Automation and Management"
depends_on: [1]
priority: HIGH
execution_mode: multi
story_concurrency: 3
estimated_stories: 8
```

### Description

As a user running multiple parallel Epics, I need AEDT to automatically manage Git Worktrees, create isolated branches, detect conflicts, and handle merges, so that I never have to manually manage Git operations.

**User Value:** Users achieve 100% Git automation. AEDT handles branch creation, Worktree lifecycle, automatic merging (when safe), conflict detection, and cleanup.

**Scope:**
- Git Worktree creation and isolation
- Branch naming and management
- Automatic merging (no conflicts)
- Conflict detection and resolution workflow
- Worktree cleanup
- Story-level commits

### Stories

#### Story 4.1: Create Git Worktree for Epic

**As a** user
**I want** AEDT to create an isolated Git Worktree for each Epic
**So that** multiple Epics can be developed in parallel without conflicts

**Acceptance Criteria:**

```gherkin
Given Epic 2 is ready to start
When AEDT starts Epic 2
Then a Git branch "epic-2" is created from the main branch
And a Worktree is created at `.aedt/worktrees/epic-2/`
And the Worktree path is saved in Epic 2's state

Given a branch "epic-2" already exists
When AEDT tries to create the Worktree
Then the CLI displays an error: "Branch 'epic-2' already exists. Clean up with `aedt clean` or delete manually."
And the Epic start is aborted
```

**Prerequisites:** Epic 1 complete (state management must exist)

**Technical Notes:**
- Implement WorktreeManager.create_worktree(epic_id, branch_prefix="epic") → Worktree
- Use GitPython: `repo.git.worktree('add', path, '-b', branch_name)`
- Branch naming: `{branch_prefix}-{epic_id}` (e.g., "epic-2")
- Worktree path: `.aedt/worktrees/epic-{epic_id}/`
- Validate: check if branch exists before creating
- Store Worktree info in state: {epic_id, branch_name, path, created_at}
- Affected components: WorktreeManager (new module), Scheduler
- FR coverage: FR18, FR26

---

#### Story 4.2: Subagent Development in Isolated Worktree

**As a** Subagent
**I want** to work in an isolated Git Worktree
**So that** my changes don't interfere with other parallel Epics

**Acceptance Criteria:**

```gherkin
Given Epic 2 has a Worktree at `.aedt/worktrees/epic-2/`
When a Subagent starts working on Epic 2
Then the Subagent's working directory is set to the Worktree path
And all file operations occur within the Worktree
And commits are made to the "epic-2" branch

Given Epic 3 is developing in parallel in `.aedt/worktrees/epic-3/`
When both Subagents modify `src/parser.py`
Then the changes are isolated in their respective Worktrees
And no conflicts occur during development
```

**Prerequisites:** Story 4.1 (Worktree must exist), Epic 6 (Subagent orchestration)

**Technical Notes:**
- Pass worktree_path to SubagentOrchestrator.start_epic_agent()
- Subagent receives prompt: "Working directory: <worktree_path>"
- All git operations (commit, status) happen in the Worktree
- Affected components: SubagentOrchestrator, WorktreeManager
- FR coverage: FR28

---

#### Story 4.3: Auto-commit After Each Story Completion

**As a** user
**I want** each Story to be committed separately
**So that** the Git history is granular and conflicts are minimized

**Acceptance Criteria:**

```gherkin
Given Epic 2 has 3 Stories
When the Subagent completes Story 2.1
Then a Git commit is made with message: "Story 2.1: Initialize CLI"
And the commit is on the "epic-2" branch

Given the Subagent completes all 3 Stories
When the Epic is done
Then there are 3 commits on the "epic-2" branch
And each commit corresponds to a Story
```

**Prerequisites:** Story 4.2 (Subagent must work in Worktree), Epic 6 (Subagent must report Story completion)

**Technical Notes:**
- Subagent prompt includes: "After completing each Story, run `git add .` and `git commit -m 'Story X: <title>'`"
- SubagentOrchestrator monitors output for "Story X completed"
- On Story completion event: verify commit exists (check `git log`)
- If commit not found, log warning: "Story X completed but no commit detected"
- Affected components: SubagentOrchestrator, WorktreeManager
- FR coverage: FR29

---

#### Story 4.4: Detect File Conflicts Across Parallel Epics

**As a** user
**I want** AEDT to detect when multiple Epics modify the same files
**So that** I can resolve conflicts before merging

**Acceptance Criteria:**

```gherkin
Given Epic 2 modifies `src/parser.py` and `src/config.py`
And Epic 3 modifies `src/parser.py` and `src/utils.py`
When AEDT checks for conflicts
Then the system reports: "Conflict detected: Epic 2 and Epic 3 both modify src/parser.py"

Given Epic 2 and Epic 3 modify completely different files
When AEDT checks for conflicts
Then no conflicts are reported
```

**Prerequisites:** Story 4.1 (Worktrees must exist)

**Technical Notes:**
- Implement WorktreeManager.detect_conflicts(epic_ids) → Dict[str, List[int]]
- Algorithm: for each Epic, run `git diff --name-only main..epic-{id}` to get modified files
- Compare file lists across Epics, identify overlaps
- Return: {filename: [epic_id1, epic_id2]} for conflicting files
- Run conflict detection: before merging, or on-demand via TUI
- Affected components: WorktreeManager, Scheduler
- FR coverage: FR31

---

#### Story 4.5: Automatic Merge to Main Branch (No Conflicts)

**As a** user
**I want** AEDT to automatically merge completed Epics to main
**So that** I don't have to manually handle merges

**Acceptance Criteria:**

```gherkin
Given Epic 2 is completed and all quality checks pass
And no other Epic is modifying the same files
When AEDT runs the merge process
Then the "epic-2" branch is merged into "main"
And the merge commit message is: "Merge Epic 2: <title>"
And the Epic status is updated to "merged"

Given Epic 2 has file conflicts with another developing Epic
When AEDT attempts to merge
Then the merge is aborted
And the Epic status is set to "awaiting_merge"
And the user is notified: "Epic 2 has conflicts. Resolve manually."
```

**Prerequisites:** Story 4.4 (conflict detection must exist), Epic 7 (quality checks must pass)

**Technical Notes:**
- Implement WorktreeManager.merge_to_main(epic_id, main_branch="main") → bool
- Steps: 1) Detect conflicts, 2) Run quality checks, 3) If both pass, merge
- Use GitPython: `repo.git.checkout('main')`, `repo.git.merge(f'epic-{epic_id}')`
- If merge conflicts: `repo.git.merge('--abort')`, return False
- On success: update Epic status to "merged", trigger cleanup
- Affected components: WorktreeManager, Scheduler, QualityGate
- FR coverage: FR30

---

#### Story 4.6: Pause Merge on Conflict Detection

**As a** user
**I want** AEDT to stop the merge process when conflicts are detected
**So that** I can manually resolve them

**Acceptance Criteria:**

```gherkin
Given Epic 2 is ready to merge but has conflicts
When AEDT detects the conflict
Then the merge is not attempted
And the Epic status is set to "awaiting_merge"
And a TUI notification appears: "Epic 2 has conflicts with Epic 3 (src/parser.py). Resolve manually."

Given I resolve the conflicts manually
When I mark the Epic as "ready_to_merge"
And I run `aedt merge epic-2`
Then the merge proceeds
```

**Prerequisites:** Story 4.4 (conflict detection), Story 4.5 (merge logic)

**Technical Notes:**
- Before merge: call WorktreeManager.detect_conflicts([epic_id])
- If conflicts detected: set Epic.status = "awaiting_merge", skip merge
- Store conflict details in state: {conflicting_epics, files}
- TUI displays conflict details in Epic panel
- Manual resolution: user edits files, commits, then runs `aedt merge <epic-id>`
- Affected components: WorktreeManager, Scheduler, TUIApp
- FR coverage: FR32

---

#### Story 4.7: Manual Conflict Resolution Workflow

**As a** user
**I want** to manually resolve conflicts and resume the merge
**So that** I have full control over complex merges

**Acceptance Criteria:**

```gherkin
Given Epic 2 has a conflict with Epic 3
When I run `aedt conflicts epic-2`
Then the CLI displays:
  - Conflicting files: src/parser.py
  - Conflicting Epics: Epic 3 (developing)
  - Suggested action: "Pause Epic 3, merge Epic 2, then resume Epic 3"

Given I manually resolve the conflict
When I run `aedt merge epic-2 --force`
Then the merge proceeds despite conflicts
And I am prompted to handle merge conflicts manually
```

**Prerequisites:** Story 4.6 (conflict detection and pause)

**Technical Notes:**
- Implement CLI command `aedt conflicts <epic-id>` to show conflict details
- Implement `aedt merge <epic-id> --force` to attempt merge despite conflicts
- If merge conflicts occur: Git enters conflict state, user resolves manually
- After resolution: user runs `git commit` to finalize merge
- AEDT detects merge completion: checks if `git status` is clean
- Affected components: CLI, WorktreeManager
- FR coverage: FR33, FR34

---

#### Story 4.8: Cleanup Worktree After Merge

**As a** user
**I want** AEDT to automatically clean up Worktrees after successful merge
**So that** disk space is freed and the workspace stays clean

**Acceptance Criteria:**

```gherkin
Given Epic 2 is successfully merged to main
When the merge completes
Then the Worktree at `.aedt/worktrees/epic-2/` is removed
And the "epic-2" branch is deleted
And the Epic state is updated: worktree_path=null, status="completed"

Given I want to manually clean up all Worktrees
When I run `aedt clean`
Then all Worktrees in `.aedt/worktrees/` are removed
And all Epic branches are deleted
And the CLI prompts for confirmation: "Remove all Worktrees? [y/N]"
```

**Prerequisites:** Story 4.5 (merge must succeed)

**Technical Notes:**
- Implement WorktreeManager.cleanup_worktree(epic_id)
- Use GitPython: `repo.git.worktree('remove', path)`, `repo.git.branch('-D', branch_name)`
- Auto-cleanup: triggered after successful merge (if config.git.auto_cleanup=true)
- Manual cleanup: `aedt clean` removes all Worktrees, requires confirmation
- Update state: set Epic.worktree_path = null, Epic.status = "completed"
- Affected components: WorktreeManager, Scheduler, CLI
- FR coverage: FR27, FR35

---

### Epic 4 Complete Criteria

- All 8 Stories implemented and tested
- Git Worktrees are created automatically for each Epic
- Subagents work in isolated environments
- Story-level commits are enforced
- Conflict detection prevents bad merges
- Automatic merging works when safe
- Manual conflict resolution workflow is clear
- Worktrees are cleaned up after merge
- Unit tests cover WorktreeManager methods
- Integration test: start 2 Epics → modify same file → detect conflict → resolve → merge → cleanup

---

## Epic 5: Intelligent Parallel Scheduling Engine

```yaml
epic_id: 5
title: "Intelligent Parallel Scheduling Engine"
depends_on: [3, 4]
priority: HIGH
execution_mode: multi
story_concurrency: 3
estimated_stories: 7
```

### Description

As a user wanting to maximize development speed, I need AEDT to intelligently schedule Epics for parallel execution, manage concurrency limits, and automatically queue dependent Epics, so that I can run 3-5 Epics simultaneously without manual coordination.

**User Value:** Users can start multiple Epics with one command, and the system handles all scheduling, queuing, and automatic启动 of dependent Epics.

**Scope:**
- Epic启动 with dependency validation
- Concurrency control (max 5 Subagents)
- Automatic queuing of dependent Epics
- Execution mode determination (single vs multi)
- Epic completion handling
- Auto-start queued Epics

### Stories

#### Story 5.1: Start Multiple Epics with Dependency Validation

**As a** user
**I want** to select multiple Epics and start them in parallel
**So that** I can maximize development speed

**Acceptance Criteria:**

```gherkin
Given I have 5 Epics (1, 2, 3 with no dependencies; 4 depends on 1, 2)
When I run `aedt start epic-1 epic-2 epic-3`
Then AEDT validates dependencies for all 3 Epics
And all 3 are started in parallel (no dependencies)
And Worktrees are created for each
And Subagents are launched for each

Given I try to start Epic 4 before Epic 1 is complete
When I run `aedt start epic-4`
Then the CLI displays: "Cannot start Epic 4. Missing dependencies: Epic 1, Epic 2"
And Epic 4 is not started
```

**Prerequisites:** Epic 3 (dependency analysis), Epic 4 (Worktree creation)

**Technical Notes:**
- Implement Scheduler.start_epics(epic_ids) → Dict[str, str] (result per Epic)
- For each Epic: check DependencyAnalyzer.get_parallel_epics() to see if dependencies are met
- If dependencies not met: add to queue, return "queued"
- If dependencies met: create Worktree, start Subagent, return "started"
- Affected components: Scheduler, DependencyAnalyzer, WorktreeManager
- FR coverage: FR16, FR17

---

#### Story 5.2: Control Maximum Concurrent Subagents

**As a** user
**I want** AEDT to limit the number of concurrent Subagents
**So that** I don't overwhelm my system or API rate limits

**Acceptance Criteria:**

```gherkin
Given max_concurrent is set to 3 in config
And I try to start 5 Epics
When all 5 Epics are valid (no dependency issues)
Then only 3 Epics start immediately
And the remaining 2 are added to the queue
And the CLI displays: "Started 3 Epics. 2 Epics queued (concurrency limit)."

Given one of the 3 running Epics completes
When the completion is detected
Then the next queued Epic starts automatically
And the CLI displays: "Epic X completed. Starting Epic Y from queue."
```

**Prerequisites:** Story 5.1 (Epic starting logic)

**Technical Notes:**
- Implement ScheduleQueue with max_concurrent limit (from config)
- Track running Epics: List[str] (Epic IDs)
- On start: if len(running) < max_concurrent, start Epic; else queue
- On Epic complete: call Scheduler.auto_start_queued()
- Affected components: Scheduler, ScheduleQueue
- FR coverage: FR20, FR21

---

#### Story 5.3: Automatically Determine Execution Mode (Single vs Multi)

**As a** user
**I want** AEDT to choose the optimal execution mode for each Epic
**So that** small Epics use a single Agent and large Epics use multiple Agents

**Acceptance Criteria:**

```gherkin
Given Epic 1 has 3 Stories and execution_mode="auto"
When AEDT starts Epic 1
Then the system chooses "single" mode (1 Epic-level Subagent)
And the Subagent completes all 3 Stories sequentially

Given Epic 3 has 8 Stories and execution_mode="auto"
When AEDT starts Epic 3
Then the system chooses "multi" mode
And multiple Story-level Subagents are used (up to story_concurrency limit)

Given Epic 2 has execution_mode="single" (manually set)
When AEDT starts Epic 2
Then "single" mode is used regardless of Story count
```

**Prerequisites:** Story 5.1 (Epic starting logic), Epic 3 (Story parsing)

**Technical Notes:**
- Implement Scheduler.determine_execution_mode(epic) → str
- Logic: if epic.execution_mode != "auto", return it; else if len(epic.stories) <= 5, return "single"; else return "multi"
- Store chosen mode in Epic state
- Affected components: Scheduler
- FR coverage: Architecture requirement (hybrid execution mode)
- Architecture: Key decision point for Epic vs Story concurrency

---

#### Story 5.4: Start Epic in Single Mode (Epic-level Subagent)

**As a** user
**I want** small Epics to be completed by a single Subagent
**So that** context is preserved and overhead is minimized

**Acceptance Criteria:**

```gherkin
Given Epic 1 has 5 Stories and is in "single" mode
When AEDT starts Epic 1
Then 1 Subagent is launched for the entire Epic
And the Subagent receives all 5 Stories in the prompt
And the Subagent completes Stories sequentially: Story 1 → commit → Story 2 → commit → ... → Story 5 → commit

Given the Subagent completes Story 3 of 5
When AEDT monitors progress
Then Epic progress is updated to 60% (3/5)
And the TUI displays: "Epic 1: Developing 60% (Story 3/5)"
```

**Prerequisites:** Story 5.3 (mode determination), Epic 6 (Subagent orchestration)

**Technical Notes:**
- Implement Scheduler.start_epic_single_mode(epic)
- Call SubagentOrchestrator.start_epic_agent(epic, worktree_path)
- Prompt includes all Stories: "Complete the following Stories in order: 1. Story 1.1 ... 2. Story 1.2 ..."
- Monitor Subagent output for "Story X completed" to update progress
- Affected components: Scheduler, SubagentOrchestrator
- FR coverage: Architecture requirement (Epic-level Subagent)

---

#### Story 5.5: Start Epic in Multi Mode (Story-level Subagents)

**As a** user
**I want** large Epics to have Stories completed in parallel
**So that** development is faster and context is focused

**Acceptance Criteria:**

```gherkin
Given Epic 3 has 8 Stories and is in "multi" mode
And story_concurrency is set to 3
When AEDT starts Epic 3
Then the first 3 Stories (no dependencies) are started in parallel
And each Story has its own Subagent
And remaining Stories are queued

Given Story 1 completes
When the completion is detected
Then Story 4 (next in queue) starts automatically
And a new Subagent is launched for Story 4
```

**Prerequisites:** Story 5.3 (mode determination), Story 3.2 (Story parsing with prerequisites)

**Technical Notes:**
- 实现 `Scheduler.start_epic_multi_mode(epic: Epic)` 方法
- **Story 并发控制逻辑：**
  ```python
  async def start_epic_multi_mode(self, epic: Epic):
      """Multi 模式：每个 Story 启动独立 Subagent"""
      # 1. 构建 Story DAG
      story_dag = self.dependency_analyzer.build_story_dag(epic.stories)

      # 2. 验证 DAG（检测循环依赖）
      if story_dag.has_cycle():
          raise DependencyError(f"Epic {epic.id} has circular Story dependencies")

      # 3. 初始化 Story 并发队列
      story_concurrency = epic.story_concurrency  # 默认 2
      running_stories = []
      completed_stories = []

      # 4. 启动可并行的 Story（最多 story_concurrency 个）
      parallel_stories = story_dag.get_parallel_stories(completed=[])
      for story in parallel_stories[:story_concurrency]:
          agent = await self.orchestrator.start_story_agent(
              story, epic, epic.worktree_path
          )
          running_stories.append((story.id, agent.id))

      # 5. 监听 Story 完成，自动启动下一个
      while running_stories or story_dag.has_queued_stories(completed_stories):
          # 等待任意 Story 完成
          completed_story_id = await self.wait_for_story_completion(running_stories)
          completed_stories.append(completed_story_id)
          running_stories.remove((completed_story_id, agent_id))

          # 更新 Epic 进度
          self.update_epic_progress(epic.id, len(completed_stories), len(epic.stories))

          # 启动下一个可并行的 Story
          if len(running_stories) < story_concurrency:
              next_stories = story_dag.get_parallel_stories(completed_stories)
              for story in next_stories:
                  if len(running_stories) >= story_concurrency:
                      break
                  agent = await self.orchestrator.start_story_agent(
                      story, epic, epic.worktree_path
                  )
                  running_stories.append((story.id, agent.id))

      # 6. 所有 Story 完成，触发 Epic 完成
      self.on_epic_completed(epic.id)
  ```
- **并发限制：**
  - `epic.story_concurrency`：Epic 内 Story 最大并发数（默认 2）
  - 全局 `max_concurrent`：所有 Epic + Story 总并发数（默认 5）
  - 示例：Epic 1 (single, 1 agent) + Epic 2 (multi, 2 stories) = 3 agents（< 5）
- **Story 完成检测：**
  - 监听 Subagent 输出："Story X completed"
  - 更新 Story 状态为 "completed"
  - 更新 Story 的 `commit_hash`
- Affected components: Scheduler, SubagentOrchestrator, DependencyAnalyzer
- 覆盖 FR20（Epic 启动）、FR21（Epic 暂停/恢复）、FR25（Story 并发）、NFR1（性能）
- 架构决策：异步处理（asyncio），不阻塞 UI

---

#### Story 5.6: Handle Epic Completion and Trigger Quality Checks

**As a** user
**I want** AEDT to automatically run quality checks when an Epic completes
**So that** only high-quality code is merged

**Acceptance Criteria:**

```gherkin
Given Epic 1 completes all Stories
When the last Story is marked complete
Then Epic status is set to "quality_checking"
And quality gates for stage "epic_complete" are triggered
And if all checks pass, Epic status becomes "merging"
And if any check fails, Epic status becomes "failed" with failure details

Given quality checks pass
When the Epic proceeds to merge
Then WorktreeManager.merge_to_main() is called
And if merge succeeds, Epic status becomes "completed"
```

**Prerequisites:** Story 5.4 or 5.5 (Epic must complete), Epic 7 (quality gates)

**Technical Notes:**
- Implement Scheduler.on_epic_completed(epic_id)
- Steps: 1) Set status="quality_checking", 2) Run QualityGate.run_checks("epic_complete", worktree_path), 3) If pass → merge, 4) If fail → set status="failed"
- On merge success: call Scheduler.auto_start_queued() to start next Epic
- Affected components: Scheduler, QualityGate, WorktreeManager
- FR coverage: Epic completion flow (FR37 quality check, FR30 merge)

---

#### Story 5.7: Auto-start Queued Epics When Dependencies Complete

**As a** user
**I want** Epics waiting for dependencies to start automatically
**So that** I don't have to manually track when dependencies finish

**Acceptance Criteria:**

```gherkin
Given Epic 4 depends on Epic 1 and Epic 2
And both Epic 1 and Epic 2 are developing
And Epic 4 is in the queue with status "queued"
When Epic 1 completes and merges
Then Epic 4 remains queued (Epic 2 still developing)
When Epic 2 also completes and merges
Then AEDT automatically starts Epic 4 (dependencies satisfied)
And the CLI logs: "Epic 4 dependencies satisfied. Starting automatically."

Given the concurrency limit is reached
When a dependency completes
Then the queued Epic is not started yet (waits for slot)
```

**Prerequisites:** Story 5.6 (Epic completion handling), Story 5.2 (concurrency control)

**Technical Notes:**
- Implement Scheduler.auto_start_queued()
- Triggered: after Epic completion, after Subagent finishes
- Algorithm: 1) Get queued Epics, 2) For each, check if dependencies met and concurrency available, 3) Start if both true
- Use DependencyAnalyzer.get_parallel_epics(dag, completed_epic_ids)
- Affected components: Scheduler, DependencyAnalyzer
- FR coverage: FR25 (auto-start dependent Epics), FR9 (queue management)

---

### Epic 5 Complete Criteria

- All 7 Stories implemented and tested
- Users can start multiple Epics with one command
- Concurrency limit is enforced
- Execution mode (single/multi) is chosen correctly
- Single mode uses 1 Epic-level Subagent
- Multi mode uses Story-level Subagents with concurrency control
- Epic completion triggers quality checks and merge
- Queued Epics start automatically when dependencies complete
- Unit tests cover Scheduler, ScheduleQueue
- Integration test: start 5 Epics → 3 run, 2 queue → 1 completes → queue starts → dependencies auto-start

---

## Epic 6: Subagent Orchestration System

```yaml
epic_id: 6
title: "Subagent Orchestration System"
depends_on: [4, 5]
priority: HIGH
execution_mode: multi
story_concurrency: 3
estimated_stories: 6
```

### Description

As a user running parallel development, I need AEDT to orchestrate multiple AI Subagents (via Claude Code Task tool), monitor their progress in real-time, and allow me to pause/resume them, so that I have full control over the AI workforce.

**User Value:** Users can launch up to 5 Subagents simultaneously, track each one's progress in real-time, and intervene when needed (pause/resume).

**Scope:**
- Claude Code Task tool integration
- Epic-level Subagent launching (single mode)
- Story-level Subagent launching (multi mode)
- Progress monitoring and parsing
- Pause/resume Subagent control
- Subagent failure handling

### Stories

#### Story 6.1: Launch Epic-level Subagent via Claude Code Task

**As a** user
**I want** AEDT to start a Subagent for an entire Epic
**So that** the Epic is completed end-to-end by a single AI Agent

**Acceptance Criteria:**

```gherkin
Given Epic 1 is starting in "single" mode
When AEDT launches the Subagent
Then a Claude Code Task is created with:
  - Prompt: "Complete Epic 1: <title>. Stories: [list]. Work in <worktree_path>."
  - Working directory: <worktree_path>
And a Subagent record is created with: mode="epic", epic_id=1, status="running"
And the Subagent ID is stored in Epic state

Given the Subagent starts working
When I check the Agent status
Then the status shows: "Agent-1 (Epic 1) - Running"
```

**Prerequisites:** Epic 5 (Scheduler must start Epics), Epic 4 (Worktree must exist)

**Technical Notes:**
- Implement SubagentOrchestrator.start_epic_agent(epic, worktree_path) → Subagent
- Use Claude Code Task tool: call async task API with structured prompt
- Prompt template: see Story 6.3 for full format
- Subagent model: {id (UUID), epic_id, story_id (null), mode="epic", status, started_at, completed_at, output_log[]}
- Store Subagent in SubagentOrchestrator.agents dict
- Affected components: SubagentOrchestrator, TaskRunner (new wrapper for Task tool)
- FR coverage: FR19 (Claude Code Task integration)

---

#### Story 6.2: Launch Story-level Subagent (Multi Mode)

**As a** user
**I want** AEDT to start independent Subagents for each Story in large Epics
**So that** Stories are completed in parallel with focused context

**Acceptance Criteria:**

```gherkin
Given Epic 3 is starting in "multi" mode with 8 Stories
And story_concurrency is 3
When AEDT launches Subagents for the first 3 Stories
Then 3 Claude Code Tasks are created:
  - Subagent 1: Story 3.1
  - Subagent 2: Story 3.2
  - Subagent 3: Story 3.3
And each Task receives: "Complete Story 3.X: <title>. Prerequisites: <list>. Work in <worktree_path>."
And each Subagent record has: mode="story", epic_id=3, story_id="3.X"

Given Story 3.1 completes
When AEDT detects completion
Then Subagent 1 is marked as "completed"
And Story 3.4 (next in queue) is started with a new Subagent
```

**Prerequisites:** Story 6.1 (Subagent launching), Epic 5 Story 5.5 (multi mode)

**Technical Notes:**
- Implement SubagentOrchestrator.start_story_agent(story, epic, worktree_path) → Subagent
- Use Claude Code Task tool: call async task API with Story-focused prompt
- Prompt template: see Story 6.3
- All Story Subagents work in the same Worktree (Epic's Worktree)
- Track Story-level concurrency in Scheduler
- Affected components: SubagentOrchestrator, Scheduler
- FR coverage: FR19, Architecture requirement (Story-level Subagent)

---

#### Story 6.3: Build Structured Prompts for Subagents

**As a** developer
**I want** Subagent prompts to be clear and structured
**So that** Agents know exactly what to do

**Acceptance Criteria:**

```gherkin
Given Epic 1 has 5 Stories
When the Epic-level prompt is built
Then the prompt includes:
  - Epic title and description
  - Full list of Stories with titles and descriptions
  - Working directory path
  - Commit instructions: "Commit after each Story with message 'Story X: <title>'"
  - Progress reporting: "Output 'Story X completed' after each Story"

Given Story 3.2 has prerequisites: [Story 3.1]
When the Story-level prompt is built
Then the prompt includes:
  - Story title and description
  - Prerequisites: "Ensure Story 3.1 is completed first"
  - Commit instructions
```

**Prerequisites:** Story 6.1, 6.2 (launching must exist)

**Technical Notes:**
- Implement SubagentOrchestrator.build_epic_prompt(epic) → str
- Implement SubagentOrchestrator.build_story_prompt(story, epic) → str
- Epic prompt template:
  ```
  You are an AI development Agent. Complete the following Epic:

  Epic {epic.id}: {epic.title}
  {epic.description}

  Stories (complete in order):
  {for story in epic.stories: f"{story.id}. {story.title} - {story.description}"}

  Working directory: {worktree_path}

  Instructions:
  - Complete each Story sequentially
  - After each Story, run: git add . && git commit -m "Story {story.id}: {story.title}"
  - Output "Story {story.id} completed" after committing
  - Ensure all tests pass before committing
  ```
- Story prompt template: similar, focused on single Story + prerequisites
- Affected components: SubagentOrchestrator
- FR coverage: Context传递 for Subagents

---

#### Story 6.4: Monitor Subagent Progress and Parse Output

**As a** user
**I want** to see real-time progress of each Subagent
**So that** I know what's happening

**Acceptance Criteria:**

```gherkin
Given Subagent 1 is working on Epic 1 (5 Stories)
When the Subagent outputs "Story 1.1 completed"
Then AEDT detects the completion
And Epic 1 progress is updated to 20% (1/5)
And Story 1.1 status is set to "completed"
And the TUI displays: "Epic 1: 20% (Story 1/5)"

Given the Subagent outputs other text (logs, errors)
When AEDT monitors the output
Then the text is appended to the output_log
And displayed in the TUI log panel
```

**Prerequisites:** Story 6.1, 6.2 (Subagents must be running)

**Technical Notes:**
- Implement SubagentOrchestrator.monitor_agent(agent_id, callback)
- Use asyncio to poll Task tool for output updates
- Parse output with regex: `r"Story ([\d.]+) completed"`
- On match: extract Story ID, update StateManager (Story.status="completed", Epic.progress)
- Callback: notify Scheduler.on_story_completed(story_id, epic_id)
- Log buffer: append all output to Subagent.output_log (max 1000 lines in memory)
- Affected components: SubagentOrchestrator, StateManager, Scheduler
- FR coverage: FR22 (monitor Subagent output), FR15 (track Story progress)
- NFR compliance: NFR4 (log processing performance)

---

#### Story 6.5: Pause and Resume Subagents

**As a** user
**I want** to pause a running Subagent and resume it later
**So that** I can intervene when needed (e.g., conflict resolution)

**Acceptance Criteria:**

```gherkin
Given Subagent 1 is running Epic 1
When I run `aedt pause epic-1`
Then the Subagent is paused (if Task tool supports pause)
And Epic status is set to "paused"
And the TUI displays: "Epic 1: Paused"

Given Epic 1 is paused
When I run `aedt resume epic-1`
Then the Subagent resumes work
And Epic status is set to "developing"

Given the Task tool does not support pause
When I run `aedt pause epic-1`
Then the CLI displays: "Warning: Pause not supported. Subagent will continue. Use `aedt stop epic-1` to terminate."
```

**Prerequisites:** Story 6.1, 6.2 (Subagents must exist)

**Technical Notes:**
- Implement SubagentOrchestrator.pause_agent(agent_id) → bool
- Implement SubagentOrchestrator.resume_agent(agent_id) → bool
- If Task tool API supports pause: call pause API
- If not supported: log warning, Subagent continues (best effort)
- Update Epic.status in StateManager
- Affected components: SubagentOrchestrator, Scheduler, CLI
- FR coverage: FR23, FR24 (pause/resume)

---

#### Story 6.6: Handle Subagent Failures and Timeouts

**As a** user
**I want** AEDT to detect when a Subagent fails or times out
**So that** I can take corrective action

**Acceptance Criteria:**

```gherkin
Given a Subagent is running Epic 1
And the Subagent timeout is set to 3600 seconds
When 3600 seconds pass without completion
Then the Subagent is marked as "timeout"
And Epic status is set to "failed"
And the TUI displays: "Epic 1: Failed (timeout after 60 minutes)"

Given a Subagent encounters an error and crashes
When AEDT detects the failure
Then the Subagent is marked as "failed"
And Epic status is set to "failed"
And the error output is logged
And the user is prompted: "Epic 1 failed. View logs with `aedt logs epic-1`. Retry with `aedt retry epic-1`."
```

**Prerequisites:** Story 6.4 (monitoring must exist)

**Technical Notes:**
- Implement timeout tracking: SubagentOrchestrator checks elapsed time (started_at vs now)
- On timeout: mark Subagent.status="timeout", Epic.status="failed", stop monitoring
- Detect failure: Task tool returns error status, or Subagent exits unexpectedly
- On failure: log error output to Epic log file, notify user via TUI
- Do NOT auto-retry (avoid infinite loops)
- Provide manual retry: `aedt retry epic-1` re-creates Worktree and restarts
- Affected components: SubagentOrchestrator, Scheduler, StateManager
- FR coverage: NFR9 (Subagent异常处理), NFR12 (network fault tolerance)

---

### Epic 6 Complete Criteria

- All 6 Stories implemented and tested
- Epic-level Subagents can be launched via Claude Code Task
- Story-level Subagents work in multi mode
- Prompts are structured and clear
- Progress is monitored and parsed in real-time
- Pause/resume controls work (if supported by Task tool)
- Failures and timeouts are handled gracefully
- Unit tests cover SubagentOrchestrator methods
- Integration test: start Epic → monitor progress → pause → resume → complete

---

## Epic 7: Quality Gate System

```yaml
epic_id: 7
title: "Quality Gate System"
depends_on: [4]
priority: MEDIUM
execution_mode: single
story_concurrency: 1
estimated_stories: 5
```

### Description

As a user concerned with code quality, I need AEDT to automatically run linters, formatters, and tests at different stages (pre-commit, Epic completion, pre-merge), so that only high-quality code reaches the main branch.

**User Value:** Users get automated quality enforcement without manual intervention. Bad code is caught early, reducing merge-time issues.

**Scope:**
- Configurable quality gate rules (3 stages)
- Pre-commit checks (linter, formatter)
- Epic completion checks (unit tests)
- Pre-merge checks (integration tests)
- Failure notifications and blocking

### Stories

#### Story 7.1: Define Quality Gate Configuration Schema

**As a** user
**I want** to configure quality checks in `.aedt/config.yaml`
**So that** I can customize what checks run and when

**Acceptance Criteria:**

```gherkin
Given I have a project with AEDT
When I edit `.aedt/config.yaml` and add:
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
Then AEDT loads the configuration
And applies the rules at the specified stages

Given a rule has required: false
When the check fails
Then a warning is logged but the process continues
```

**Prerequisites:** Epic 1 (ConfigManager must exist)

**Technical Notes:**
- Extend config schema: add quality_gates{pre_commit[], epic_complete[], pre_merge[]}
- GateRule schema: {name, command, stage, required (bool), timeout (seconds)}
- Stages: "pre_commit" (before each Story commit), "epic_complete" (after all Stories), "pre_merge" (before merge to main)
- Affected components: ConfigManager, QualityGate (new module)
- FR coverage: FR39 (custom quality gate config)

---

#### Story 7.2: Run Pre-commit Checks Before Story Commits

**As a** user
**I want** linters and formatters to run before each Story is committed
**So that** code quality is enforced early

**Acceptance Criteria:**

```gherkin
Given pre_commit rules are configured (lint, format_check)
When a Subagent completes Story 1.1
And tries to commit
Then AEDT runs the pre_commit checks in the Worktree
And if all pass, the commit proceeds
And if any required check fails, the commit is blocked
And the Subagent is notified: "Pre-commit check failed: lint. Fix errors and retry."

Given a non-required check fails
When the commit is attempted
Then a warning is logged but the commit proceeds
```

**Prerequisites:** Story 7.1 (config must exist), Epic 6 (Subagents must work)

**Technical Notes:**
- Implement QualityGate.run_checks(stage="pre_commit", worktree_path) → List[TestResult]
- Use subprocess to run commands in the Worktree directory
- Capture stdout/stderr and exit code
- TestResult: {rule, passed (bool), output, error, duration}
- If any required=true check fails: return validation error, block commit
- Integrate with SubagentOrchestrator: before committing, run checks
- Affected components: QualityGate, SubagentOrchestrator
- FR coverage: FR36 (pre-commit checks)

---

#### Story 7.3: Run Epic Completion Checks (Unit Tests)

**As a** user
**I want** unit tests to run when an Epic is completed
**So that** I know the Epic works before merging

**Acceptance Criteria:**

```gherkin
Given epic_complete rules are configured (unit_tests)
When Epic 1 completes all Stories
Then AEDT runs the unit tests in the Worktree
And if tests pass, Epic status becomes "merging"
And if tests fail, Epic status becomes "failed"
And the failure output is logged and displayed in TUI

Given unit tests fail
When I view the Epic details
Then the TUI shows: "Epic 1: Failed (unit tests failed). View logs with `aedt logs epic-1`."
```

**Prerequisites:** Story 7.2 (QualityGate must exist), Epic 5 Story 5.6 (Epic completion handling)

**Technical Notes:**
- Integrate QualityGate.run_checks(stage="epic_complete", worktree_path) into Scheduler.on_epic_completed()
- If validation fails: set Epic.status="failed", store failure details in state
- Log test output to Epic-specific log file
- Notify TUI: display failure in Epic panel
- Affected components: QualityGate, Scheduler, StateManager
- FR coverage: FR37 (Epic completion tests)

---

#### Story 7.4: Run Pre-merge Checks (Integration Tests)

**As a** user
**I want** integration tests to run before merging to main
**So that** the merge doesn't break the main branch

**Acceptance Criteria:**

```gherkin
Given pre_merge rules are configured (integration_tests, e2e_tests)
When Epic 1 passes epic_complete checks
And is ready to merge
Then AEDT runs the pre_merge checks in the Worktree
And if all pass, the merge proceeds
And if any fail, the merge is blocked
And Epic status is set to "awaiting_merge"

Given integration tests fail
When I run `aedt merge epic-1 --force`
Then the checks are skipped (user override)
And the merge proceeds with a warning
```

**Prerequisites:** Story 7.3 (epic_complete checks), Epic 4 Story 4.5 (merge logic)

**Technical Notes:**
- Integrate QualityGate.run_checks(stage="pre_merge", worktree_path) into WorktreeManager.merge_to_main()
- If validation fails: abort merge, set Epic.status="awaiting_merge"
- Provide override: `aedt merge <epic-id> --force` skips checks (logs warning)
- Affected components: QualityGate, WorktreeManager, Scheduler
- FR coverage: FR38 (pre-merge tests)

---

#### Story 7.5: Notify User of Quality Check Failures

**As a** user
**I want** clear notifications when quality checks fail
**So that** I know what to fix

**Acceptance Criteria:**

```gherkin
Given a lint check fails with output: "src/parser.py:42: undefined variable 'x'"
When the check runs
Then the TUI displays:
  - Epic 1: Failed (pre_commit: lint)
  - "src/parser.py:42: undefined variable 'x'"
  - "Fix errors and run `aedt retry epic-1`"

Given I run `aedt logs epic-1`
When quality checks have failed
Then the full check output is displayed
And I can see detailed error messages
```

**Prerequisites:** Story 7.2, 7.3, 7.4 (checks must exist), Epic 8 (TUI must exist)

**Technical Notes:**
- Store TestResult in Epic state: Epic.quality_checks = {stage: [TestResult]}
- TUI EpicPanel: display failed checks with truncated error messages
- CLI `aedt logs epic-1`: read Epic log file, include quality check output
- Log format: `[Quality Gate] [pre_commit] lint FAILED: <output>`
- Affected components: QualityGate, StateManager, TUIApp, CLI
- FR coverage: FR40 (quality check failure notifications)

---

### Epic 7 Complete Criteria

- All 5 Stories implemented and tested
- Quality gate rules are configurable in config.yaml
- Pre-commit checks block bad commits
- Epic completion checks ensure unit tests pass
- Pre-merge checks prevent broken merges
- Failures are clearly communicated to the user
- Unit tests cover QualityGate methods
- Integration test: configure rules → commit with error → check fails → fix → check passes

---

## Epic 8: TUI Dashboard Real-time Visualization

```yaml
epic_id: 8
title: "TUI Dashboard Real-time Visualization"
depends_on: [2, 3]
priority: HIGH
execution_mode: multi
story_concurrency: 3
estimated_stories: 8
```

### Description

As a user managing multiple projects and Epics, I need a real-time terminal UI that displays all project statuses, Epic progress, Agent activities, and logs, so that I can monitor and control the entire workflow from a single interface.

**User Value:** Users get a powerful, keyboard-driven dashboard that shows everything at a glance, with real-time updates and intuitive navigation.

**Scope:**
- Multi-panel TUI layout (Textual framework)
- Project list panel
- Epic details panel with Story status
- Agent activity panel
- Real-time log panel
- Keyboard navigation (Vim-style)
- Search and filter
- Command mode
- Help system

### Stories

#### Story 8.1: TUI Application Framework and Layout

**As a** user
**I want** to launch a TUI dashboard with multiple panels
**So that** I can see all project information at once

**Acceptance Criteria:**

```gherkin
Given AEDT is initialized with projects
When I run `aedt start`
Then a TUI launches with 4 panels:
  - Header: "AEDT - AI Enhanced Delivery Toolkit | Projects: X | Active: Y"
  - Left panel (30%): Project list
  - Right-top panel (70%): Epic details
  - Right-bottom panel (70%): Logs
  - Footer: Keyboard shortcuts

Given the terminal is < 120 columns wide
When the TUI renders
Then the layout switches to single-column (stacked panels)
```

**Prerequisites:** Epic 2 (ProjectManager), Epic 3 (EpicParser)

**Technical Notes:**
- Use Textual framework for TUI
- Implement TUIApp(App) with compose() method
- Layout: Header, Container(ProjectPanel, EpicPanel, LogPanel), Footer
- Responsive: use Textual's responsive containers, switch layout at 120 columns
- Bindings: define keyboard shortcuts (q=quit, r=refresh, s=switch, /=search, :=command)
- Affected components: TUIApp (new module)
- FR coverage: FR41 (launch TUI)
- NFR compliance: NFR1 (TUI response < 100ms), NFR27 (terminal compatibility)

---

#### Story 8.2: Project List Panel with Status

**As a** user
**I want** to see all my projects in a list with their status
**So that** I can quickly switch between projects

**Acceptance Criteria:**

```gherkin
Given I have 3 projects (A, B, C)
When the TUI displays the Project List panel
Then I see:
  - Project A (5 Epics, 2 active) ⭐ Recommended
  - Project B (3 Epics, 0 active)
  - Project C (8 Epics, 3 active)

Given I press 'j' to move down the list
When I press Enter
Then the selected project becomes active
And the Epic panel updates to show that project's Epics
```

**Prerequisites:** Story 8.1 (TUI framework), Epic 2 (ProjectManager)

**Technical Notes:**
- Implement ProjectPanel(Static) with render() method
- Query ProjectManager.list_projects() for data
- Display: name, Epic count, active Epic count
- Highlight recommended project (from ProjectManager.recommend_next_project())
- Navigation: use Textual ListView or custom navigation with hjkl keys
- Affected components: TUIApp.ProjectPanel, ProjectManager
- FR coverage: FR43 (navigate projects), FR49 (switch projects)

---

#### Story 8.3: Epic Details Panel with Story List

**As a** user
**I want** to see detailed information about Epics and their Stories
**So that** I understand progress and dependencies

**Acceptance Criteria:**

```gherkin
Given I select Project A
When the Epic panel displays
Then I see a list of Epics:
  - Epic 1: Foundation (✓ Completed)
  - Epic 2: Parser (⚙ Developing 60%) [Story 3/5]
  - Epic 3: Scheduler (⏳ Queued)

Given I expand Epic 2 (press Enter)
When the panel updates
Then I see the Story list:
  - Story 2.1: Parse Epics (✓ Completed)
  - Story 2.2: Extract Stories (✓ Completed)
  - Story 2.3: Build DAG (⚙ In Progress)
  - Story 2.4: Parallel Epics (⏳ Pending)
  - Story 2.5: File Watching (⏳ Pending)

Given I press 'd' on Epic 2
When the dependencies view appears
Then I see: "Depends on: Epic 1 (✓ Completed)"
```

**Prerequisites:** Story 8.2 (project selection), Epic 3 (Epic parsing)

**Technical Notes:**
- Implement EpicPanel(Static) with render_epic_list() and render_story_list()
- Query StateManager for Epic statuses and progress
- Status icons: ✓ (completed), ⚙ (developing), ⏳ (queued), ✗ (failed), ⏸ (paused)
- Expandable: track selected Epic, toggle between Epic list and Story list
- Dependencies: show Epic.depends_on with status lookup
- Affected components: TUIApp.EpicPanel, StateManager
- FR coverage: FR44 (view Epic details), FR14 (view Story status), FR10 (view dependencies)

---

#### Story 8.4: Agent Activity Panel

**As a** user
**I want** to see which Subagents are currently running
**So that** I know what's being worked on

**Acceptance Criteria:**

```gherkin
Given 3 Subagents are running
When the Agent Activity panel displays
Then I see:
  - Agent-1 (Epic 2, mode=epic) → 60% (Story 3/5)
  - Agent-2 (Epic 3, mode=story, Story 3.1) → Running
  - Agent-3 (Epic 3, mode=story, Story 3.2) → Running

Given Epic 2 completes
When the Agent Activity updates
Then Agent-1 disappears from the list
And the panel shows: "2 active agents"
```

**Prerequisites:** Story 8.1 (TUI framework), Epic 6 (Subagent orchestration)

**Technical Notes:**
- Implement AgentPanel(Static) with render()
- Query SubagentOrchestrator.agents for running Subagents
- Display: Agent ID, Epic ID, mode (epic/story), Story ID (if story mode), status
- Progress: show Epic progress for epic-mode, "Running" for story-mode
- Affected components: TUIApp.AgentPanel, SubagentOrchestrator
- FR coverage: FR46 (view Agent activity)

---

#### Story 8.5: Real-time Log Panel with Auto-scroll

**As a** user
**I want** to see real-time logs from all Subagents
**So that** I can monitor what's happening

**Acceptance Criteria:**

```gherkin
Given Subagents are outputting logs
When the Log panel displays
Then I see recent log entries (max 1000 lines in memory):
  - [10:23:45] [Epic 2] Story 2.3: Implementing DAG builder
  - [10:24:12] [Epic 3] Story 3.1: Parsing Epic frontmatter
  - [10:24:30] [Epic 2] Story 2.3 completed

Given new logs are appended
When the panel refreshes
Then the log auto-scrolls to the latest entry

Given I press 'l' on an Epic
When the log view filters
Then only logs from that Epic are shown
```

**Prerequisites:** Story 8.1 (TUI framework), Epic 6 (Subagent output)

**Technical Notes:**
- Implement LogPanel(Static) with append_log() and render()
- Log buffer: List[str] (max 1000 lines in memory)
- Append logs from SubagentOrchestrator.monitor_agent() callback
- Auto-scroll: use Textual's RichLog widget with auto_scroll=True
- Filter: add LogPanel.set_filter(epic_id) to show only specific Epic
- Affected components: TUIApp.LogPanel, SubagentOrchestrator
- FR coverage: FR45 (view real-time logs)
- NFR compliance: NFR4 (log processing performance)

---

#### Story 8.6: Real-time Auto-refresh and Manual Refresh

**As a** user
**I want** the TUI to automatically update every 5 seconds
**So that** I see the latest status without manual action

**Acceptance Criteria:**

```gherkin
Given the TUI is running
When 5 seconds pass
Then all panels refresh with the latest data
And Epic progress percentages update
And Agent statuses update

Given I press 'r'
When the manual refresh is triggered
Then all panels refresh immediately (< 200ms)
And the last refresh time is displayed in the header
```

**Prerequisites:** Story 8.1-8.5 (all panels must exist)

**Technical Notes:**
- Implement TUIApp.auto_refresh() using Textual's set_interval(5.0, callback)
- Refresh all panels: call refresh() on ProjectPanel, EpicPanel, AgentPanel, LogPanel
- Manual refresh: bind 'r' key to TUIApp.action_refresh()
- Incremental update: only re-render changed components (Textual's reactive properties)
- Display refresh timestamp in Header: "Last updated: 10:25:30"
- Affected components: TUIApp (all panels)
- FR coverage: FR42 (real-time refresh)
- NFR compliance: NFR2 (refresh performance < 200ms)

---

#### Story 8.7: Search and Filter Epics

**As a** user
**I want** to search for Epics by keyword
**So that** I can quickly find what I need

**Acceptance Criteria:**

```gherkin
Given I press '/' in the TUI
When the search input appears at the bottom
And I type "parser"
Then the Epic panel filters to show only Epics with "parser" in title or description

Given I press 'f'
When the filter menu appears
And I select "Status: Developing"
Then only Epics with status="developing" are shown

Given I press Esc
When the filter is cleared
Then all Epics are shown again
```

**Prerequisites:** Story 8.3 (Epic panel must exist)

**Technical Notes:**
- Implement TUIApp.action_search() (/ key) to show input widget
- Fuzzy match: use simple substring matching on Epic.title and Epic.description
- Implement TUIApp.action_filter() (f key) to show filter menu
- Filter options: by status (developing/queued/completed/failed), by priority (high/medium/low)
- Store filter state in TUIApp, apply in EpicPanel.render()
- Affected components: TUIApp, EpicPanel
- FR coverage: FR47 (search), FR48 (filter)

---

#### Story 8.8: Command Mode and Help System

**As a** user
**I want** to execute commands via a Vim-style command mode
**So that** I can perform advanced operations

**Acceptance Criteria:**

```gherkin
Given I press ':' in the TUI
When the command input appears
And I type "pause epic-2"
Then Epic 2 is paused
And the command result is displayed: "Epic 2 paused successfully"

Given I press '?' in the TUI
When the help screen appears
Then I see:
  - All keyboard shortcuts (q, r, s, /, :, ?)
  - List of available commands (pause, resume, logs, clean, status, help)
  - Link to online documentation

Given I am using the TUI for the first time
When the TUI launches
Then a welcome message appears: "Welcome to AEDT! Press ? for help."
```

**Prerequisites:** Story 8.1 (TUI framework)

**Technical Notes:**
- Implement TUIApp.action_command_mode() (: key) to show command input widget
- Parse command: split by space, execute via Scheduler or CLI commands
- Supported commands: pause <epic-id>, resume <epic-id>, logs <epic-id>, clean, status, help
- Implement TUIApp.action_help() (? key) to show help screen (modal overlay)
- Help content: list of bindings, commands, link to README
- First-time check: create `.aedt/.first_run` flag, show tutorial if not exists
- Affected components: TUIApp, Scheduler, CLI
- FR coverage: FR50 (command mode), FR52 (help system), FR51 (first-time tutorial)

---

### Epic 8 Complete Criteria

- All 8 Stories implemented and tested
- TUI launches with multi-panel layout
- Project list shows all projects with status
- Epic panel displays detailed Epic and Story info
- Agent activity panel shows running Subagents
- Log panel displays real-time logs with auto-scroll
- Auto-refresh (5s) and manual refresh (r key) work
- Search and filter work correctly
- Command mode and help system are functional
- Unit tests cover TUI components (using Textual's test framework)
- Integration test: launch TUI → navigate → search → execute command

---

## FR Coverage Matrix

The following matrix shows how all 58 functional requirements are covered by Epics and Stories:

### Epic 1: Project Initialization and Foundation
- **FR53** - Story 1.1: Initialize AEDT configuration
- **FR54** - Story 1.3: Persist project and Epic states
- **FR55** - Story 1.5: Recover states after restart
- **FR56** - Story 1.2: Customize AEDT via config file
- **FR57** - Story 1.4: Generate structured logs

### Epic 2: Multi-Project Management Center
- **FR1** - Story 2.1: Add projects to AEDT
- **FR2** - Story 2.2: View project list and status
- **FR3** - Story 2.3: Remove projects
- **FR4** - Story 2.4: Intelligent project recommendation
- **FR5** - Story 2.5: Configure workflow type
- **FR58** - Story 2.6: Non-interactive status summary

### Epic 3: Epic Parsing and Dependency Analysis
- **FR6** - Story 3.1: Parse Epic documents
- **FR7** - Story 3.3: Extract Epic dependencies
- **FR8** - Story 3.4: Identify parallelizable Epics
- **FR9** - Story 3.5: Identify queued Epics
- **FR10** - Story 3.6: View Epic dependencies
- **FR11** - Story 3.1: Parse Epic priority (from frontmatter)
- **FR12** - Story 3.7: Monitor Epic file changes
- **FR13** - Story 3.2: Parse Story list
- **FR14** - Story 8.3: View Story status (in TUI)
- **FR15** - Story 6.4: Track Story progress

### Epic 4: Git Worktree Automation
- **FR18** - Story 4.1: Create Git Worktree for Epic
- **FR26** - Story 4.1: Auto-create Epic branch
- **FR27** - Story 4.8: Manage Worktree lifecycle
- **FR28** - Story 4.2: Subagent works in isolated Worktree
- **FR29** - Story 4.3: Auto-commit after each Story
- **FR30** - Story 4.5: Auto-merge to main branch
- **FR31** - Story 4.4: Detect file conflicts
- **FR32** - Story 4.6: Pause merge on conflict
- **FR33** - Story 4.7: Manual conflict resolution
- **FR34** - Story 4.7: Resume merge after resolution
- **FR35** - Story 4.8: Manual cleanup of Worktrees

### Epic 5: Intelligent Parallel Scheduling Engine
- **FR16** - Story 5.1: Select multiple Epics to start
- **FR17** - Story 5.1: Display dependencies and concurrency plan
- **FR20** - Story 5.2: Control max concurrent Subagents
- **FR21** - Story 5.2: Auto-queue Epics exceeding limit
- **FR25** - Story 5.7: Auto-start queued Epics when dependencies complete

### Epic 6: Subagent Orchestration System
- **FR19** - Story 6.1, 6.2: Launch Subagents via Claude Code Task
- **FR22** - Story 6.4: Monitor Subagent output and progress
- **FR23** - Story 6.5: Pause running Epic
- **FR24** - Story 6.5: Resume paused Epic

### Epic 7: Quality Gate System
- **FR36** - Story 7.2: Run pre-commit checks
- **FR37** - Story 7.3: Run Epic completion checks
- **FR38** - Story 7.4: Run pre-merge checks
- **FR39** - Story 7.1: Configure custom quality gates
- **FR40** - Story 7.5: Notify user of quality failures

### Epic 8: TUI Dashboard Real-time Visualization
- **FR41** - Story 8.1: Launch TUI Dashboard
- **FR42** - Story 8.6: Real-time auto-refresh
- **FR43** - Story 8.2: Navigate projects and Epics
- **FR44** - Story 8.3: View Epic details
- **FR45** - Story 8.5: View real-time logs
- **FR46** - Story 8.4: View Agent activity panel
- **FR47** - Story 8.7: Search Epics
- **FR48** - Story 8.7: Filter Epics
- **FR49** - Story 8.2: Switch projects
- **FR50** - Story 8.8: Command mode
- **FR51** - Story 8.8: First-time tutorial
- **FR52** - Story 8.8: Help system

### Coverage Summary
- **Total FRs:** 58
- **FRs Covered:** 58
- **Coverage:** 100%

**Validation:** All 58 functional requirements from the PRD are mapped to specific Epics and Stories. No FR is left uncovered.

---

## Epic Dependencies and Execution Order

### Dependency Graph

```
Epic 1 (Foundation)
  ├── Epic 2 (Multi-Project)
  ├── Epic 3 (Epic Parsing)
  └── Epic 4 (Git Worktree)
      ├── Epic 5 (Scheduler) ← also depends on Epic 3
      │   └── Epic 6 (Subagent) ← also depends on Epic 4
      └── Epic 7 (Quality Gate)

Epic 8 (TUI) ← depends on Epic 2, Epic 3
```

### Recommended Execution Order

**Phase 1: Foundation (Week 1)**
- Epic 1 (must complete first)
- Then in parallel: Epic 2, Epic 3, Epic 4

**Phase 2: Core Engine (Week 2-3)**
- Epic 5 (after Epic 3 and Epic 4 complete)
- Epic 6 (after Epic 4 and Epic 5 complete)
- Epic 7 (can run in parallel with Epic 5/6, only needs Epic 4)

**Phase 3: User Interface (Week 3-4)**
- Epic 8 (after Epic 2 and Epic 3 complete, can run in parallel with Epic 5/6/7)

**Total Estimated Duration:** 4 weeks (with parallel execution)
**Sequential Duration (without AEDT):** ~10-12 weeks

---

## Appendix: Story Template Reference

Each Story follows this structure:

```markdown
#### Story X.Y: <Title>

**As a** <user role>
**I want** <capability>
**So that** <business value>

**Acceptance Criteria:**

​```gherkin
Given <precondition>
When <action>
Then <expected outcome>
​```

**Prerequisites:** <List of prerequisite Story IDs or "None">

**Technical Notes:**
- Implementation guidance
- Affected components
- FR coverage
- NFR compliance
- Architecture decisions
```

---

**Document Status:** Complete
**Next Steps:** Begin implementation with Epic 1, following the recommended execution order.

