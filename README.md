---
title: Data Cleaning Agent Environment
emoji: 🧹
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# Data Cleaning Agent Environment

An **OpenEnv-compliant** environment where AI agents learn to clean messy real-world datasets. Agents must detect and fix data quality issues including malformed dates, missing values, duplicates, inconsistent categories, type errors, and incorrect computed fields.

## Why Data Cleaning?

Data cleaning consumes **60-80% of a data scientist's time** in real-world workflows. This environment trains AI agents to automate the most common and tedious cleaning tasks, making it immediately useful in production data pipelines.

## Environment Overview

The agent receives a **dirty CSV dataset** and must produce a **clean version** by taking sequential actions. Each action modifies the dataset, and the agent receives feedback (updated dataset + score) after every step.

### Action Space

| Action | Parameters | Description |
|---|---|---|
| `fix_date` | row_index, column_name, new_value | Fix malformed date → YYYY-MM-DD |
| `fill_missing` | row_index, column_name, new_value | Fill empty/null values |
| `delete_row` | row_index | Remove duplicate or invalid rows |
| `replace_value` | row_index, column_name, new_value | Replace incorrect values |
| `fix_type` | row_index, column_name, new_value | Fix type errors (e.g., string → int) |
| `submit` | — | Submit the cleaned dataset |

### Observation Space

After each action, the agent receives:
- `dataset_csv`: Current state of the dataset as CSV
- `num_rows`, `num_columns`: Dataset dimensions
- `column_names`, `column_types`: Schema information
- `step_number` / `max_steps`: Progress tracking
- `last_action_success` + `last_action_message`: Feedback
- `score`: Current score (0.0 – 1.0)

### Reward Function

Score is computed as a weighted combination:
- **40% Cell accuracy**: Cell-by-cell comparison with ground truth
- **40% Row match**: F1 score of exact row matches
- **20% Structural match**: Column names and order correctness

This provides **partial credit** — each correct fix improves the score.

## Tasks

| Task ID | Difficulty | Description | Max Steps |
|---|---|---|---|
| `fix_dates_and_nulls` | Easy | Fix date formats + handle missing values | 20 |
| `dedup_and_normalize` | Medium | Remove duplicates + normalize categories | 25 |
| `full_pipeline_clean` | Hard | End-to-end cleaning: dates, dupes, types, outliers, computed fields | 40 |

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check |
| `/reset` | POST | Reset to a task (`{"task_id": "..."}`) |
| `/step` | POST | Take an action |
| `/state` | GET | Get full environment state |
| `/tasks` | GET | List all available tasks |

## Setup & Local Development

### Prerequisites
- Python 3.10+
- Docker (for deployment)

### Install & Run Locally

```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Test the Endpoints

```bash
# Health check
curl http://localhost:7860/

# Reset to easy task
curl -X POST http://localhost:7860/reset -H "Content-Type: application/json" -d '{"task_id": "fix_dates_and_nulls"}'

# Take an action
curl -X POST http://localhost:7860/step -H "Content-Type: application/json" -d '{"action_type": "fix_date", "row_index": 1, "column_name": "signup_date", "new_value": "2024-01-20"}'
```

### Run Baseline Agent

```bash
export API_BASE_URL="https://api-inference.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export HF_TOKEN="your_token_here"
export ENV_URL="http://localhost:7860"

python inference.py
```

### Docker Build & Run

```bash
docker build -t data-cleaning-env .
docker run -p 7860:7860 data-cleaning-env
```

## Baseline Scores

| Task | Score |
|---|---|
| fix_dates_and_nulls (Easy) | ~0.45–0.65 |
| dedup_and_normalize (Medium) | ~0.35–0.55 |
| full_pipeline_clean (Hard) | ~0.25–0.45 |

*Scores vary depending on the LLM model used.*

## Project Structure

```
data-cleaning-env/
├── models.py              ← Pydantic models (Action, Observation, State)
├── client.py              ← Python client for the environment
├── server/
│   ├── environment.py     ← Core environment logic
│   └── app.py             ← FastAPI server
├── tasks/
│   └── task_data.py       ← Task definitions, data, and graders
├── inference.py           ← Baseline agent script
├── openenv.yaml           ← OpenEnv manifest
├── Dockerfile             ← Container definition
├── requirements.txt       ← Python dependencies
├── pyproject.toml         ← Package metadata
└── README.md              ← This file
```

## Team

**Codecatalysts** — Built for the OpenEnv Hackathon 2026
- Ayush (Team Lead)
- Yatharth Gautam
- Vardaan Dua
