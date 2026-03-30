import csv
import io
from tasks.generator import generate_task, ERROR_INJECTORS


def test_generate_task_returns_required_keys():
    task = generate_task(num_rows=20, difficulty="easy", seed=42)
    assert "dirty" in task
    assert "clean" in task
    assert "types" in task
    assert "max_steps" in task
    assert "difficulty" in task
    assert "description" in task


def test_generate_task_dirty_has_correct_row_count():
    task = generate_task(num_rows=30, difficulty="easy", seed=1)
    clean_reader = csv.DictReader(io.StringIO(task["clean"]))
    clean_rows = list(clean_reader)
    assert len(clean_rows) == 30


def test_generate_task_clean_is_valid():
    task = generate_task(num_rows=25, difficulty="medium", seed=7)
    reader = csv.DictReader(io.StringIO(task["clean"]))
    rows = list(reader)
    for row in rows:
        for col, val in row.items():
            assert val.strip() != "", f"Empty value in clean data: row={row}, col={col}"


def test_generate_task_seed_reproducibility():
    task1 = generate_task(num_rows=20, difficulty="easy", seed=99)
    task2 = generate_task(num_rows=20, difficulty="easy", seed=99)
    assert task1["dirty"] == task2["dirty"]
    assert task1["clean"] == task2["clean"]


def test_generate_task_different_seeds_differ():
    task1 = generate_task(num_rows=20, difficulty="easy", seed=1)
    task2 = generate_task(num_rows=20, difficulty="easy", seed=2)
    assert task1["dirty"] != task2["dirty"]


def test_generate_task_difficulty_affects_max_steps():
    easy = generate_task(num_rows=20, difficulty="easy", seed=1)
    hard = generate_task(num_rows=20, difficulty="hard", seed=1)
    assert hard["max_steps"] >= easy["max_steps"]


def test_generate_task_hard_has_more_errors():
    easy = generate_task(num_rows=50, difficulty="easy", seed=10)
    hard = generate_task(num_rows=50, difficulty="hard", seed=10)
    easy_diff = _count_differences(easy["dirty"], easy["clean"])
    hard_diff = _count_differences(hard["dirty"], hard["clean"])
    assert hard_diff >= easy_diff


def test_generate_task_specific_error_types():
    task = generate_task(num_rows=30, difficulty="medium", seed=5,
                         error_types=["null_values"])
    reader = csv.DictReader(io.StringIO(task["dirty"]))
    rows = list(reader)
    has_empty = any(val.strip() == "" for row in rows for val in row.values())
    assert has_empty, "null_values error type should produce empty cells"


def test_error_injectors_exist():
    expected = ["malformed_dates", "null_values", "duplicates",
                "inconsistent_casing", "type_errors", "wrong_computed"]
    for name in expected:
        assert name in ERROR_INJECTORS, f"Missing injector: {name}"


def _count_differences(csv1: str, csv2: str) -> int:
    rows1 = list(csv.DictReader(io.StringIO(csv1)))
    rows2 = list(csv.DictReader(io.StringIO(csv2)))
    diffs = abs(len(rows1) - len(rows2)) * 5
    for i in range(min(len(rows1), len(rows2))):
        for k in rows1[i]:
            if rows1[i].get(k, "") != rows2[i].get(k, ""):
                diffs += 1
    return diffs
