"""
Client SDK for interacting with the Data Cleaning Environment server.
Provides methods for all endpoints including hints, validation, undo, episodes, and generation.
"""

import requests
from typing import Optional
from models import Observation, State, HintResponse, ValidateResponse, EpisodeRecord


class DataCleaningClient:
    """HTTP client for the Data Cleaning Environment."""

    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url.rstrip("/")

    def health(self) -> dict:
        resp = requests.get(f"{self.base_url}/health")
        resp.raise_for_status()
        return resp.json()

    def reset(self, task_id: str = "fix_dates_and_nulls") -> Observation:
        resp = requests.post(f"{self.base_url}/reset", json={"task_id": task_id})
        resp.raise_for_status()
        return Observation(**resp.json())

    def step(self, action_type: str, row_index: Optional[int] = None,
             column_name: Optional[str] = None,
             new_value: Optional[str] = None) -> Observation:
        payload = {"action_type": action_type}
        if row_index is not None:
            payload["row_index"] = row_index
        if column_name is not None:
            payload["column_name"] = column_name
        if new_value is not None:
            payload["new_value"] = new_value
        resp = requests.post(f"{self.base_url}/step", json=payload)
        resp.raise_for_status()
        return Observation(**resp.json())

    def get_state(self) -> State:
        resp = requests.get(f"{self.base_url}/state")
        resp.raise_for_status()
        return State(**resp.json())

    def list_tasks(self) -> dict:
        resp = requests.get(f"{self.base_url}/tasks")
        resp.raise_for_status()
        return resp.json()

    def hints(self) -> HintResponse:
        resp = requests.get(f"{self.base_url}/hints")
        resp.raise_for_status()
        return HintResponse(**resp.json())

    def validate(self) -> ValidateResponse:
        resp = requests.get(f"{self.base_url}/validate")
        resp.raise_for_status()
        return ValidateResponse(**resp.json())

    def undo(self) -> Observation:
        resp = requests.post(f"{self.base_url}/undo")
        resp.raise_for_status()
        return Observation(**resp.json())

    def episodes(self) -> list[EpisodeRecord]:
        resp = requests.get(f"{self.base_url}/episodes")
        resp.raise_for_status()
        return [EpisodeRecord(**ep) for ep in resp.json()]

    def generate(self, num_rows: int = 50, difficulty: str = "medium",
                 seed: Optional[int] = None,
                 error_types: Optional[list[str]] = None) -> Observation:
        payload = {"num_rows": num_rows, "difficulty": difficulty}
        if seed is not None:
            payload["seed"] = seed
        if error_types is not None:
            payload["error_types"] = error_types
        resp = requests.post(f"{self.base_url}/generate", json=payload)
        resp.raise_for_status()
        return Observation(**resp.json())
