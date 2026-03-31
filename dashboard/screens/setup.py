"""Setup screen — provider, API key, model, and task configuration."""

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
[#00d4ff bold]
██╗   ██╗███████╗██████╗ ██╗ ██████╗ ███████╗███╗   ██╗
██║   ██║██╔════╝██╔══██╗██║██╔════╝ ██╔════╝████╗  ██║
██║   ██║█████╗  ██████╔╝██║██║  ███╗█████╗  ██╔██╗ ██║
╚██╗ ██╔╝██╔══╝  ██╔══██╗██║██║   ██║██╔══╝  ██║╚██╗██║
 ╚████╔╝ ███████╗██║  ██║██║╚██████╔╝███████╗██║ ╚████║
  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝
[/#00d4ff bold]"""


class SetupScreen(Screen):
    CSS = """
    Screen { background: #0a0a0f; }
    #setup-outer { align: center middle; }
    #setup-box {
        width: 76;
        height: auto;
        background: #0f0f1a;
        border: double #00d4ff;
        padding: 1 2;
    }
    #banner { text-align: center; color: #00d4ff; }
    #subtitle { text-align: center; color: #6666aa; margin-bottom: 1; }
    .section-label { color: #00d4ff; text-style: bold; margin-top: 1; }
    #api-key-input { margin: 0 0 1 0; }
    #launch-btn {
        width: 100%;
        margin-top: 1;
    }
    #status-line { color: #6666aa; text-align: center; margin-top: 1; }
    #model-section { margin-top: 1; }
    RadioSet { background: #0a0a0f; border: solid #2a2a4a; }
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
                yield Static("[#6666aa]Data Cleaning Agent v3.0[/#6666aa]", id="subtitle")
                yield Rule()

                yield Static("[#00d4ff bold]PROVIDER[/#00d4ff bold]", classes="section-label")
                with RadioSet(id="provider-select"):
                    for key, p in PROVIDERS.items():
                        yield RadioButton(p["label"], value=(key == self.selected_provider))

                yield Static("[#00d4ff bold]API KEY[/#00d4ff bold]", classes="section-label")
                yield Input(
                    placeholder="Enter your API key...",
                    password=True,
                    value=self.config.api_key,
                    id="api-key-input"
                )

                yield Static("[#00d4ff bold]MODEL[/#00d4ff bold]", classes="section-label")
                with Vertical(id="model-section"):
                    with RadioSet(id="model-select"):
                        models = PROVIDERS.get(self.selected_provider, {}).get("models", [])
                        for i, m in enumerate(models):
                            yield RadioButton(m, value=(i == 0 if not self.selected_model else m == self.selected_model))

                yield Rule()
                yield Button("LAUNCH DASHBOARD", id="launch-btn", variant="primary")
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
                    f"[#6666aa]${pricing['cost_per_1m_in']}/1M in | "
                    f"${pricing['cost_per_1m_out']}/1M out[/#6666aa]"
                )

    def _refresh_models(self):
        model_section = self.query_one("#model-section", Vertical)
        old_radio = self.query_one("#model-select", RadioSet)
        old_radio.remove()

        models = PROVIDERS.get(self.selected_provider, {}).get("models", [])
        radio_set = RadioSet(id="model-select")
        model_section.mount(radio_set)
        for i, m in enumerate(models):
            radio_set.mount(RadioButton(m, value=(i == 0)))
        if models:
            self.selected_model = models[0]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "launch-btn":
            api_key = self.query_one("#api-key-input", Input).value.strip()
            if not api_key:
                status = self.query_one("#status-line", Static)
                status.update("[#ff4444]API key is required![/#ff4444]")
                return

            if not self.selected_model:
                models = PROVIDERS.get(self.selected_provider, {}).get("models", [])
                self.selected_model = models[0] if models else ""

            self.config.provider = self.selected_provider
            self.config.model = self.selected_model
            self.config.api_key = api_key
            save_config(self.config)

            self.app.launch_config = self.config
            self.app.push_screen("run")

    def action_quit(self):
        self.app.exit()
