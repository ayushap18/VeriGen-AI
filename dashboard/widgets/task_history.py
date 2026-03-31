"""Task score history panel — shows completed task results."""

from textual.widgets import Static


class TaskHistory(Static):
    DEFAULT_CSS = """
    TaskHistory {
        height: auto;
        border: solid #1a3a1a;
        background: #050a05;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__("[#00ff88 bold]\u25c9 COMPLETED TASKS[/#00ff88 bold]")
        self._results: list[dict] = []

    def add_result(self, task_id: str, score: float, steps: int, errors_left: int):
        self._results.append({
            "task_id": task_id, "score": score,
            "steps": steps, "errors_left": errors_left,
        })
        self._rebuild()

    def _rebuild(self):
        lines = ["[#00ff88 bold]\u25c9 COMPLETED TASKS[/#00ff88 bold]"]

        if not self._results:
            lines.append("[#3a6a3a]  No tasks completed yet[/#3a6a3a]")
            self.update("\n".join(lines))
            return

        lines.append(
            f"[#3a6a3a]  {'Task':<26} {'Score':>7} {'Steps':>6} {'Err':>4}[/#3a6a3a]"
        )
        lines.append(f"[#1a3a1a]  {'─' * 48}[/#1a3a1a]")

        total_score = 0.0
        for r in self._results:
            tid = r["task_id"][:25].ljust(25)
            sc = r["score"]
            total_score += sc
            color = "#00ff88" if sc >= 0.8 else "#ffaa00" if sc >= 0.5 else "#ff4444"
            icon = "\u2713" if sc >= 0.8 else "\u26a0" if sc >= 0.5 else "\u2717"

            bar_len = int(sc * 15)
            bar = f"[{color}]\u2588[/{color}]" * bar_len + "[#0a2a0a]\u2591[/#0a2a0a]" * (15 - bar_len)

            lines.append(
                f"  [{color}]{icon} {tid} {sc:>6.4f} {r['steps']:>5} {r['errors_left']:>4}[/{color}]"
            )
            lines.append(f"    {bar}")

        if len(self._results) > 0:
            avg = total_score / len(self._results)
            avg_color = "#00ff88" if avg >= 0.8 else "#ffaa00" if avg >= 0.5 else "#ff4444"
            lines.append(f"[#1a3a1a]  {'─' * 48}[/#1a3a1a]")
            lines.append(
                f"  [{avg_color} bold]AVG: {avg:.4f} ({len(self._results)} tasks)[/{avg_color} bold]"
            )

        self.update("\n".join(lines))
