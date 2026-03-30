"""
Core environment logic for the Data Cleaning Environment.
Handles reset, step, undo, hints, validation, episode tracking, and dynamic generation.
"""

import copy
import csv
import io
import uuid
from datetime import datetime
from typing import Optional

from models import (
    Action, ActionType, Observation, State,
    HintItem, ValidateResponse, EpisodeRecord
)
from tasks.task_data import TASKS, parse_csv, rows_to_csv, grade
from tasks.generator import generate_task


class DataCleaningEnvironment:
    """
    Environment where an agent cleans messy datasets.
    Supports curated tasks, dynamic generation, undo, hints, validation, and episodes.
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
        self._undo_stack: list[tuple] = []
        self._episodes: list[EpisodeRecord] = []
        self._actions_log: list[dict] = []

    def reset(self, task_id: str) -> Observation:
        if task_id not in TASKS:
            raise ValueError(f"Unknown task: {task_id}. Available: {list(TASKS.keys())}")
        self._load_task(task_id, TASKS[task_id])
        return self._make_observation()

    def reset_generated(self, num_rows: int = 50, difficulty: str = "medium",
                        seed: Optional[int] = None,
                        error_types: Optional[list[str]] = None) -> Observation:
        task = generate_task(num_rows=num_rows, difficulty=difficulty,
                             seed=seed, error_types=error_types)
        task_id = f"generated_{difficulty}_{num_rows}r"
        if seed is not None:
            task_id += f"_s{seed}"
        self._load_task(task_id, task)
        return self._make_observation()

    def _load_task(self, task_id: str, task: dict):
        self._finalize_episode()
        self.task_id = task_id
        self.dirty_csv = task["dirty"]
        self.clean_csv = task["clean"]
        self.column_types = task["types"]
        self.max_steps = task["max_steps"]
        self.step_number = 0
        self.done = False
        self.last_action_success = True
        self.last_action_message = f"Task '{task_id}' loaded. Clean the dataset!"
        self._undo_stack = []
        self._actions_log = []
        self.rows = parse_csv(self.dirty_csv)
        self.columns = list(self.rows[0].keys()) if self.rows else []

    def step(self, action: Action) -> Observation:
        if self.done:
            self.last_action_message = "Episode is done. Call reset() to start a new task."
            return self._make_observation()

        self.step_number += 1

        if self.step_number > self.max_steps:
            self.done = True
            self.last_action_message = "Max steps exceeded. Episode ended."
            self._finalize_episode()
            return self._make_observation()

        self._push_undo()

        action_dict = action.model_dump()
        action_dict["action_type"] = (
            action_dict["action_type"].value
            if hasattr(action_dict["action_type"], "value")
            else str(action_dict["action_type"])
        )
        self._actions_log.append(action_dict)

        try:
            if action.action_type == ActionType.SUBMIT:
                self.done = True
                score = self._compute_score()
                self.last_action_success = True
                self.last_action_message = f"Submitted! Final score: {score:.4f}"
                self._finalize_episode()
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

    def undo(self) -> Observation:
        if not self._undo_stack:
            self.last_action_success = False
            self.last_action_message = "Nothing to undo."
            return self._make_observation()
        rows_snapshot, columns, step_number, _ = self._undo_stack.pop()
        self.rows = rows_snapshot
        self.columns = columns
        self.step_number = step_number
        if self._actions_log:
            self._actions_log.pop()
        self.last_action_success = True
        self.last_action_message = "Undone last action."
        self.done = False
        return self._make_observation()

    def detect_errors(self) -> list[HintItem]:
        hints = []
        for i, row in enumerate(self.rows):
            for col, expected_type in self.column_types.items():
                val = row.get(col, "")

                if val.strip() == "":
                    hints.append(HintItem(
                        row_index=i, column_name=col, error_type="missing_value",
                        severity="high",
                        description=f"Missing value at row {i}, column '{col}'",
                        suggested_action="fill_missing"
                    ))
                    continue

                if expected_type == "date_yyyy_mm_dd":
                    try:
                        datetime.strptime(val, "%Y-%m-%d")
                    except ValueError:
                        hints.append(HintItem(
                            row_index=i, column_name=col, error_type="malformed_date",
                            severity="high",
                            description=f"Date '{val}' at row {i} is not YYYY-MM-DD",
                            suggested_action="fix_date"
                        ))

                elif expected_type == "integer":
                    try:
                        v = int(val)
                        if v < 0 and col not in ("id", "order_id", "product_id", "customer_id"):
                            hints.append(HintItem(
                                row_index=i, column_name=col,
                                error_type="negative_value", severity="medium",
                                description=f"Negative value {v} at row {i}, column '{col}'",
                                suggested_action="fix_type"
                            ))
                    except ValueError:
                        hints.append(HintItem(
                            row_index=i, column_name=col, error_type="type_error",
                            severity="high",
                            description=f"Non-integer '{val}' at row {i}, column '{col}'",
                            suggested_action="fix_type"
                        ))

                elif expected_type == "float":
                    try:
                        v = float(val)
                        if v > 50000:
                            hints.append(HintItem(
                                row_index=i, column_name=col,
                                error_type="outlier", severity="medium",
                                description=f"Possible outlier {v} at row {i}, column '{col}'",
                                suggested_action="replace_value"
                            ))
                    except ValueError:
                        hints.append(HintItem(
                            row_index=i, column_name=col, error_type="type_error",
                            severity="high",
                            description=f"Non-numeric '{val}' at row {i}, column '{col}'",
                            suggested_action="fix_type"
                        ))

                elif expected_type == "boolean":
                    if val.lower() not in ("true", "false"):
                        hints.append(HintItem(
                            row_index=i, column_name=col,
                            error_type="invalid_boolean", severity="medium",
                            description=f"Invalid boolean '{val}' at row {i}, column '{col}'",
                            suggested_action="replace_value"
                        ))

        # Check duplicates
        seen = {}
        for i, row in enumerate(self.rows):
            key = str(sorted(row.items()))
            if key in seen:
                hints.append(HintItem(
                    row_index=i, column_name="*", error_type="duplicate_row",
                    severity="high",
                    description=f"Row {i} is a duplicate of row {seen[key]}",
                    suggested_action="delete_row"
                ))
            else:
                seen[key] = i

        # Check computed columns
        if all(c in self.column_types for c in ("total", "quantity", "unit_price")):
            for i, row in enumerate(self.rows):
                try:
                    qty = float(row.get("quantity", "0"))
                    price = float(row.get("unit_price", "0"))
                    total = float(row.get("total", "0"))
                    expected = round(qty * price, 2)
                    if abs(total - expected) > 0.01:
                        hints.append(HintItem(
                            row_index=i, column_name="total",
                            error_type="wrong_computed", severity="high",
                            description=f"Total {total} != {qty}*{price}={expected} at row {i}",
                            suggested_action="replace_value"
                        ))
                except (ValueError, KeyError):
                    pass

        return hints

    def validate(self) -> ValidateResponse:
        hints = self.detect_errors()
        error_breakdown: dict[str, int] = {}
        error_messages = []
        for h in hints:
            error_breakdown[h.error_type] = error_breakdown.get(h.error_type, 0) + 1
            error_messages.append(h.description)
        return ValidateResponse(
            is_valid=len(hints) == 0,
            errors=error_messages,
            score=self._compute_score(),
            error_breakdown=error_breakdown
        )

    def get_episodes(self) -> list[EpisodeRecord]:
        return list(self._episodes)

    def get_state(self) -> State:
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

    def _push_undo(self):
        self._undo_stack.append((
            copy.deepcopy(self.rows), list(self.columns),
            self.step_number - 1, self.last_action_message,
        ))
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)

    def _finalize_episode(self):
        if self.task_id and self._actions_log:
            self._episodes.append(EpisodeRecord(
                episode_id=f"ep_{uuid.uuid4().hex[:8]}",
                task_id=self.task_id,
                steps_taken=self.step_number,
                max_steps=self.max_steps,
                final_score=self._compute_score(),
                actions_log=list(self._actions_log),
                error_type_scores={}
            ))

    def _delete_row(self, row_index: Optional[int]):
        if row_index is None:
            raise ValueError("row_index is required for delete_row")
        if row_index < 0 or row_index >= len(self.rows):
            raise ValueError(f"row_index {row_index} out of range (0-{len(self.rows)-1})")
        self.rows.pop(row_index)
        self.last_action_success = True
        self.last_action_message = f"Deleted row {row_index}. {len(self.rows)} rows remaining."

    def _fix_date(self, row_index, column, new_value):
        self._validate_cell_args(row_index, column, new_value)
        try:
            datetime.strptime(new_value, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: '{new_value}'. Expected YYYY-MM-DD.")
        self.rows[row_index][column] = new_value
        self.last_action_success = True
        self.last_action_message = f"Fixed date at row {row_index}, column '{column}' -> '{new_value}'"

    def _fill_missing(self, row_index, column, new_value):
        self._validate_cell_args(row_index, column, new_value)
        self.rows[row_index][column] = new_value
        self.last_action_success = True
        self.last_action_message = f"Filled missing at row {row_index}, column '{column}' -> '{new_value}'"

    def _replace_value(self, row_index, column, new_value):
        self._validate_cell_args(row_index, column, new_value)
        old_val = self.rows[row_index][column]
        self.rows[row_index][column] = new_value
        self.last_action_success = True
        self.last_action_message = f"Replaced at row {row_index}, column '{column}': '{old_val}' -> '{new_value}'"

    def _fix_type(self, row_index, column, new_value):
        self._validate_cell_args(row_index, column, new_value)
        self.rows[row_index][column] = new_value
        self.last_action_success = True
        self.last_action_message = f"Fixed type at row {row_index}, column '{column}' -> '{new_value}'"

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
        current = self._current_csv()
        if not current or not self.clean_csv:
            return 0.0
        return grade(current, self.clean_csv)

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
