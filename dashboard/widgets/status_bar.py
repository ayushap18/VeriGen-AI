"""Bloomberg-style multi-segment status header — fully packed."""

import time
import random
from textual.widgets import Static


class StatusBar(Static):
    DEFAULT_CSS = """
    StatusBar {
        dock: top;
        height: 3;
        background: #0a1a0a;
        padding: 0 1;
        border-bottom: solid #1a3a1a;
    }
    """

    def __init__(self):
        super().__init__("")
        self._model = ""
        self._provider = ""
        self._status = "INITIALIZING"
        self._elapsed = 0.0
        self._score = 0.0
        self._tasks_done = 0
        self._tasks_total = 0
        self._tokens = 0
        self._cost = 0.0
        self._tps = 0.0
        self._rebuild()

    def set_config(self, model: str, provider: str, total_tasks: int):
        self._model = model
        self._provider = provider
        self._tasks_total = total_tasks
        self._status = "RUNNING"
        self._rebuild()

    def update_stats(self, elapsed: float = None, score: float = None,
                     tasks_done: int = None, tokens: int = None, cost: float = None,
                     status: str = None):
        if elapsed is not None:
            self._elapsed = elapsed
            if elapsed > 0 and self._tokens > 0:
                self._tps = self._tokens / elapsed
        if score is not None:
            self._score = score
        if tasks_done is not None:
            self._tasks_done = tasks_done
        if tokens is not None:
            self._tokens = tokens
        if cost is not None:
            self._cost = cost
        if status is not None:
            self._status = status
        self._rebuild()

    def _rebuild(self):
        m, s = divmod(int(self._elapsed), 60)
        h, m = divmod(m, 60)

        status_color = "#00ff88" if self._status == "RUNNING" else "#ffaa00" if self._status == "PAUSED" else "#00d4ff"
        dot = "\u25cf"

        # Progress percentage
        pct = (self._tasks_done / self._tasks_total * 100) if self._tasks_total > 0 else 0

        line1 = (
            f"[#00ff88 bold] \u25c8 VERIGEN-AI TERMINAL [/#00ff88 bold]"
            f"[#1a3a1a]\u2502[/#1a3a1a]"
            f"[{status_color}] {dot} {self._status} [/{status_color}]"
            f"[#1a3a1a]\u2502[/#1a3a1a]"
            f"[#3a6a3a] {self._provider} [/#3a6a3a]"
            f"[#1a3a1a]\u2502[/#1a3a1a]"
            f"[#00d4ff] {self._model} [/#00d4ff]"
            f"[#1a3a1a]\u2502[/#1a3a1a]"
            f"[#ffaa00] {h:02d}:{m:02d}:{s:02d} [/#ffaa00]"
            f"[#1a3a1a]\u2502[/#1a3a1a]"
            f"[#3a6a3a] TPS:[/#3a6a3a][#00d4ff]{self._tps:>6.1f}[/#00d4ff]"
            f"[#1a3a1a]\u2502[/#1a3a1a]"
            f"[#3a6a3a] PROGRESS:[/#3a6a3a][#00ff88]{pct:>5.1f}%[/#00ff88]"
        )

        score_bar_len = int(self._score * 20)
        score_bar = "[#00ff88]\u2588[/#00ff88]" * score_bar_len + "[#0a2a0a]\u2591[/#0a2a0a]" * (20 - score_bar_len)
        score_color = "#00ff88" if self._score >= 0.8 else "#ffaa00" if self._score >= 0.5 else "#ff4444"

        # Task progress mini-bar
        task_bar_len = int(self._tasks_done / self._tasks_total * 10) if self._tasks_total > 0 else 0
        task_bar = "[#00d4ff]\u2588[/#00d4ff]" * task_bar_len + "[#0a2a0a]\u2591[/#0a2a0a]" * (10 - task_bar_len)

        line2 = (
            f"[#3a6a3a] SCORE [/#3a6a3a]"
            f"[{score_color} bold]{self._score:.4f}[/{score_color} bold] "
            f"{score_bar}"
            f"[#1a3a1a] \u2502 [/#1a3a1a]"
            f"[#3a6a3a]TASKS [/#3a6a3a][#00ff88]{self._tasks_done}/{self._tasks_total}[/#00ff88] "
            f"{task_bar}"
            f"[#1a3a1a] \u2502 [/#1a3a1a]"
            f"[#3a6a3a]TOK [/#3a6a3a][#00d4ff]{self._tokens:,}[/#00d4ff]"
            f"[#1a3a1a] \u2502 [/#1a3a1a]"
            f"[#3a6a3a]COST [/#3a6a3a][#00ff88]${self._cost:.4f}[/#00ff88]"
            f"[#1a3a1a] \u2502 [/#1a3a1a]"
            f"[#3a6a3a]$/1K [/#3a6a3a][#ffaa00]${self._cost / max(self._tokens, 1) * 1000:.3f}[/#ffaa00]"
        )

        self.update(f"{line1}\n{line2}")
