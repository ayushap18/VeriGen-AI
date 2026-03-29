"""
Core environment logic for the Data Cleaning Environment.
Handles reset, step (action processing), and state management.
"""

import csv
import io
import re
from datetime import datetime
from typing import Optional

from models import Action, ActionType, Observation, State
from tasks.task_data import TASKS, parse_csv, rows_to_csv, grade


class DataCleaningEnvironment:
    """
    Environment where an agent cleans messy datasets.
    Supports multiple tasks with increasing difficulty.
    """

    def __init__(self):
        self.task_id: Optional[str] = None
        self.rows: list[dict[str, str]] = []
        self.columns: list[str] = []
        self.column_types: dict[str, str] = {}
        self.clean_csv: str = ""
        self.dirty_csv: str = ""
        self.step_number: int = 0
        self.max_steps: int = 20
        self.done: bool = False
        self.last_action_success: bool = True
        self.last_action_message: str = "Environment ready."

    def reset(self, task_id: str) -> Observation:
        """Reset environment to a specific task."""
        if task_id not in TASKS:
            raise ValueError(f"Unknown task: {task_id}. Available: {list(TASKS.keys())}")

        task = TASKS[task_id]
        self.task_id = task_id
        self.dirty_csv = task["dirty"]
        self.clean_csv = task["clean"]
        self.column_types = task["types"]
        self.max_steps = task["max_steps"]
        self.step_number = 0
        self.done = False
        self.last_action_success = True
        self.last_action_message = f"Task '{task_id}' loaded. Clean the dataset!"

        # Parse dirty data
        self.rows = parse_csv(self.dirty_csv)
        self.columns = list(self.rows[0].keys()) if self.rows else []

        return self._make_observation()

    def step(self, action: Action) -> Observation:
        """Process an agent action and return the new observation."""
        if self.done:
            self.last_action_message = "Episode is done. Call reset() to start a new task."
            return self._make_observation()

        self.step_number += 1

        if self.step_number > self.max_steps:
            self.done = True
            self.last_action_message = "Max steps exceeded. Episode ended."
            return self._make_observation()

        try:
            if action.action_type == ActionType.SUBMIT:
                self.done = True
                score = self._compute_score()
                self.last_action_success = True
                self.last_action_message = f"Submitted! Final score: {score}"

            elif action.action_type == ActionType.DELETE_ROW:
                self._delete_row(action.row_index)

            elif action.action_type == ActionType.FIX_DATE:
                self._fix_date(action.row_index, action.column_name, action.new_value)

            elif action.action_type == ActionType.FILL_MISSING:
                self._fill_missing(action.row_index, action.column_name, action.new_value)

            elif action.action_type == ActionType.REPLACE_VALUE:
                self._replace_value(action.row_index, action.column_name, action.new_value)

            elif action.action_type == ActionType.FIX_TYPE:
                self._fix_type(action.row_index, action.column_name, action.new_value)

            else:
                self.last_action_success = False
                self.last_action_message = f"Unknown action type: {action.action_type}"

        except Exception as e:
            self.last_action_success = False
            self.last_action_message = f"Action failed: {str(e)}"

        return self._make_observation()

    def get_state(self) -> State:
        """Return full serializable state."""
        return State(
            task_id=self.task_id or "",
            dirty_csv=self.dirty_csv,
            current_csv=self._current_csv(),
            clean_csv=self.clean_csv,
            column_types=self.column_types,
            step_number=self.step_number,
            max_steps=self.max_steps,
            done=self.done,
            score=self._compute_score()
        )

    # ---- Action Handlers ----

    def _delete_row(self, row_index: Optional[int]):
        if row_index is None:
            raise ValueError("row_index is required for delete_row")
        if row_index < 0 or row_index >= len(self.rows):
            raise ValueError(f"row_index {row_index} out of range (0-{len(self.rows)-1})")
        self.rows.pop(row_index)
        self.last_action_success = True
        self.last_action_message = f"Deleted row {row_index}. {len(self.rows)} rows remaining."

    def _fix_date(self, row_index: Optional[int], column: Optional[str], new_value: Optional[str]):
        self._validate_cell_args(row_index, column, new_value)
        # Validate date format
        try:
            datetime.strptime(new_value, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: '{new_value}'. Expected YYYY-MM-DD.")
        self.rows[row_index][column] = new_value
        self.last_action_success = True
        self.last_action_message = f"Fixed date at row {row_index}, column '{column}' → '{new_value}'"

    def _fill_missing(self, row_index: Optional[int], column: Optional[str], new_value: Optional[str]):
        self._validate_cell_args(row_index, column, new_value)
        self.rows[row_index][column] = new_value
        self.last_action_success = True
        self.last_action_message = f"Filled missing value at row {row_index}, column '{column}' → '{new_value}'"

    def _replace_value(self, row_index: Optional[int], column: Optional[str], new_value: Optional[str]):
        self._validate_cell_args(row_index, column, new_value)
        old_val = self.rows[row_index][column]
        self.rows[row_index][column] = new_value
        self.last_action_success = True
        self.last_action_message = f"Replaced at row {row_index}, column '{column}': '{old_val}' → '{new_value}'"

    def _fix_type(self, row_index: Optional[int], column: Optional[str], new_value: Optional[str]):
        self._validate_cell_args(row_index, column, new_value)
        self.rows[row_index][column] = new_value
        self.last_action_success = True
        self.last_action_message = f"Fixed type at row {row_index}, column '{column}' → '{new_value}'"

    # ---- Helpers ----

    def _validate_cell_args(self, row_index, column, new_value):
        if row_index is None:
            raise ValueError("row_index is required")
        if column is None:
            raise ValueError("column_name is required")
        if new_value is None:
            raise ValueError("new_value is required")
        if row_index < 0 or row_index >= len(self.rows):
            raise ValueError(f"row_index {row_index} out of range (0-{len(self.rows)-1})")
        if column not in self.columns:
            raise ValueError(f"Unknown column '{column}'. Available: {self.columns}")

    def _current_csv(self) -> str:
        if not self.rows:
            return ""
        return rows_to_csv(self.rows, self.columns)

    def _compute_score(self) -> float:
        return grade(self._current_csv(), self.clean_csv)

    def _make_observation(self) -> Observation:
        return Observation(
            dataset_csv=self._current_csv(),
            num_rows=len(self.rows),
            num_columns=len(self.columns),
            column_names=self.columns,
            column_types=self.column_types,
            step_number=self.step_number,
            max_steps=self.max_steps,
            last_action_success=self.last_action_success,
            last_action_message=self.last_action_message,
            score=self._compute_score(),
            done=self.done
        )
