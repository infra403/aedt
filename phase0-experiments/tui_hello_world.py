"""
Textual TUI Hello World - Phase 0 验证
验证 Textual 框架的基本功能和性能
"""
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Label
from textual.binding import Binding


class HelloWorldApp(App):
    """简单的 TUI 应用，验证 Textual 框架"""

    CSS = """
    Screen {
        background: $surface;
    }

    #project_list {
        width: 30%;
        border: solid $primary;
    }

    #epic_details {
        width: 70%;
        border: solid $secondary;
    }

    .status_complete {
        color: $success;
    }

    .status_progress {
        color: $warning;
    }

    .status_queued {
        color: $accent;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        ("s", "switch_project", "Switch Project"),
    ]

    def compose(self) -> ComposeResult:
        """创建 TUI 布局"""
        yield Header()

        with Horizontal():
            # 左侧：项目列表
            with Vertical(id="project_list"):
                yield Static("📁 Projects", classes="section_header")
                yield Label("├─ AEDT          [5 epics]", classes="status_progress")
                yield Label("├─ Other Project [2 epics]", classes="status_complete")
                yield Label("└─ Demo App      [3 epics]", classes="status_queued")

            # 右侧：Epic 详情
            with Vertical(id="epic_details"):
                yield Static("🎯 Epic Details", classes="section_header")
                yield Label("Epic 1: 多项目管理     ✓ Complete", classes="status_complete")
                yield Label("Epic 2: BMAD 集成      ⚙ Developing 60%", classes="status_progress")
                yield Label("Epic 3: 调度引擎       ⏳ Queued", classes="status_queued")

        yield Footer()

    def action_quit(self) -> None:
        """退出应用"""
        self.exit()

    def action_refresh(self) -> None:
        """刷新状态"""
        self.notify("状态已刷新！", title="Refresh", timeout=2)

    def action_switch_project(self) -> None:
        """切换项目"""
        self.notify("切换项目功能演示", title="Switch Project", timeout=2)


if __name__ == "__main__":
    app = HelloWorldApp()
    app.run()
