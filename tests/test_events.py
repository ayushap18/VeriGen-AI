from agent.events import StepResult, TaskStart, TaskEnd, RunComplete


def test_step_result_creation():
    e = StepResult(
        task_id="fix_dates", step=1, action_type="fix_date",
        target="r1:signup_date", new_value="2024-03-15",
        score=0.73, delta=0.04, undone=False
    )
    assert e.task_id == "fix_dates"
    assert e.delta == 0.04
    assert e.undone is False


def test_step_result_undone():
    e = StepResult(
        task_id="fix_dates", step=2, action_type="fix_date",
        target="r3:name", new_value="Bob",
        score=0.70, delta=-0.03, undone=True
    )
    assert e.undone is True


def test_task_start():
    e = TaskStart(task_id="dedup", num_rows=12, num_columns=5,
                  column_types={"id": "integer"}, max_steps=25, task_index=1, total_tasks=4)
    assert e.task_index == 1


def test_task_end():
    e = TaskEnd(task_id="dedup", final_score=0.636, steps_taken=3,
                remaining_errors={"invalid_boolean": 1}, task_index=1, total_tasks=4)
    assert e.final_score == 0.636


def test_run_complete():
    e = RunComplete(scores={"a": 1.0, "b": 0.5}, average=0.75,
                    total_tokens_in=1000, total_tokens_out=200, total_cost=0.004,
                    elapsed_seconds=67.0)
    assert e.average == 0.75
    assert e.total_cost == 0.004
