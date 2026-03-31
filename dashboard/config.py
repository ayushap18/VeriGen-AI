"""Config persistence for VeriGen-AI dashboard."""

import json
import os
from dataclasses import dataclass, field

CONFIG_DIR = os.path.expanduser("~/.verigen")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
MAX_HISTORY = 20


@dataclass
class VeriGenConfig:
    provider: str = ""
    model: str = ""
    api_key: str = ""
    env_url: str = "http://localhost:7860"
    difficulty: str = "medium"
    generated_rows: int = 30
    run_history: list = field(default_factory=list)

    def add_run(self, run_data: dict):
        self.run_history.append(run_data)
        if len(self.run_history) > MAX_HISTORY:
            self.run_history = self.run_history[-MAX_HISTORY:]


def save_config(config: VeriGenConfig, path: str = CONFIG_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "provider": config.provider,
        "model": config.model,
        "api_key": config.api_key,
        "env_url": config.env_url,
        "difficulty": config.difficulty,
        "generated_rows": config.generated_rows,
        "run_history": config.run_history,
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_config(path: str = CONFIG_PATH) -> VeriGenConfig:
    if not os.path.exists(path):
        return VeriGenConfig()
    try:
        with open(path) as f:
            data = json.load(f)
        return VeriGenConfig(**{k: v for k, v in data.items()
                                if k in VeriGenConfig.__dataclass_fields__})
    except (json.JSONDecodeError, TypeError):
        return VeriGenConfig()
