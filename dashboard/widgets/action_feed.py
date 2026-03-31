"""Scrolling action log feed — Bloomberg terminal style."""

from textual.widgets import RichLog


class ActionFeed(RichLog):
    DEFAULT_CSS = """
    ActionFeed {
        height: 100%;
        min-height: 10;
        border: solid #1a3a1a;
        background: #050a05;
        scrollbar-color: #1a3a1a;
        scrollbar-color-hover: #2a5a2a;
    }
    """

    def __init__(self):
        super().__init__(highlight=True, markup=True, wrap=False, max_lines=500)

    def on_mount(self):
        self.write("[#00ff88 bold]\u25c9 ACTION LOG[/#00ff88 bold]")
        self.write("[#1a3a1a]" + "\u2500" * 60 + "[/#1a3a1a]")

    def log_step(self, step: int, action_type: str, target: str,
                 score: float, delta: float, undone: bool):
        sign = "+" if delta >= 0 else ""
        delta_color = "#00ff88" if delta >= 0 else "#ff4444"
        undo_marker = " [#ff4444 bold]\u21b6 UNDO[/#ff4444 bold]" if undone else ""
        score_color = "#00ff88" if score >= 0.8 else "#ffaa00" if score >= 0.5 else "#ff4444"

        line = (
            f"  [#3a6a3a]#{step:>3}[/#3a6a3a] "
            f"[#1a3a1a]\u2502[/#1a3a1a] "
            f"[#00d4ff]{action_type:<16}[/#00d4ff] "
            f"[#ccddcc]{target:<22}[/#ccddcc] "
            f"[{delta_color}]{sign}{delta:.4f}[/{delta_color}] "
            f"[#1a3a1a]\u2502[/#1a3a1a] "
            f"[{score_color}]{score:.4f}[/{score_color}]"
            f"{undo_marker}"
        )
        self.write(line)

    def log_message(self, msg: str, color: str = "#3a6a3a"):
        self.write(f"  [{color}]{msg}[/{color}]")
