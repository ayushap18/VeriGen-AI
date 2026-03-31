"""VeriGen-AI Textual App — screen routing and lifecycle."""

from textual.app import App
from textual.binding import Binding

from dashboard.screens.setup import SetupScreen
from dashboard.screens.run import RunScreen
from dashboard.screens.summary import SummaryScreen
from dashboard.config import VeriGenConfig, load_config
from agent.events import RunComplete


class VeriGenApp(App):
    TITLE = "VeriGen-AI"
    SUB_TITLE = "Data Cleaning Agent Dashboard"
    CSS_PATH = "../dashboard.css"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.launch_config: VeriGenConfig | None = None
        self.run_result: RunComplete | None = None

    def on_mount(self):
        self.push_screen(SetupScreen())

    def push_screen(self, screen, *args, **kwargs):
        if isinstance(screen, str):
            if screen == "run" and self.launch_config:
                run_screen = RunScreen(self.launch_config)
                super().push_screen(run_screen)
                return
            elif screen == "summary" and self.run_result:
                config = self.launch_config or load_config()
                summary = SummaryScreen(self.run_result, config.model, config.provider)
                super().push_screen(summary)
                return
        super().push_screen(screen, *args, **kwargs)
