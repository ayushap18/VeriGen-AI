"""
Client for interacting with the Data Cleaning Environment server.
Used by agents and the inference script to communicate with the environment.
"""

import requests
from typing import Optional
from models import Observation, State


class DataCleaningClient:
    """HTTP client for the Data Cleaning Environment."""

    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url.rstrip("/")

    def health_check(self) -> dict:
        """Check if the environment is running."""
        resp = requests.get(f"{self.base_url}/")
        resp.raise_for_status()
        return resp.json()

    def reset(self, task_id: str) -> Observation:
        """Reset environment to a task."""
        resp = requests.post(
            f"{self.base_url}/reset",
            json={"task_id": task_id}
        )
        resp.raise_for_status()
        return Observation(**resp.json())

    def step(
        self,
        action_type: str,
        row_index: Optional[int] = None,
        column_name: Optional[str] = None,
        new_value: Optional[str] = None
    ) -> Observation:
        """Take an action in the environment."""
        payload = {"action_type": action_type}
        if row_index is not None:
            payload["row_index"] = row_index
        if column_name is not None:
            payload["column_name"] = column_name
        if new_value is not None:
            payload["new_value"] = new_value

        resp = requests.post(
            f"{self.base_url}/step",
            json=payload
        )
        resp.raise_for_status()
        return Observation(**resp.json())

    def get_state(self) -> State:
        """Get current state."""
        resp = requests.get(f"{self.base_url}/state")
        resp.raise_for_status()
        return State(**resp.json())

    def list_tasks(self) -> dict:
        """List available tasks."""
        resp = requests.get(f"{self.base_url}/tasks")
        resp.raise_for_status()
        return resp.json()
