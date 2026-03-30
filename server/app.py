"""
FastAPI server for the Data Cleaning Environment.
Exposes reset(), step(), and state() endpoints per OpenEnv spec.
"""

import sys
import os

# Add parent directory to path so we can import models and tasks
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional

from models import Action, Observation, State
from server.environment import DataCleaningEnvironment
from tasks.task_data import TASKS

app = FastAPI(
    title="Data Cleaning Environment",
    description="An OpenEnv-compliant environment for training AI agents to clean messy datasets.",
    version="1.0.0"
)

# Single environment instance
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
    """Health check endpoint."""
    return {
        "status": "ok",
        "environment": "data-cleaning-agent",
        "version": "1.0.0",
        "available_tasks": list(TASKS.keys())
    }


@app.post("/reset", response_model=Observation)
def reset(request: Optional[ResetRequest] = Body(default=None)):
    """Reset the environment to a specific task."""
    try:
        task_id = request.task_id if request else "fix_dates_and_nulls"
        observation = env.reset(task_id)
        return observation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=Observation)
def step(request: StepRequest):
    """Take an action in the environment."""
    try:
        action = Action(
            action_type=request.action_type,
            row_index=request.row_index,
            column_name=request.column_name,
            new_value=request.new_value
        )
        observation = env.step(action)
        return observation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state", response_model=State)
def state():
    """Get the full current state of the environment."""
    try:
        return env.get_state()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks")
def list_tasks():
    """List all available tasks with metadata."""
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


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
