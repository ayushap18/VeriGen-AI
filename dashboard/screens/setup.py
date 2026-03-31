"""Setup screen — Bloomberg terminal style with CSV file support."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import (
    Static, Input, Button, RadioSet, RadioButton, Rule, Footer
)
from textual.binding import Binding

from dashboard.providers import PROVIDERS, get_pricing
from dashboard.config import VeriGenConfig, load_config, save_config


BANNER = """\
[#00ff88 bold]
██╗   ██╗███████╗██████╗ ██╗ ██████╗ ███████╗███╗   ██╗
██║   ██║██╔════╝██╔══██╗██║██╔════╝ ██╔════╝████╗  ██║
██║   ██║█████╗  ██████╔╝██║██║  ███╗█████╗  ██╔██╗ ██║
╚██╗ ██╔╝██╔══╝  ██╔══██╗██║██║   ██║██╔══╝  ██║╚██╗██║
 ╚████╔╝ ███████╗██║  ██║██║╚██████╔╝███████╗██║ ╚████║
  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝
[/#00ff88 bold]"""


class SetupScreen(Screen):
    CSS = """
    Screen { background: #020502; }
    #setup-outer { align: center middle; }
    #setup-box {
        width: 80;
        height: auto;
        background: #050a05;
        border: double #00ff88;
        padding: 1 2;
    }
    #banner { text-align: center; color: #00ff88; }
    #subtitle { text-align: center; color: #3a6a3a; margin-bottom: 1; }
    .section-label { color: #00ff88; text-style: bold; margin-top: 1; }
    Input {
        margin: 0 0 1 0;
        border: solid #1a3a1a;
        background: #0a1a0a;
        color: #00ff88;
    }
    #launch-btn {
        width: 100%;
        margin-top: 1;
        background: #0a2a0a;
        color: #00ff88;
        border: solid #00ff88;
    }
    #launch-btn:hover { background: #1a4a1a; }
    #status-line { color: #3a6a3a; text-align: center; margin-top: 1; }
    #model-section { margin-top: 1; }
    #csv-hint { color: #3a6a3a; margin: 0 0 1 0; }
    RadioSet { background: #0a1a0a; border: solid #1a3a1a; }
    RadioButton { color: #00ff88; }
    Rule { color: #1a3a1a; }
    """

    BINDINGS = [
        Binding("escape", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.selected_provider = self.config.provider or "gemini"
        self.selected_model = self.config.model or ""

    def compose(self) -> ComposeResult:
        with Vertical(id="setup-outer"):
            with Vertical(id="setup-box"):
                yield Static(BANNER, id="banner")
                yield Static(
                    "[#3a6a3a]Data Cleaning Agent Terminal v3.0[/#3a6a3a]\n"
                    "[#1a3a1a]\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501[/#1a3a1a]",
                    id="subtitle"
                )

                yield Static("[#00ff88 bold]\u25b8 PROVIDER[/#00ff88 bold]", classes="section-label")
                with RadioSet(id="provider-select"):
                    for key, p in PROVIDERS.items():
                        yield RadioButton(p["label"], value=(key == self.selected_provider))

                yield Static("[#00ff88 bold]\u25b8 API KEY[/#00ff88 bold]", classes="section-label")
                yield Input(
                    placeholder="Enter your API key...",
                    password=True,
                    value=self.config.api_key,
                    id="api-key-input"
                )

                yield Static("[#00ff88 bold]\u25b8 MODEL[/#00ff88 bold]", classes="section-label")
                with Vertical(id="model-section"):
                    with RadioSet(id="model-select"):
                        models = PROVIDERS.get(self.selected_provider, {}).get("models", [])
                        for i, m in enumerate(models):
                            yield RadioButton(m, value=(i == 0 if not self.selected_model else m == self.selected_model))

                yield Static("[#00ff88 bold]\u25b8 CSV FILE (optional)[/#00ff88 bold]", classes="section-label")
                yield Static(
                    "[#3a6a3a]Provide path to your own CSV file, or leave blank for built-in tasks[/#3a6a3a]",
                    id="csv-hint"
                )
                yield Input(
                    placeholder="/path/to/your/data.csv",
                    value=self.config.csv_path,
                    id="csv-path-input"
                )

                yield Rule()
                yield Button(
                    "\u25b6  INITIALIZE TERMINAL",
                    id="launch-btn", variant="success"
                )
                yield Static("", id="status-line")

        yield Footer()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id == "provider-select":
            idx = event.index
            provider_keys = list(PROVIDERS.keys())
            if 0 <= idx < len(provider_keys):
                self.selected_provider = provider_keys[idx]
                self._refresh_models()
        elif event.radio_set.id == "model-select":
            models = PROVIDERS.get(self.selected_provider, {}).get("models", [])
            if 0 <= event.index < len(models):
                self.selected_model = models[event.index]
                pricing = get_pricing(self.selected_provider, self.selected_model)
                status = self.query_one("#status-line", Static)
                status.update(
                    f"[#3a6a3a]${pricing['cost_per_1m_in']}/1M in | "
                    f"${pricing['cost_per_1m_out']}/1M out[/#3a6a3a]"
                )

    async def _refresh_models(self):
        old_radio = self.query_one("#model-select", RadioSet)
        await old_radio.remove()

        model_section = self.query_one("#model-section", Vertical)
        models = PROVIDERS.get(self.selected_provider, {}).get("models", [])
        radio_set = RadioSet(id="model-select")
        await model_section.mount(radio_set)
        for i, m in enumerate(models):
            await radio_set.mount(RadioButton(m, value=(i == 0)))
        if models:
            self.selected_model = models[0]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "launch-btn":
            api_key = self.query_one("#api-key-input", Input).value.strip()
            if not api_key:
                self.query_one("#status-line", Static).update(
                    "[#ff4444]\u26a0 API key is required![/#ff4444]"
                )
                return

            csv_path = self.query_one("#csv-path-input", Input).value.strip()
            if csv_path:
                import os
                if not os.path.exists(csv_path):
                    self.query_one("#status-line", Static).update(
                        f"[#ff4444]\u26a0 File not found: {csv_path}[/#ff4444]"
                    )
                    return
                if not csv_path.endswith(".csv"):
                    self.query_one("#status-line", Static).update(
                        "[#ff4444]\u26a0 File must be a .csv file[/#ff4444]"
                    )
                    return

            if not self.selected_model:
                models = PROVIDERS.get(self.selected_provider, {}).get("models", [])
                self.selected_model = models[0] if models else ""

            self.config.provider = self.selected_provider
            self.config.model = self.selected_model
            self.config.api_key = api_key
            self.config.csv_path = csv_path
            save_config(self.config)

            self.app.launch_config = self.config
            self.app.push_screen("run")

    def action_quit(self):
        self.app.exit()
