"""Stock market-style scrolling ticker — live stats with trend arrows."""

import random
from textual.widgets import Static


class TickerBar(Static):
    DEFAULT_CSS = """
    TickerBar {
        dock: bottom;
        height: 1;
        background: #0a1a0a;
        color: #00ff88;
        text-style: bold;
        border-top: solid #1a3a1a;
    }
    """

    def __init__(self):
        super().__init__("")
        self._items: list[str] = []
        self._offset = 0
        self._prev_values: dict[str, float] = {}

    def set_items(self, items: list[str]):
        self._items = items
        self._render_ticker()

    def scroll_tick(self):
        text = self._build_text()
        if text:
            self._offset = (self._offset + 2) % len(text)
        self._render_ticker()

    def _build_text(self) -> str:
        if not self._items:
            return ""
        sep = "  \u2503  "
        return sep.join(self._items) + sep

    def _render_ticker(self):
        full = self._build_text()
        if not full:
            self.update(
                "[#00ff88 bold] \u25b2 VERIGEN-AI [/#00ff88 bold]"
                "[#1a3a1a]\u2503[/#1a3a1a]"
                "[#00d4ff] SYSTEM ONLINE [/#00d4ff]"
                "[#1a3a1a]\u2503[/#1a3a1a]"
                "[#00ff88] AWAITING DATA [/#00ff88]"
            )
            return
        doubled = full + full
        visible = doubled[self._offset:self._offset + 200]
        self.update(f"[#00ff88 bold]{visible}[/#00ff88 bold]")
