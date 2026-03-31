"""End-of-run summary screen — Bloomberg terminal style."""

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
    Screen { background: #020502; }
    #summary-header {
        dock: top; height: 3; background: #0a1a0a;
        color: #00ff88; text-style: bold; padding: 0 1;
        border-bottom: solid #1a3a1a;
    }
    #summary-outer { padding: 1 2; }
    .summary-panel {
        border: solid #1a3a1a; background: #050a05;
        padding: 0 1; margin: 1 0;
    }
    .summary-label { color: #00ff88; text-style: bold; }
    #avg-score { color: #00ff88; text-style: bold; }
    #btn-row { height: 3; margin-top: 1; }
    #rerun-btn {
        margin-right: 2;
        background: #0a2a0a;
        color: #00ff88;
        border: solid #00ff88;
    }
    #quit-btn {
        background: #2a0a0a;
        color: #ff4444;
        border: solid #ff4444;
    }
    DataTable { background: #050a05; }
    DataTable > .datatable--header {
        background: #0a1a0a;
        color: #00ff88;
        text-style: bold;
    }
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
        m, s = divmod(int(self.result.elapsed_seconds), 60)
        avg_color = "#00ff88" if self.result.average >= 0.8 else "#ffaa00" if self.result.average >= 0.5 else "#ff4444"

        yield Static(
            f"[#00ff88 bold] VERIGEN-AI TERMINAL[/#00ff88 bold]\n"
            f"[#3a6a3a] RUN COMPLETE \u2502 {self.model} \u2502 "
            f"AVG: [{avg_color}]{self.result.average:.4f}[/{avg_color}] \u2502 "
            f"TIME: {m:02d}:{s:02d}[/#3a6a3a]",
            id="summary-header"
        )

        with Vertical(id="summary-outer"):
            with Vertical(classes="summary-panel"):
                yield Static("[#00ff88 bold]\u25c9 FINAL SCORES[/#00ff88 bold]", classes="summary-label")
                yield DataTable(id="scores-table")

            with Horizontal():
                with Vertical(classes="summary-panel"):
                    yield Static("[#00ff88 bold]\u25c9 STATS[/#00ff88 bold]", classes="summary-label")
                    yield Static(
                        f"  [#3a6a3a]Time:[/#3a6a3a]       [#ffaa00]{m:02d}:{s:02d}[/#ffaa00]\n"
                        f"  [#3a6a3a]Tokens In:[/#3a6a3a]  [#00d4ff]{self.result.total_tokens_in:,}[/#00d4ff]\n"
                        f"  [#3a6a3a]Tokens Out:[/#3a6a3a] [#ffaa00]{self.result.total_tokens_out:,}[/#ffaa00]\n"
                        f"  [#3a6a3a]Cost:[/#3a6a3a]       [#00ff88]${self.result.total_cost:.4f}[/#00ff88]"
                    )

                with Vertical(classes="summary-panel"):
                    yield Static("[#00ff88 bold]\u25c9 AVERAGE[/#00ff88 bold]", classes="summary-label")
                    bar_len = int(self.result.average * 30)
                    bar = f"[{avg_color}]\u2588[/{avg_color}]" * bar_len + "[#0a2a0a]\u2591[/#0a2a0a]" * (30 - bar_len)
                    yield Static(
                        f"\n  [{avg_color} bold]{self.result.average:.4f}[/{avg_color} bold]\n"
                        f"  {bar}",
                        id="avg-score"
                    )

            with Vertical(classes="summary-panel"):
                yield Static("[#00ff88 bold]\u25c9 RUN HISTORY (last 5)[/#00ff88 bold]", classes="summary-label")
                yield DataTable(id="history-table")

            with Horizontal(id="btn-row"):
                yield Button("\u25b6  RERUN", id="rerun-btn", variant="success")
                yield Button("\u25a0  QUIT", id="quit-btn", variant="error")

        yield Footer()

    def on_mount(self):
        table = self.query_one("#scores-table", DataTable)
        table.add_columns("Task", "Score", "Status")
        for task_id, score in self.result.scores.items():
            status = "\u2713 PASS" if score >= 0.8 else "\u26a0 WARN" if score >= 0.5 else "\u2717 FAIL"
            table.add_row(task_id, f"{score:.4f}", status)
        table.add_row("AVERAGE", f"{self.result.average:.4f}", "")

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

        hist_table = self.query_one("#history-table", DataTable)
        hist_table.add_columns("Date", "Model", "Avg", "Cost", "Time")
        for run in reversed(config.run_history[-5:]):
            rm, rs = divmod(int(run.get("elapsed", 0)), 60)
            hist_table.add_row(
                run.get("date", "?"),
                run.get("model", "?")[:20],
                f"{run.get('average', 0):.4f}",
                f"${run.get('cost', 0):.4f}",
                f"{rm:02d}:{rs:02d}"
            )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "quit-btn":
            self.app.exit()
        elif event.button.id == "rerun-btn":
            self.app.pop_screen()
            self.app.pop_screen()

    def action_quit(self):
        self.app.exit()

    def action_rerun(self):
        self.app.pop_screen()
        self.app.pop_screen()
