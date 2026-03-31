"""Task progress bars panel — Bloomberg terminal style."""

from textual.widgets import Static


class TaskProgress(Static):
    DEFAULT_CSS = """
    TaskProgress {
        height: auto;
        max-height: 12;
        border: solid #1a3a1a;
        background: #050a05;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__("[#00ff88 bold]\u25c9 TASK QUEUE[/#00ff88 bold]")
        self._tasks: list[str] = []
        self._scores: dict[str, float] = {}
        self._active: str = ""

    def set_tasks(self, task_ids: list[str]):
        self._tasks = task_ids
        self._scores = {}
        self._active = ""
        self._rebuild()

    def set_active(self, task_id: str):
        self._active = task_id
        self._rebuild()

    def set_score(self, task_id: str, score: float):
        self._scores[task_id] = score
        self._rebuild()

    def _rebuild(self):
        lines = ["[#00ff88 bold]\u25c9 TASK QUEUE[/#00ff88 bold]"]
        for i, tid in enumerate(self._tasks):
            short = tid[:24].ljust(24)
            score = self._scores.get(tid)
            idx = f"[#3a6a3a]{i+1:>2}.[/#3a6a3a]"

            if tid == self._active and score is None:
                lines.append(
                    f"  {idx} [#ffaa00 bold]\u25b6 {short} "
                    f"[blink]\u2588\u2588\u2588[/blink] PROCESSING...[/#ffaa00 bold]"
                )
            elif score is not None:
                bar_len = int(score * 20)
                bar = "\u2588" * bar_len + "\u2591" * (20 - bar_len)
                color = "#00ff88" if score >= 0.8 else "#ffaa00" if score >= 0.5 else "#ff4444"
                marker = " [#00ff88]\u25c0[/#00ff88]" if tid == self._active else ""
                status = "\u2713" if tid != self._active else "\u25b6"
                lines.append(
                    f"  {idx} [{color}]{status} {short} {bar} {score:.3f}{marker}[/{color}]"
                )
            else:
                lines.append(
                    f"  {idx} [#1a3a1a]\u25cb {short} {'.' * 20} QUEUED[/#1a3a1a]"
                )
        self.update("\n".join(lines))
