"""Scrolling action log feed."""

from textual.widgets import RichLog


class ActionFeed(RichLog):
    DEFAULT_CSS = """
    ActionFeed {
        height: 10;
        border: solid #2a2a4a;
        background: #0f0f1a;
    }
    """

    def __init__(self):
        super().__init__(highlight=True, markup=True, wrap=False, max_lines=200)

    def log_step(self, step: int, action_type: str, target: str,
                 score: float, delta: float, undone: bool):
        sign = "+" if delta >= 0 else ""
        delta_color = "#00ff88" if delta >= 0 else "#ff4444"
        undo_marker = " [#ff4444]UNDO[/#ff4444]" if undone else ""

        line = (
            f"  [#6666aa]#{step:>3}[/#6666aa]  "
            f"[#00d4ff]{action_type:<16}[/#00d4ff] "
            f"[#ccccdd]{target:<20}[/#ccccdd] "
            f"[{delta_color}]{sign}{delta:.4f}[/{delta_color}]  "
            f"[#00ff88]{score:.4f}[/#00ff88]"
            f"{undo_marker}"
        )
        self.write(line)

    def log_message(self, msg: str, color: str = "#6666aa"):
        self.write(f"  [{color}]{msg}[/{color}]")
