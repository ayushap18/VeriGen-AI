"""System information panel — Bloomberg terminal style."""

from textual.widgets import Static


class SystemInfo(Static):
    DEFAULT_CSS = """
    SystemInfo {
        height: auto;
        border: solid #1a3a1a;
        background: #050a05;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__("[#00ff88 bold]\u25c9 SYSTEM[/#00ff88 bold]")
        self._data: dict = {}

    def set_info(self, provider: str, model: str, env_url: str):
        self._data = {"provider": provider, "model": model, "env": env_url}
        self._rebuild()

    def update_stats(self, elapsed: float = 0, undos: int = 0,
                     max_undos: int = 5, stalls: int = 0, max_stalls: int = 5):
        self._data.update({
            "elapsed": elapsed, "undos": undos, "max_undos": max_undos,
            "stalls": stalls, "max_stalls": max_stalls
        })
        self._rebuild()

    def _rebuild(self):
        lines = ["[#00ff88 bold]\u25c9 SYSTEM[/#00ff88 bold]"]
        if "provider" in self._data:
            lines.append(f"  [#3a6a3a]Provider:[/#3a6a3a] [#00ff88]{self._data['provider']}[/#00ff88]")
        if "model" in self._data:
            lines.append(f"  [#3a6a3a]Model:[/#3a6a3a]    [#00d4ff]{self._data['model']}[/#00d4ff]")
        if "env" in self._data:
            lines.append(f"  [#3a6a3a]Env:[/#3a6a3a]      [#ccddcc]{self._data['env']}[/#ccddcc]")
        if "elapsed" in self._data:
            m, s = divmod(int(self._data["elapsed"]), 60)
            lines.append(f"  [#3a6a3a]Elapsed:[/#3a6a3a]  [#ffaa00]{m:02d}:{s:02d}[/#ffaa00]")
        if "undos" in self._data:
            u = self._data['undos']
            mu = self._data['max_undos']
            uc = "#00ff88" if u < mu else "#ff4444"
            lines.append(f"  [#3a6a3a]Undos:[/#3a6a3a]    [{uc}]{u}/{mu}[/{uc}]")
        if "stalls" in self._data:
            st = self._data['stalls']
            ms = self._data['max_stalls']
            sc = "#00ff88" if st < ms else "#ff4444"
            lines.append(f"  [#3a6a3a]Stalls:[/#3a6a3a]   [{sc}]{st}/{ms}[/{sc}]")
        self.update("\n".join(lines))
