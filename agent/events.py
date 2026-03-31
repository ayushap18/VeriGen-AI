"""Event dataclasses emitted by the agent during execution."""

from dataclasses import dataclass, field


@dataclass
class StepResult:
    task_id: str
    step: int
    action_type: str
    target: str          # e.g. "r1:signup_date" or ""
    new_value: str       # the value set, or ""
    score: float
    delta: float
    undone: bool
    tokens_in: int = 0
    tokens_out: int = 0


@dataclass
class TaskStart:
    task_id: str
    num_rows: int
    num_columns: int
    column_types: dict
    max_steps: int
    task_index: int      # 0-based
    total_tasks: int


@dataclass
class TaskEnd:
    task_id: str
    final_score: float
    steps_taken: int
    remaining_errors: dict
    task_index: int
    total_tasks: int


@dataclass
class RunComplete:
    scores: dict
    average: float
    total_tokens_in: int
    total_tokens_out: int
    total_cost: float
    elapsed_seconds: float
    task_details: list = field(default_factory=list)
