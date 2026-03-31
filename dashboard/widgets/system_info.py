"""System information panel."""

from textual.app import ComposeResult
from textual.widgets import Static


class SystemInfo(Static):
    DEFAULT_CSS = """
    SystemInfo {
        height: auto;
        border: solid #2a2a4a;
        background: #0f0f1a;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self._data: dict = {}

    def compose(self) -> ComposeResult:
        yield Static("[#6666aa]SYSTEM[/#6666aa]", id="si-label")
        yield Static("", id="si-content")

    def set_info(self, provider: str, model: str, env_url: str):
        self._data = {"provider": provider, "model": model, "env": env_url}
        self._render()

    def update_stats(self, elapsed: float = 0, undos: int = 0,
                     max_undos: int = 5, stalls: int = 0, max_stalls: int = 5):
        self._data.update({
            "elapsed": elapsed, "undos": undos, "max_undos": max_undos,
            "stalls": stalls, "max_stalls": max_stalls
        })
        self._render()

    def _render(self):
        lines = []
        if "provider" in self._data:
            lines.append(f"  [#6666aa]Provider:[/#6666aa] [#ccccdd]{self._data['provider']}[/#ccccdd]")
        if "model" in self._data:
            lines.append(f"  [#6666aa]Model:[/#6666aa]    [#ccccdd]{self._data['model']}[/#ccccdd]")
        if "env" in self._data:
            lines.append(f"  [#6666aa]Env:[/#6666aa]      [#ccccdd]{self._data['env']}[/#ccccdd]")
        if "elapsed" in self._data:
            m, s = divmod(int(self._data["elapsed"]), 60)
            lines.append(f"  [#6666aa]Elapsed:[/#6666aa]  [#ccccdd]{m}m{s:02d}s[/#ccccdd]")
        if "undos" in self._data:
            lines.append(f"  [#6666aa]Undos:[/#6666aa]    [#ccccdd]{self._data['undos']}/{self._data['max_undos']}[/#ccccdd]")
        if "stalls" in self._data:
            lines.append(f"  [#6666aa]Stalls:[/#6666aa]   [#ccccdd]{self._data['stalls']}/{self._data['max_stalls']}[/#ccccdd]")
        self.query_one("#si-content", Static).update("\n".join(lines))
