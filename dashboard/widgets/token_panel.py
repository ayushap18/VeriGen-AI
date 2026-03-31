"""Token usage and cost panel."""

from textual.app import ComposeResult
from textual.widgets import Static


class TokenPanel(Static):
    DEFAULT_CSS = """
    TokenPanel {
        height: 5;
        border: solid #2a2a4a;
        background: #0f0f1a;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("[#6666aa]TOKENS[/#6666aa]", id="tok-label")
        yield Static("[#00d4ff]In: 0[/#00d4ff]  [#ffaa00]Out: 0[/#ffaa00]", id="tok-in")
        yield Static("[#00ff88]Cost: $0.0000[/#00ff88]", id="tok-cost")

    def update_tokens(self, tokens_in: int, tokens_out: int, cost: float):
        self.query_one("#tok-in", Static).update(
            f"[#00d4ff]In: {tokens_in:,}[/#00d4ff]  "
            f"[#ffaa00]Out: {tokens_out:,}[/#ffaa00]"
        )
        self.query_one("#tok-cost", Static).update(
            f"[#00ff88]Cost: ${cost:.4f}[/#00ff88]"
        )
