from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data
    assert "version" in data
    assert "endpoints" in data


def test_root_endpoint():
    r = client.get("/")
    assert r.status_code == 200
    assert "available_tasks" in r.json()


def test_reset_empty_body():
    r = client.post("/reset")
    assert r.status_code == 200
    assert r.json()["done"] is False


def test_reset_with_task_id():
    r = client.post("/reset", json={"task_id": "fix_dates_and_nulls"})
    assert r.status_code == 200
    assert r.json()["num_rows"] == 8


def test_reset_invalid_task():
    r = client.post("/reset", json={"task_id": "nonexistent"})
    assert r.status_code == 400


def test_step_fix_date():
    client.post("/reset", json={"task_id": "fix_dates_and_nulls"})
    r = client.post("/step", json={
        "action_type": "fix_date", "row_index": 1,
        "column_name": "signup_date", "new_value": "2024-01-20"
    })
    assert r.status_code == 200
    assert r.json()["last_action_success"] is True


def test_step_submit():
    client.post("/reset", json={"task_id": "fix_dates_and_nulls"})
    r = client.post("/step", json={"action_type": "submit"})
    assert r.status_code == 200
    assert r.json()["done"] is True


def test_state_endpoint():
    client.post("/reset", json={"task_id": "fix_dates_and_nulls"})
    r = client.get("/state")
    assert r.status_code == 200
    assert r.json()["task_id"] == "fix_dates_and_nulls"


def test_tasks_endpoint():
    r = client.get("/tasks")
    assert r.status_code == 200
    data = r.json()
    assert "fix_dates_and_nulls" in data
    assert "dedup_and_normalize" in data
    assert "full_pipeline_clean" in data


def test_hints_endpoint():
    client.post("/reset", json={"task_id": "fix_dates_and_nulls"})
    r = client.get("/hints")
    assert r.status_code == 200
    data = r.json()
    assert "total_errors" in data
    assert "hints" in data
    assert data["total_errors"] > 0


def test_validate_endpoint():
    client.post("/reset", json={"task_id": "fix_dates_and_nulls"})
    r = client.get("/validate")
    assert r.status_code == 200
    data = r.json()
    assert "is_valid" in data
    assert "errors" in data
    assert "score" in data
    assert "error_breakdown" in data


def test_undo_endpoint():
    client.post("/reset", json={"task_id": "fix_dates_and_nulls"})
    client.post("/step", json={"action_type": "delete_row", "row_index": 0})
    r = client.post("/undo")
    assert r.status_code == 200
    assert "Undone" in r.json()["last_action_message"]


def test_undo_empty_stack():
    client.post("/reset", json={"task_id": "fix_dates_and_nulls"})
    r = client.post("/undo")
    assert r.status_code == 200
    assert "Nothing to undo" in r.json()["last_action_message"]


def test_episodes_endpoint():
    client.post("/reset", json={"task_id": "fix_dates_and_nulls"})
    client.post("/step", json={"action_type": "submit"})
    r = client.get("/episodes")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_generate_endpoint_default():
    r = client.post("/generate")
    assert r.status_code == 200
    data = r.json()
    assert data["num_rows"] >= 10
    assert data["done"] is False


def test_generate_endpoint_custom():
    r = client.post("/generate", json={
        "num_rows": 30, "difficulty": "hard", "seed": 42
    })
    assert r.status_code == 200
    data = r.json()
    assert data["num_rows"] >= 30


def test_generate_reproducible():
    r1 = client.post("/generate", json={"num_rows": 20, "seed": 99, "difficulty": "easy"})
    r2 = client.post("/generate", json={"num_rows": 20, "seed": 99, "difficulty": "easy"})
    assert r1.json()["dataset_csv"] == r2.json()["dataset_csv"]
