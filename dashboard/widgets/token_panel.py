"""Token usage and cost panel — Bloomberg style."""

from textual.widgets import Static


class TokenPanel(Static):
    DEFAULT_CSS = """
    TokenPanel {
        height: 7;
        border: solid #1a3a1a;
        background: #050a05;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__(self._build(0, 0, 0.0))

    def _build(self, tin: int, tout: int, cost: float) -> str:
        total = tin + tout
        ratio = tin / max(total, 1) * 20
        bar_in = "[#00d4ff]\u2588[/#00d4ff]" * int(ratio)
        bar_out = "[#ffaa00]\u2588[/#ffaa00]" * (20 - int(ratio))

        return (
            f"[#00ff88 bold]\u25c9 TOKENS[/#00ff88 bold]\n"
            f"[#3a6a3a]  In:[/#3a6a3a]   [#00d4ff]{tin:>10,}[/#00d4ff]\n"
            f"[#3a6a3a]  Out:[/#3a6a3a]  [#ffaa00]{tout:>10,}[/#ffaa00]\n"
            f"  {bar_in}{bar_out}\n"
            f"[#3a6a3a]  Cost:[/#3a6a3a] [#00ff88 bold]${cost:.6f}[/#00ff88 bold]"
        )

    def update_tokens(self, tokens_in: int, tokens_out: int, cost: float):
        self.update(self._build(tokens_in, tokens_out, cost))
