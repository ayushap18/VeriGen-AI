"""Agent chat panel — see what the AI is thinking and interact with it."""

from textual.widgets import RichLog


class AgentChat(RichLog):
    DEFAULT_CSS = """
    AgentChat {
        height: 100%;
        border: solid #1a3a1a;
        background: #050a05;
        scrollbar-color: #1a3a1a;
        scrollbar-color-hover: #2a5a2a;
    }
    """

    def __init__(self):
        super().__init__(highlight=True, markup=True, wrap=True, max_lines=500)

    def on_mount(self):
        self.write("[#00ff88 bold]\u25c9 AGENT NEURAL LINK[/#00ff88 bold]")
        self.write("[#1a3a1a]" + "\u2500" * 40 + "[/#1a3a1a]")
        self.write("[#3a6a3a]Connecting to AI agent...[/#3a6a3a]")
        self.write("")

    def log_thinking(self, task_id: str, step: int, action: str, target: str,
                     new_value: str = ""):
        self.write(f"[#ffaa00]\u25b6 Step {step}[/#ffaa00]")
        self.write(f"  [#3a6a3a]Task:[/#3a6a3a]   [#ccddcc]{task_id}[/#ccddcc]")
        self.write(f"  [#3a6a3a]Action:[/#3a6a3a] [#00ff88]{action}[/#00ff88]")
        if target:
            self.write(f"  [#3a6a3a]Target:[/#3a6a3a] [#00d4ff]{target}[/#00d4ff]")
        if new_value:
            self.write(f"  [#3a6a3a]Value:[/#3a6a3a]  [#ccddcc]{new_value}[/#ccddcc]")

    def log_decision(self, msg: str):
        self.write(f"  [#6a6aaa]{msg}[/#6a6aaa]")

    def log_task_start(self, task_id: str, rows: int, cols: int, types: dict):
        self.write("")
        self.write(f"[#00ff88 bold]\u250c{'─' * 40}\u2510[/#00ff88 bold]")
        self.write(f"[#00ff88 bold]\u2502 NEW TASK: {task_id:<29}\u2502[/#00ff88 bold]")
        self.write(f"[#00ff88 bold]\u2502 Rows: {rows}  Cols: {cols:<24}\u2502[/#00ff88 bold]")
        self.write(f"[#00ff88 bold]\u2514{'─' * 40}\u2518[/#00ff88 bold]")
        self.write(f"  [#3a6a3a]Columns:[/#3a6a3a]")
        for col, ctype in types.items():
            self.write(f"    [#00d4ff]{col}[/#00d4ff] [#3a6a3a]({ctype})[/#3a6a3a]")
        self.write("")

    def log_score_change(self, score: float, delta: float):
        color = "#00ff88" if delta >= 0 else "#ff4444"
        sign = "+" if delta >= 0 else ""
        self.write(f"  [{color}]Score: {score:.4f} ({sign}{delta:.4f})[/{color}]")
        self.write("")

    def log_error(self, msg: str):
        self.write(f"  [#ff4444]\u26a0 {msg}[/#ff4444]")

    def log_success(self, msg: str):
        self.write(f"  [#00ff88]\u2713 {msg}[/#00ff88]")

    def log_user_msg(self, msg: str):
        self.write(f"[#00d4ff bold]YOU:[/#00d4ff bold] {msg}")

    def log_agent_reply(self, msg: str):
        self.write(f"[#00ff88 bold]AGENT:[/#00ff88 bold] {msg}")
