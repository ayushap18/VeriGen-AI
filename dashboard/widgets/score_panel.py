"""Score gauge panel with sparkline."""

from textual.app import ComposeResult
from textual.widgets import Static


class ScorePanel(Static):
    DEFAULT_CSS = """
    ScorePanel {
        height: 5;
        border: solid #2a2a4a;
        background: #0f0f1a;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self._score = 0.0
        self._delta = 0.0
        self._history: list[float] = []

    def compose(self) -> ComposeResult:
        yield Static("[#6666aa]SCORE[/#6666aa]", id="score-label")
        yield Static("[#00ff88 bold]0.0000[/#00ff88 bold]", id="score-value")
        yield Static("", id="score-delta")

    def update_score(self, score: float, delta: float):
        self._score = score
        self._delta = delta
        self._history.append(score)
        self.query_one("#score-value", Static).update(
            f"[#00ff88 bold]{score:.4f}[/#00ff88 bold]"
        )
        color = "#00ff88" if delta >= 0 else "#ff4444"
        sign = "+" if delta >= 0 else ""
        blocks = " \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
        spark = "".join(
            f"[#00ff88]{blocks[min(int(v * 8), 8)]}[/#00ff88]"
            for v in self._history[-20:]
        )
        self.query_one("#score-delta", Static).update(
            f"[{color}]{sign}{delta:.4f}[/{color}]  {spark}"
        )

    def reset(self):
        self._score = 0.0
        self._delta = 0.0
        self._history = []
        self.query_one("#score-value", Static).update("[#00ff88 bold]0.0000[/#00ff88 bold]")
        self.query_one("#score-delta", Static).update("")
