"""Error breakdown horizontal bar chart — Bloomberg style."""

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

ERROR_ICONS = {
    "duplicate_row": "\u229e",
    "wrong_computed": "\u2234",
    "malformed_date": "\u29d6",
    "missing_value": "\u2205",
    "negative_value": "\u2296",
    "outlier": "\u26a0",
    "invalid_boolean": "\u2262",
    "type_error": "\u2260",
}


class ErrorChart(Static):
    DEFAULT_CSS = """
    ErrorChart {
        height: auto;
        max-height: 14;
        border: solid #1a3a1a;
        background: #050a05;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__("[#00ff88 bold]\u25c9 ERROR BREAKDOWN[/#00ff88 bold]")

    def update_errors(self, breakdown: dict[str, int]):
        if not breakdown:
            self.update(
                "[#00ff88 bold]\u25c9 ERROR BREAKDOWN[/#00ff88 bold]\n"
                "[#00ff88]\n  \u2713 ALL CLEAR — No errors remaining\n"
                "  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588 100% CLEAN[/#00ff88]"
            )
            return

        total = sum(breakdown.values())
        max_count = max(breakdown.values()) if breakdown else 1
        lines = ["[#00ff88 bold]\u25c9 ERROR BREAKDOWN[/#00ff88 bold]"]
        lines.append(f"[#3a6a3a]  Total errors: {total}[/#3a6a3a]")

        for err_type, count in sorted(breakdown.items(), key=lambda x: -x[1]):
            bar_len = int((count / max_count) * 18)
            bar = "\u2588" * bar_len
            color = ERROR_COLORS.get(err_type, "#ccccdd")
            icon = ERROR_ICONS.get(err_type, "\u25aa")
            pct = count / total * 100
            lines.append(
                f"  [{color}]{icon} {err_type:<18} {bar:<18} {count:>3} ({pct:>5.1f}%)[/{color}]"
            )
        self.update("\n".join(lines))
