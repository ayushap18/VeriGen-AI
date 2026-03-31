"""Error breakdown horizontal bar chart."""

from textual.app import ComposeResult
from textual.widget import Widget
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


class ErrorChart(Widget):
    DEFAULT_CSS = """
    ErrorChart {
        height: auto;
        max-height: 12;
        border: solid #2a2a4a;
        background: #0f0f1a;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("[#6666aa]ERROR BREAKDOWN[/#6666aa]", id="ec-label")
        yield Static("", id="ec-content")

    def update_errors(self, breakdown: dict[str, int]):
        if not breakdown:
            self.query_one("#ec-content", Static).update(
                "[#00ff88]  No errors remaining[/#00ff88]"
            )
            return
        max_count = max(breakdown.values()) if breakdown else 1
        lines = []
        for err_type, count in sorted(breakdown.items(), key=lambda x: -x[1]):
            bar_len = int((count / max_count) * 15)
            bar = "\u2588" * bar_len
            color = ERROR_COLORS.get(err_type, "#ccccdd")
            lines.append(f"  [{color}]{err_type:<18} {bar} {count}[/{color}]")
        self.query_one("#ec-content", Static).update("\n".join(lines))
