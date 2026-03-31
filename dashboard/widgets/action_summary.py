"""Live action type breakdown — tracks what the agent is doing."""

from textual.widgets import Static

ACTION_COLORS = {
    "fill_value": "#00d4ff",
    "delete_row": "#ff4444",
    "fix_date": "#ffaa00",
    "fix_type": "#ffcc00",
    "normalize": "#aa66ff",
    "deduplicate": "#ff66aa",
    "cap_outlier": "#ff8800",
    "fix_boolean": "#66aaff",
    "set_value": "#00ff88",
    "drop_column": "#ff4444",
    "rename": "#aa66ff",
}


class ActionSummary(Static):
    DEFAULT_CSS = """
    ActionSummary {
        height: 1fr;
        border: solid #1a3a1a;
        background: #050a05;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__("[#00ff88 bold]\u25c9 ACTION SUMMARY[/#00ff88 bold]")
        self._actions: dict[str, int] = {}
        self._total_steps = 0
        self._undos = 0
        self._best_delta = 0.0
        self._worst_delta = 0.0

    def record_action(self, action_type: str, delta: float, undone: bool):
        self._total_steps += 1
        self._actions[action_type] = self._actions.get(action_type, 0) + 1
        if undone:
            self._undos += 1
        if delta > self._best_delta:
            self._best_delta = delta
        if delta < self._worst_delta:
            self._worst_delta = delta
        self._rebuild()

    def reset(self):
        self._actions.clear()
        self._total_steps = 0
        self._undos = 0
        self._best_delta = 0.0
        self._worst_delta = 0.0
        self._rebuild()

    def _rebuild(self):
        lines = ["[#00ff88 bold]\u25c9 ACTION SUMMARY[/#00ff88 bold]"]

        if not self._actions:
            lines.append("[#3a6a3a]  Awaiting agent actions...[/#3a6a3a]")
            self.update("\n".join(lines))
            return

        total = sum(self._actions.values())
        sorted_actions = sorted(self._actions.items(), key=lambda x: -x[1])

        # Stacked bar showing action distribution
        bar_width = 28
        bar_parts = []
        for action, count in sorted_actions:
            seg_len = max(1, round(count / total * bar_width))
            color = ACTION_COLORS.get(action, "#ccddcc")
            bar_parts.append(f"[{color}]{'\u2588' * seg_len}[/{color}]")
        lines.append(f"  {''.join(bar_parts)}")
        lines.append("")

        # Action breakdown with bars
        for action, count in sorted_actions:
            pct = count / total * 100
            color = ACTION_COLORS.get(action, "#ccddcc")
            mini_bar_len = max(1, int(pct / 100 * 12))
            mini_bar = f"[{color}]{'\u2588' * mini_bar_len}[/{color}]"
            lines.append(
                f"  [{color}]\u25cf {action:<16}[/{color}] "
                f"[#ccddcc]{count:>3}[/#ccddcc] "
                f"{mini_bar} "
                f"[#3a6a3a]{pct:>5.1f}%[/#3a6a3a]"
            )

        lines.append("")
        lines.append(f"[#1a3a1a]{'─' * 34}[/#1a3a1a]")

        # Stats row
        success_rate = ((self._total_steps - self._undos) / self._total_steps * 100) if self._total_steps > 0 else 0
        sr_color = "#00ff88" if success_rate >= 80 else "#ffaa00" if success_rate >= 50 else "#ff4444"

        lines.append(
            f"  [#3a6a3a]TOTAL:[/#3a6a3a] [#ccddcc]{self._total_steps}[/#ccddcc]"
            f"  [#3a6a3a]UNDO:[/#3a6a3a] [#ff4444]{self._undos}[/#ff4444]"
            f"  [#3a6a3a]OK:[/#3a6a3a] [{sr_color}]{success_rate:.0f}%[/{sr_color}]"
        )
        lines.append(
            f"  [#3a6a3a]BEST \u0394:[/#3a6a3a] [#00ff88]+{self._best_delta:.4f}[/#00ff88]"
            f"  [#3a6a3a]WORST \u0394:[/#3a6a3a] [#ff4444]{self._worst_delta:.4f}[/#ff4444]"
        )

        self.update("\n".join(lines))
