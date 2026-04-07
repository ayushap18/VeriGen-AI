"""
FastAPI server for the Data Cleaning Environment.
Exposes reset, step, state, hints, validate, undo, episodes, generate, and health endpoints.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional

from models import (
    Action, Observation, State,
    HintResponse, ValidateResponse, EpisodeRecord,
    GenerateTaskRequest
)
from server.environment import DataCleaningEnvironment
from tasks.task_data import TASKS

_start_time = time.time()

app = FastAPI(
    title="Data Cleaning Environment",
    description=(
        "An OpenEnv-compliant environment for training AI agents to clean messy datasets. "
        "Features dynamic task generation, error detection hints, undo/redo, validation, "
        "and multi-episode tracking."
    ),
    version="2.0.0"
)

env = DataCleaningEnvironment()


class ResetRequest(BaseModel):
    task_id: str = "fix_dates_and_nulls"


class StepRequest(BaseModel):
    action_type: str
    row_index: Optional[int] = None
    column_name: Optional[str] = None
    new_value: Optional[str] = None


@app.get("/")
def root():
    return {
        "status": "ok",
        "environment": "data-cleaning-agent",
        "version": "2.0.0",
        "available_tasks": list(TASKS.keys()),
        "features": ["dynamic_generation", "hints", "undo", "validation", "episodes"]
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "uptime_seconds": round(time.time() - _start_time, 2),
        "available_tasks": list(TASKS.keys()),
        "endpoints": [
            "GET /", "GET /health", "GET /tasks",
            "POST /reset", "POST /step", "GET /state",
            "GET /hints", "GET /validate", "POST /undo",
            "GET /episodes", "POST /generate",
            "GET /metadata", "GET /schema", "POST /mcp"
        ],
        "features": {
            "dynamic_generation": True,
            "error_hints": True,
            "undo_redo": True,
            "validation": True,
            "episode_tracking": True,
        }
    }


@app.get("/metadata")
def metadata():
    return {
        "name": "data-cleaning-agent",
        "description": (
            "An OpenEnv-compliant environment for training AI agents to clean messy datasets. "
            "Features dynamic task generation, error detection hints, undo/redo, validation, "
            "and multi-episode tracking."
        ),
        "version": "2.0.0",
        "authors": ["Codecatalysts"],
        "tags": ["data-cleaning", "tabular-data", "real-world"],
    }


@app.get("/schema")
def schema():
    return {
        "action": Action.model_json_schema(),
        "observation": Observation.model_json_schema(),
        "state": State.model_json_schema(),
    }


@app.post("/mcp")
def mcp():
    return {"jsonrpc": "2.0", "result": {"status": "ok"}}


@app.post("/reset", response_model=Observation)
def reset(request: Optional[ResetRequest] = Body(default=None)):
    try:
        task_id = request.task_id if request else "fix_dates_and_nulls"
        return env.reset(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=Observation)
def step(request: StepRequest):
    try:
        action = Action(
            action_type=request.action_type,
            row_index=request.row_index,
            column_name=request.column_name,
            new_value=request.new_value
        )
        return env.step(action)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state", response_model=State)
def state():
    try:
        return env.get_state()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks")
def list_tasks():
    return {
        task_id: {
            "difficulty": task["difficulty"],
            "description": task["description"],
            "max_steps": task["max_steps"],
            "num_columns": len(task["types"]),
            "column_types": task["types"]
        }
        for task_id, task in TASKS.items()
    }


@app.get("/hints", response_model=HintResponse)
def hints():
    try:
        error_hints = env.detect_errors()
        return HintResponse(total_errors=len(error_hints), hints=error_hints)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/validate", response_model=ValidateResponse)
def validate():
    try:
        return env.validate()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/undo", response_model=Observation)
def undo():
    try:
        return env.undo()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/episodes", response_model=list[EpisodeRecord])
def episodes():
    return env.get_episodes()


@app.post("/generate", response_model=Observation)
def generate(request: Optional[GenerateTaskRequest] = Body(default=None)):
    try:
        req = request or GenerateTaskRequest()
        return env.reset_generated(
            num_rows=req.num_rows,
            difficulty=req.difficulty,
            seed=req.seed,
            error_types=req.error_types
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
