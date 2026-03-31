"""End-of-run summary screen with final scores, token usage, and run history."""

from datetime import datetime
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, DataTable, Footer, Rule, Button
from textual.binding import Binding

from agent.events import RunComplete
from dashboard.config import load_config, save_config


class SummaryScreen(Screen):
    CSS = """
    Screen { background: #0a0a0f; }
    #summary-header {
        dock: top; height: 1; background: #1a1a2e;
        color: #00d4ff; text-style: bold; padding: 0 1;
    }
    #summary-outer { padding: 1 2; }
    .summary-panel {
        border: solid #2a2a4a; background: #0f0f1a;
        padding: 0 1; margin: 1 0;
    }
    .summary-label { color: #00d4ff; text-style: bold; }
    #avg-score { color: #00ff88; text-style: bold; }
    #btn-row { height: 3; margin-top: 1; }
    #rerun-btn { margin-right: 2; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "rerun", "Rerun"),
    ]

    def __init__(self, result: RunComplete, model: str, provider: str):
        super().__init__()
        self.result = result
        self.model = model
        self.provider = provider

    def compose(self) -> ComposeResult:
        yield Static(
            " VERIGEN-AI  \u2502  RUN COMPLETE",
            id="summary-header"
        )

        with Vertical(id="summary-outer"):
            with Vertical(classes="summary-panel"):
                yield Static("[#00d4ff bold]FINAL SCORES[/#00d4ff bold]", classes="summary-label")
                yield DataTable(id="scores-table")

            with Horizontal():
                with Vertical(classes="summary-panel"):
                    yield Static("[#00d4ff bold]STATS[/#00d4ff bold]", classes="summary-label")
                    m, s = divmod(int(self.result.elapsed_seconds), 60)
                    yield Static(
                        f"  [#6666aa]Time:[/#6666aa]       [#ccccdd]{m}m{s:02d}s[/#ccccdd]\n"
                        f"  [#6666aa]Tokens In:[/#6666aa]  [#ccccdd]{self.result.total_tokens_in:,}[/#ccccdd]\n"
                        f"  [#6666aa]Tokens Out:[/#6666aa] [#ccccdd]{self.result.total_tokens_out:,}[/#ccccdd]\n"
                        f"  [#6666aa]Cost:[/#6666aa]       [#00ff88]${self.result.total_cost:.4f}[/#00ff88]"
                    )

                with Vertical(classes="summary-panel"):
                    yield Static("[#00d4ff bold]AVERAGE[/#00d4ff bold]", classes="summary-label")
                    bar_len = int(self.result.average * 30)
                    bar = "\u2588" * bar_len + "\u2591" * (30 - bar_len)
                    yield Static(
                        f"\n  [#00ff88 bold]{self.result.average:.4f}[/#00ff88 bold]\n"
                        f"  [#00ff88]{bar}[/#00ff88]",
                        id="avg-score"
                    )

            with Vertical(classes="summary-panel"):
                yield Static("[#00d4ff bold]RUN HISTORY (last 5)[/#00d4ff bold]", classes="summary-label")
                yield DataTable(id="history-table")

            with Horizontal(id="btn-row"):
                yield Button("Rerun", id="rerun-btn", variant="primary")
                yield Button("Quit", id="quit-btn", variant="error")

        yield Footer()

    def on_mount(self):
        # Scores table
        table = self.query_one("#scores-table", DataTable)
        table.add_columns("Task", "Score")
        for task_id, score in self.result.scores.items():
            table.add_row(task_id, f"{score:.4f}")
        table.add_row("AVERAGE", f"{self.result.average:.4f}")

        # Save run to history
        config = load_config()
        config.add_run({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "model": self.model,
            "provider": self.provider,
            "average": round(self.result.average, 4),
            "cost": round(self.result.total_cost, 6),
            "elapsed": round(self.result.elapsed_seconds, 1),
            "scores": {k: round(v, 4) for k, v in self.result.scores.items()},
        })
        save_config(config)

        # History table
        hist_table = self.query_one("#history-table", DataTable)
        hist_table.add_columns("Date", "Model", "Avg", "Cost", "Time")
        for run in reversed(config.run_history[-5:]):
            m, s = divmod(int(run.get("elapsed", 0)), 60)
            hist_table.add_row(
                run.get("date", "?"),
                run.get("model", "?")[:20],
                f"{run.get('average', 0):.4f}",
                f"${run.get('cost', 0):.4f}",
                f"{m}m{s:02d}s"
            )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "quit-btn":
            self.app.exit()
        elif event.button.id == "rerun-btn":
            self.app.pop_screen()
            self.app.pop_screen()  # Back to setup

    def action_quit(self):
        self.app.exit()

    def action_rerun(self):
        self.app.pop_screen()
        self.app.pop_screen()
