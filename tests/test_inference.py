from inference import extract_json, build_analysis_prompt, prioritize_hints


def test_extract_json_direct():
    result = extract_json('{"action_type": "submit"}')
    assert result["action_type"] == "submit"


def test_extract_json_with_markdown():
    result = extract_json('```json\n{"action_type": "fix_date", "row_index": 0}\n```')
    assert result["action_type"] == "fix_date"
    assert result["row_index"] == 0


def test_extract_json_with_text():
    result = extract_json('I think we should do this: {"action_type": "submit"} and then wait')
    assert result["action_type"] == "submit"


def test_extract_json_fallback():
    result = extract_json("no json here at all")
    assert result["action_type"] == "submit"


def test_build_analysis_prompt():
    obs = {
        "dataset_csv": "a,b\n1,2",
        "column_types": {"a": "integer", "b": "integer"},
        "step_number": 0,
        "max_steps": 20,
        "score": 0.0,
        "last_action_message": "ready",
        "num_rows": 1,
    }
    hints_data = {
        "total_errors": 1,
        "hints": [{"row_index": 0, "column_name": "a", "error_type": "type_error",
                    "severity": "high", "description": "bad", "suggested_action": "fix_type"}]
    }
    prompt = build_analysis_prompt(obs, hints_data)
    assert "a,b" in prompt
    assert "fix_type" in prompt
    assert "Step 0/20" in prompt


def test_prioritize_hints():
    hints = [
        {"severity": "low", "error_type": "x", "row_index": 0, "column_name": "a",
         "description": "minor", "suggested_action": "fix_type"},
        {"severity": "high", "error_type": "y", "row_index": 1, "column_name": "b",
         "description": "critical", "suggested_action": "fix_date"},
        {"severity": "medium", "error_type": "z", "row_index": 2, "column_name": "c",
         "description": "moderate", "suggested_action": "fill_missing"},
    ]
    ordered = prioritize_hints(hints)
    assert ordered[0]["severity"] == "high"
    assert ordered[1]["severity"] == "medium"
    assert ordered[2]["severity"] == "low"
