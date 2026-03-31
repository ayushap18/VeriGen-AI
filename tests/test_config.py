import os
from dashboard.config import VeriGenConfig, load_config, save_config


def test_default_config():
    c = VeriGenConfig()
    assert c.provider == ""
    assert c.model == ""
    assert c.api_key == ""


def test_save_and_load(tmp_path):
    path = tmp_path / "config.json"
    c = VeriGenConfig(provider="gemini", model="gemini-2.5-flash", api_key="AIzaTest123")
    save_config(c, str(path))
    loaded = load_config(str(path))
    assert loaded.provider == "gemini"
    assert loaded.model == "gemini-2.5-flash"
    assert loaded.api_key == "AIzaTest123"


def test_load_missing_file(tmp_path):
    path = tmp_path / "nonexistent.json"
    c = load_config(str(path))
    assert c.provider == ""


def test_save_creates_directory(tmp_path):
    path = tmp_path / "subdir" / "config.json"
    c = VeriGenConfig(provider="openai", model="gpt-4o-mini")
    save_config(c, str(path))
    assert os.path.exists(str(path))


def test_run_history(tmp_path):
    path = tmp_path / "config.json"
    c = VeriGenConfig(provider="gemini", model="gemini-2.5-flash")
    c.add_run({"scores": {"a": 1.0}, "average": 1.0, "model": "gemini-2.5-flash",
               "cost": 0.004, "elapsed": 67.0, "date": "2026-03-31"})
    save_config(c, str(path))
    loaded = load_config(str(path))
    assert len(loaded.run_history) == 1
    assert loaded.run_history[0]["average"] == 1.0


def test_run_history_max_20(tmp_path):
    path = tmp_path / "config.json"
    c = VeriGenConfig()
    for i in range(25):
        c.add_run({"average": i / 25})
    save_config(c, str(path))
    loaded = load_config(str(path))
    assert len(loaded.run_history) == 20
