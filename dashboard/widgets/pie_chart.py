"""ASCII pie chart for error type distribution."""

import math
from textual.widgets import Static

ERROR_COLORS = {
    "duplicate_row": "#ff4444",
    "wrong_computed": "#ff8800",
    "malformed_date": "#ffaa00",
    "missing_value": "#00d4ff",
    "negative_value": "#ff66aa",
    "outlier": "#aa66ff",
    "invalid_boolean": "#66aaff",
    "type_error": "#ffcc00",
}


class PieChart(Static):
    DEFAULT_CSS = """
    PieChart {
        height: auto;
        min-height: 8;
        border: solid #1a3a1a;
        background: #050a05;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__("[#00ff88 bold]\u25c9 ERROR DISTRIBUTION[/#00ff88 bold]")
        self._data: dict[str, int] = {}

    def update_data(self, breakdown: dict[str, int]):
        self._data = breakdown
        self._rebuild()

    def _rebuild(self):
        if not self._data:
            self.update(
                "[#00ff88 bold]\u25c9 ERROR DISTRIBUTION[/#00ff88 bold]\n"
                "[#00ff88]  \u2713 ALL CLEAN \u2014 0 errors[/#00ff88]"
            )
            return

        total = sum(self._data.values())
        lines = ["[#00ff88 bold]\u25c9 ERROR DISTRIBUTION[/#00ff88 bold]"]

        # Build pie segments
        pie_chars = "\u2588\u2593\u2592\u2591"
        segments = sorted(self._data.items(), key=lambda x: -x[1])

        # Draw a horizontal stacked bar as "pie"
        bar_width = 30
        bar_parts = []
        for err_type, count in segments:
            seg_len = max(1, round(count / total * bar_width))
            color = ERROR_COLORS.get(err_type, "#ccddcc")
            bar_parts.append(f"[{color}]{'\u2588' * seg_len}[/{color}]")

        lines.append(f"  {''.join(bar_parts)}")
        lines.append("")

        # Legend with percentages
        for err_type, count in segments:
            pct = count / total * 100
            color = ERROR_COLORS.get(err_type, "#ccddcc")
            dot = "\u25cf"
            lines.append(
                f"  [{color}]{dot} {err_type:<18} {count:>3} ({pct:>5.1f}%)[/{color}]"
            )

        lines.append(f"[#3a6a3a]  Total: {total} errors[/#3a6a3a]")
        self.update("\n".join(lines))
