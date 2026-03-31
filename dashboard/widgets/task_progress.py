"""Task progress bars panel."""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class TaskProgress(Widget):
    DEFAULT_CSS = """
    TaskProgress {
        height: auto;
        max-height: 10;
        border: solid #2a2a4a;
        background: #0f0f1a;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self._tasks: list[str] = []
        self._scores: dict[str, float] = {}
        self._active: str = ""

    def compose(self) -> ComposeResult:
        yield Static("[#6666aa]TASK PROGRESS[/#6666aa]", id="tp-label")
        yield Static("", id="tp-content")

    def set_tasks(self, task_ids: list[str]):
        self._tasks = task_ids
        self._scores = {}
        self._active = ""
        self._render()

    def set_active(self, task_id: str):
        self._active = task_id
        self._render()

    def set_score(self, task_id: str, score: float):
        self._scores[task_id] = score
        self._render()

    def _render(self):
        lines = []
        for tid in self._tasks:
            short = tid[:22].ljust(22)
            score = self._scores.get(tid)
            if tid == self._active and score is None:
                lines.append(f"[#ffaa00 bold]  {short} > running...[/#ffaa00 bold]")
            elif score is not None:
                bar_len = int(score * 20)
                bar = "\u2588" * bar_len + "\u2591" * (20 - bar_len)
                color = "#00ff88" if score >= 0.8 else "#ffaa00" if score >= 0.5 else "#ff4444"
                marker = " <" if tid == self._active else ""
                lines.append(f"  [{color}]{short} {bar} {score:.3f}{marker}[/{color}]")
            else:
                lines.append(f"  [#444466]{short} {'\u2591' * 20} ---[/#444466]")
        self.query_one("#tp-content", Static).update("\n".join(lines))
