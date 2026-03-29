"""
Typed Pydantic models for the Data Cleaning Environment.
These define the contract between the agent and the environment.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ActionType(str, Enum):
    """Types of cleaning actions the agent can perform."""
    FIX_DATE = "fix_date"              # Fix a malformed date in a cell
    FILL_MISSING = "fill_missing"      # Fill a missing/null value
    DELETE_ROW = "delete_row"          # Remove a duplicate or invalid row
    REPLACE_VALUE = "replace_value"    # Replace an incorrect value
    FIX_TYPE = "fix_type"              # Cast a value to the correct type
    SUBMIT = "submit"                  # Submit the cleaned dataset as final answer


class Action(BaseModel):
    """An action the agent takes to clean the data."""
    action_type: ActionType = Field(description="The type of cleaning operation")
    row_index: Optional[int] = Field(default=None, description="Row index to operate on (0-based)")
    column_name: Optional[str] = Field(default=None, description="Column name to operate on")
    new_value: Optional[str] = Field(default=None, description="The corrected value to set")


class CellError(BaseModel):
    """Describes a single error in the dataset."""
    row_index: int
    column_name: str
    error_type: str
    current_value: Optional[str] = None


class Observation(BaseModel):
    """What the agent sees after each action."""
    dataset_csv: str = Field(description="Current state of the dataset as CSV string")
    num_rows: int = Field(description="Number of rows in the current dataset")
    num_columns: int = Field(description="Number of columns")
    column_names: list[str] = Field(description="List of column names")
    column_types: dict[str, str] = Field(description="Expected types for each column")
    step_number: int = Field(description="Current step number")
    max_steps: int = Field(description="Maximum allowed steps")
    last_action_success: bool = Field(default=True, description="Whether last action succeeded")
    last_action_message: str = Field(default="", description="Feedback message from last action")
    score: float = Field(default=0.0, description="Current score (0.0 - 1.0)")
    done: bool = Field(default=False, description="Whether the episode is finished")


class State(BaseModel):
    """Full environment state for save/restore."""
    task_id: str
    dirty_csv: str
    current_csv: str
    clean_csv: str  # ground truth
    column_types: dict[str, str]
    step_number: int
    max_steps: int
    done: bool
    score: float
