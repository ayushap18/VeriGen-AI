"""Score gauge panel with sparkline — Bloomberg green style."""

from textual.widgets import Static


class ScorePanel(Static):
    DEFAULT_CSS = """
    ScorePanel {
        height: 7;
        border: solid #1a3a1a;
        background: #050a05;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__(self._build_display(0.0, 0.0, []))
        self._score = 0.0
        self._delta = 0.0
        self._history: list[float] = []

    def _build_display(self, score: float, delta: float, history: list[float]) -> str:
        color = "#00ff88" if score >= 0.8 else "#ffaa00" if score >= 0.5 else "#ff4444"
        delta_color = "#00ff88" if delta >= 0 else "#ff4444"
        sign = "+" if delta >= 0 else ""

        bar_len = int(score * 30)
        bar = f"[{color}]\u2588[/{color}]" * bar_len + "[#0a2a0a]\u2591[/#0a2a0a]" * (30 - bar_len)

        blocks = " \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
        spark = "".join(
            f"[#00ff88]{blocks[min(int(v * 8), 8)]}[/#00ff88]"
            for v in history[-30:]
        )

        return (
            f"[#00ff88 bold]\u25c9 SCORE[/#00ff88 bold]\n"
            f"[{color} bold]  {score:.4f}[/{color} bold]"
            f"  [{delta_color}]{sign}{delta:.4f}[/{delta_color}]\n"
            f"  {bar}\n"
            f"[#3a6a3a]  Trend:[/#3a6a3a] {spark}\n"
            f"[#3a6a3a]  Samples: {len(history)}[/#3a6a3a]"
        )

    def update_score(self, score: float, delta: float):
        self._score = score
        self._delta = delta
        self._history.append(score)
        self.update(self._build_display(score, delta, self._history))

    def reset(self):
        self._score = 0.0
        self._delta = 0.0
        self._history = []
        self.update(self._build_display(0.0, 0.0, []))
