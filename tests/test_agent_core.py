from agent.core import AgentConfig, build_action_target, extract_json, clean_action


def test_agent_config_defaults():
    c = AgentConfig(api_key="test", base_url="http://test", model="test-model",
                    env_url="http://localhost:7860")
    assert c.max_undos == 5
    assert c.max_stalls == 5
    assert c.curated_tasks == ["fix_dates_and_nulls", "dedup_and_normalize", "full_pipeline_clean"]


def test_build_action_target_with_row_and_col():
    action = {"action_type": "fix_date", "row_index": 1, "column_name": "date"}
    assert build_action_target(action) == "r1:date"


def test_build_action_target_row_only():
    action = {"action_type": "delete_row", "row_index": 3}
    assert build_action_target(action) == "r3"


def test_build_action_target_submit():
    action = {"action_type": "submit"}
    assert build_action_target(action) == ""


def test_build_action_target_no_row():
    action = {"action_type": "submit", "row_index": None}
    assert build_action_target(action) == ""


def test_extract_json_direct():
    result = extract_json('{"action_type": "submit"}')
    assert result["action_type"] == "submit"


def test_extract_json_markdown():
    result = extract_json('```json\n{"action_type": "fix_date", "row_index": 0}\n```')
    assert result["action_type"] == "fix_date"


def test_extract_json_fallback():
    result = extract_json("no json here")
    assert result["action_type"] == "submit"


def test_clean_action_strips_extras():
    action = {"action_type": "fix_date", "row_index": 1, "column_name": "date",
              "new_value": "2024-01-01", "reasoning": "because it was wrong"}
    cleaned = clean_action(action)
    assert "reasoning" not in cleaned
    assert cleaned["action_type"] == "fix_date"
    assert cleaned["row_index"] == 1
