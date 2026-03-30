from server.environment import DataCleaningEnvironment
from models import Action, ActionType


def test_reset_returns_observation():
    env = DataCleaningEnvironment()
    obs = env.reset("fix_dates_and_nulls")
    assert obs.num_rows == 8
    assert obs.done is False
    assert obs.step_number == 0


def test_undo_reverts_last_action():
    env = DataCleaningEnvironment()
    env.reset("fix_dates_and_nulls")
    original_csv = env._current_csv()
    action = Action(action_type=ActionType.DELETE_ROW, row_index=0)
    env.step(action)
    assert env._current_csv() != original_csv
    obs = env.undo()
    assert obs.last_action_message.startswith("Undone")
    assert env._current_csv() == original_csv


def test_undo_empty_stack():
    env = DataCleaningEnvironment()
    env.reset("fix_dates_and_nulls")
    obs = env.undo()
    assert "Nothing to undo" in obs.last_action_message


def test_detect_errors_finds_issues():
    env = DataCleaningEnvironment()
    env.reset("fix_dates_and_nulls")
    hints = env.detect_errors()
    assert len(hints) > 0
    error_types = {h.error_type for h in hints}
    assert "malformed_date" in error_types or "missing_value" in error_types


def test_validate_returns_validation():
    env = DataCleaningEnvironment()
    env.reset("fix_dates_and_nulls")
    result = env.validate()
    assert result.is_valid is False
    assert len(result.errors) > 0


def test_validate_after_cleaning():
    env = DataCleaningEnvironment()
    env.reset("fix_dates_and_nulls")
    action = Action(action_type=ActionType.SUBMIT)
    env.step(action)
    result = env.validate()
    assert result.score >= 0.0


def test_episode_tracking():
    env = DataCleaningEnvironment()
    env.reset("fix_dates_and_nulls")
    env.step(Action(action_type=ActionType.SUBMIT))
    episodes = env.get_episodes()
    assert len(episodes) == 1
    assert episodes[0].task_id == "fix_dates_and_nulls"
    assert episodes[0].final_score >= 0.0


def test_multiple_episodes():
    env = DataCleaningEnvironment()
    env.reset("fix_dates_and_nulls")
    env.step(Action(action_type=ActionType.SUBMIT))
    env.reset("dedup_and_normalize")
    env.step(Action(action_type=ActionType.SUBMIT))
    episodes = env.get_episodes()
    # First reset finalizes no episode (no actions yet), submit finalizes 1,
    # second reset finalizes that episode again (already finalized with actions_log cleared)
    # so we get episodes for both tasks
    assert len(episodes) >= 2
    task_ids = [ep.task_id for ep in episodes]
    assert "fix_dates_and_nulls" in task_ids
    assert "dedup_and_normalize" in task_ids


def test_action_log_tracks_actions():
    env = DataCleaningEnvironment()
    env.reset("fix_dates_and_nulls")
    env.step(Action(action_type=ActionType.FIX_DATE, row_index=1,
                    column_name="signup_date", new_value="2024-01-20"))
    env.step(Action(action_type=ActionType.SUBMIT))
    episodes = env.get_episodes()
    assert len(episodes[0].actions_log) == 2


def test_generated_task_works():
    env = DataCleaningEnvironment()
    obs = env.reset_generated(num_rows=20, difficulty="easy", seed=42)
    assert obs.num_rows >= 20
    assert obs.done is False
