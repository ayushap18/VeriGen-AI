

<div align="center">

# VeriGen AI — Data Cleaning Agent Environment

**Train AI agents to clean messy real-world datasets. Automatically.**

[![Tests](https://github.com/ayushap18/VeriGen-AI/actions/workflows/docker-image.yml/badge.svg)](https://github.com/ayushap18/VeriGen-AI/actions)
[![HF Space](https://img.shields.io/badge/HuggingFace-Space-yellow)](https://huggingface.co/spaces/axy18/VeriGen-AI)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-v2.0-blue)](https://openenv.org)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)

</div>

---

## The Problem

Data scientists spend **60-80% of their time** cleaning data. Malformed dates, missing values, duplicates, inconsistent categories, type mismatches, wrong calculations — these errors are tedious, repetitive, and expensive.

**VeriGen AI** is an OpenEnv-compliant environment that teaches AI agents to fix these problems autonomously. Give it a dirty dataset, and the agent learns to produce a clean one — step by step, with full observability.

---

## What Makes This Different

| Feature | Basic Envs | VeriGen AI |
|---|:---:|:---:|
| Static hardcoded tasks | Yes | Yes + Dynamic |
| Procedural task generation | No | 10-500 rows, 3 templates, 6 error types |
| Error detection with hints | No | Severity-ranked, actionable hints |
| Undo/redo support | No | Full action history stack |
| Dataset validation | No | Type-aware validation with breakdown |
| Episode tracking | No | Multi-episode scores + action logs |
| Smart inference agent | Basic | CoT reasoning, self-verification, stall detection |
| Seed-based reproducibility | No | Same seed = same task, always |

---

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Run server
python -c "from server.app import main; main()"

# Server is live at http://localhost:7860
```

### Try It

```bash
# Reset to a task
curl -X POST localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "fix_dates_and_nulls"}'

# See what's wrong
curl localhost:7860/hints

# Fix a date
curl -X POST localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"action_type":"fix_date","row_index":1,"column_name":"signup_date","new_value":"2024-01-20"}'

# Changed your mind? Undo it
curl -X POST localhost:7860/undo

# Generate a fresh random task
curl -X POST localhost:7860/generate \
  -H "Content-Type: application/json" \
  -d '{"num_rows":100,"difficulty":"hard","seed":42}'
```

---

## Architecture

```
                    +------------------+
                    |   AI Agent       |
                    |  (inference.py)  |
                    +--------+---------+
                             |
                    REST API (FastAPI)
                             |
          +------------------+------------------+
          |                  |                  |
   +------+------+   +------+------+   +-------+-----+
   | /reset      |   | /step       |   | /hints      |
   | /generate   |   | /undo       |   | /validate   |
   | /tasks      |   | /state      |   | /episodes   |
   +------+------+   +------+------+   +-------+-----+
          |                  |                  |
          +------------------+------------------+
                             |
                  +----------+----------+
                  |   Environment       |
                  |  (environment.py)   |
                  +----------+----------+
                             |
              +--------------+--------------+
              |                             |
    +---------+---------+     +-------------+----------+
    | Curated Tasks     |     | Dynamic Generator      |
    | (task_data.py)    |     | (generator.py)         |
    | 3 difficulty tiers|     | Procedural error       |
    |                   |     | injection engine       |
    +-------------------+     +------------------------+
```

---

## API Reference

### Core Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `POST /reset` | Reset to a curated task (accepts empty body for defaults) |
| `POST /step` | Take a cleaning action |
| `GET /state` | Get full environment state with ground truth |
| `GET /tasks` | List all curated tasks with metadata |

### Intelligence Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `GET /hints` | Detect errors with severity-ranked, actionable hints |
| `GET /validate` | Validate dataset with error type breakdown |
| `POST /undo` | Revert last action (full state restoration) |
| `GET /episodes` | Multi-episode performance history with action logs |

### Generation Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `POST /generate` | Create dynamic task (10-500 rows, easy/medium/hard) |
| `GET /health` | Detailed health check with capabilities |

---

## Action Space

| Action | Parameters | What It Does |
|---|---|---|
| `fix_date` | row, column, value | Correct malformed dates to YYYY-MM-DD |
| `fill_missing` | row, column, value | Fill empty/null cells |
| `delete_row` | row | Remove duplicates or invalid rows |
| `replace_value` | row, column, value | Replace incorrect values |
| `fix_type` | row, column, value | Fix type mismatches |
| `submit` | — | Submit cleaned dataset for scoring |

---

## Scoring

Score is computed as a weighted combination against ground truth:

| Component | Weight | What It Measures |
|---|---|---|
| Cell accuracy | 40% | Cell-by-cell match with clean data |
| Row match (F1) | 40% | Precision + recall of exact row matches |
| Structural match | 20% | Column names and order correctness |

Every correct fix incrementally improves the score. Partial credit is always given.

---

## Tasks

### Curated Tasks

| Task ID | Difficulty | Errors | Rows | Max Steps |
|---|---|---|---|---|
| `fix_dates_and_nulls` | Easy | Malformed dates, missing values | 8 | 20 |
| `dedup_and_normalize` | Medium | Duplicates, inconsistent categories, bad booleans | 12 | 25 |
| `full_pipeline_clean` | Hard | All error types + wrong computed fields | 12 | 40 |

### Dynamic Tasks

Generate unlimited unique tasks via `/generate`:

```json
{
  "num_rows": 100,
  "difficulty": "hard",
  "seed": 42,
  "error_types": ["malformed_dates", "null_values", "duplicates"]
}
```

**6 error injectors:** `malformed_dates` | `null_values` | `duplicates` | `inconsistent_casing` | `type_errors` | `wrong_computed`

**3 data templates:** Customer records | Sales orders | Product catalogs

---

## Smart Agent

The inference agent (`inference.py`) uses a multi-stage approach:

1. **SCAN** — Query `/hints` for severity-ranked error detection
2. **PLAN** — Prioritize fixes: HIGH severity first, then MEDIUM, then LOW
3. **EXECUTE** — Apply one fix at a time via `/step`
4. **VERIFY** — If score drops, auto-undo via `/undo` and try a different approach
5. **SUBMIT** — Stall detection triggers early submission when no progress is being made

```bash
# Run the smart agent
export API_BASE_URL="https://api-inference.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export HF_TOKEN="your_token"
export ENV_URL="http://localhost:7860"

python inference.py
```

---

## Development

### Run Tests

```bash
pip install pytest httpx
python -m pytest tests/ -v    # 48 tests
```

### Docker

```bash
docker build -t verigen-ai .
docker run -p 7860:7860 verigen-ai
```

### Project Structure

```
verigen-ai/
├── server/
│   ├── app.py                 # FastAPI — 11 endpoints
│   └── environment.py         # Core logic: step, undo, hints, validate, episodes
├── tasks/
│   ├── task_data.py           # 3 curated tasks with ground truth
│   └── generator.py           # Procedural generator with 6 error injectors
├── models.py                  # Pydantic models (Action, Observation, HintItem, etc.)
├── inference.py               # Smart agent with CoT + self-verification
├── client.py                  # Python SDK for all endpoints
├── tests/                     # 48 tests (models, generator, environment, endpoints, agent)
├── openenv.yaml               # OpenEnv manifest
├── Dockerfile                 # Production container
├── requirements.txt           # Dependencies
└── pyproject.toml             # Package config with entry points
```

---

## Tech Stack

- **FastAPI** — async-ready API server
- **Pydantic v2** — strict typed models
- **OpenEnv Core** — framework compliance
- **uvicorn** — ASGI server
- **Docker** — containerized deployment
- **GitHub Actions** — CI with tests + Docker build

---

## Team

**Codecatalysts** — OpenEnv Hackathon 2026

- **Ayush** — Team Lead
- **Yatharth Gautam**
- **Vardaan Dua**

---

<div align="center">

Built with precision for the OpenEnv Hackathon 2026

</div>
