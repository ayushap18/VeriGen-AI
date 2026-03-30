from models import (
    Action, ActionType, Observation, State,
    HintItem, HintResponse, ValidateResponse,
    EpisodeRecord, ErrorTypeStats, GenerateTaskRequest
)


def test_hint_item_creation():
    hint = HintItem(
        row_index=0, column_name="date", error_type="malformed_date",
        severity="high", description="Date '01/15/2024' is not in YYYY-MM-DD format",
        suggested_action="fix_date"
    )
    assert hint.severity == "high"
    assert hint.suggested_action == "fix_date"


def test_hint_response():
    resp = HintResponse(
        total_errors=2,
        hints=[
            HintItem(row_index=0, column_name="d", error_type="x",
                     severity="high", description="bad", suggested_action="fix_date"),
            HintItem(row_index=1, column_name="e", error_type="y",
                     severity="low", description="meh", suggested_action="fill_missing"),
        ]
    )
    assert resp.total_errors == 2
    assert len(resp.hints) == 2


def test_validate_response():
    resp = ValidateResponse(
        is_valid=False, errors=["Row 2 has null in required column 'name'"],
        score=0.5, error_breakdown={"null_values": 1}
    )
    assert not resp.is_valid
    assert resp.score == 0.5


def test_episode_record():
    rec = EpisodeRecord(
        episode_id="ep_001", task_id="fix_dates_and_nulls",
        steps_taken=5, max_steps=20, final_score=0.85,
        actions_log=[{"action_type": "fix_date", "row_index": 0, "column_name": "date", "new_value": "2024-01-15"}],
        error_type_scores={"date_errors": 1.0, "null_errors": 0.7}
    )
    assert rec.final_score == 0.85
    assert len(rec.actions_log) == 1


def test_generate_task_request_defaults():
    req = GenerateTaskRequest()
    assert req.num_rows == 50
    assert req.difficulty == "medium"
    assert req.seed is None


def test_generate_task_request_custom():
    req = GenerateTaskRequest(num_rows=200, difficulty="hard", seed=42,
                              error_types=["null_values", "malformed_dates"])
    assert req.num_rows == 200
    assert req.seed == 42
    assert len(req.error_types) == 2
