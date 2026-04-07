"""
FastAPI server for the Data Cleaning Environment.
Exposes reset, step, state, hints, validate, undo, episodes, generate, and health endpoints.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse
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


@app.get("/", response_class=HTMLResponse)
def root():
    tasks_html = ""
    diff_colors = {"easy": "#22c55e", "medium": "#f59e0b", "hard": "#ef4444"}
    for tid, task in TASKS.items():
        color = diff_colors.get(task["difficulty"], "#888")
        tasks_html += f"""
        <div class="task-card">
          <div class="task-header">
            <code class="task-id">{tid}</code>
            <span class="badge" style="background:{color}">{task['difficulty'].upper()}</span>
          </div>
          <p class="task-desc">{task['description']}</p>
          <div class="task-meta">
            <span>Max steps: {task['max_steps']}</span>
            <span>Columns: {len(task['types'])}</span>
          </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VeriGen AI — Data Cleaning Agent</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
    background:#0a0a0a;color:#e0e0e0;min-height:100vh}}
  .container{{max-width:960px;margin:0 auto;padding:32px 20px}}
  .hero{{text-align:center;padding:48px 0 32px}}
  .hero h1{{font-size:2.4rem;font-weight:700;
    background:linear-gradient(135deg,#22c55e,#3b82f6);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent}}
  .hero .sub{{color:#888;font-size:1.1rem;margin-top:8px}}
  .hero .version{{display:inline-block;margin-top:12px;padding:4px 12px;
    background:#1a1a2e;border:1px solid #333;border-radius:20px;font-size:0.8rem;color:#888}}
  .status-bar{{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin:24px 0}}
  .status-pill{{padding:6px 16px;border-radius:20px;font-size:0.85rem;font-weight:500}}
  .status-live{{background:#052e16;color:#22c55e;border:1px solid #166534}}
  .status-feat{{background:#1a1a2e;color:#93c5fd;border:1px solid #1e3a5f}}
  h2{{font-size:1.3rem;margin:32px 0 16px;color:#fff;
    border-bottom:1px solid #222;padding-bottom:8px}}
  .task-card{{background:#111;border:1px solid #222;border-radius:12px;
    padding:20px;margin-bottom:12px;transition:border-color 0.2s}}
  .task-card:hover{{border-color:#3b82f6}}
  .task-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}}
  .task-id{{font-size:1rem;color:#93c5fd;background:#1a1a2e;padding:2px 8px;border-radius:4px}}
  .badge{{padding:3px 10px;border-radius:12px;font-size:0.75rem;font-weight:600;color:#fff}}
  .task-desc{{color:#aaa;font-size:0.9rem;margin-bottom:8px}}
  .task-meta{{display:flex;gap:16px;font-size:0.8rem;color:#666}}
  .endpoints{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}}
  .ep{{background:#111;border:1px solid #222;border-radius:8px;padding:12px 16px;
    display:flex;align-items:center;gap:10px}}
  .method{{font-size:0.7rem;font-weight:700;padding:2px 8px;border-radius:4px;min-width:44px;text-align:center}}
  .method-get{{background:#052e16;color:#22c55e}}
  .method-post{{background:#1e1b4b;color:#a78bfa}}
  .ep-path{{color:#e0e0e0;font-family:monospace;font-size:0.9rem}}
  .try-section{{background:#111;border:1px solid #222;border-radius:12px;padding:24px;margin-top:24px}}
  .try-section h3{{margin-bottom:16px;color:#fff}}
  .btn-row{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}}
  .btn{{padding:8px 16px;border-radius:8px;border:1px solid #333;background:#1a1a2e;
    color:#93c5fd;cursor:pointer;font-family:monospace;font-size:0.85rem;transition:all 0.2s}}
  .btn:hover{{background:#1e3a5f;border-color:#3b82f6}}
  .btn.active{{background:#1e3a5f;border-color:#3b82f6}}
  #output{{background:#0a0a0a;border:1px solid #222;border-radius:8px;padding:16px;
    font-family:monospace;font-size:0.85rem;min-height:120px;white-space:pre-wrap;
    overflow-x:auto;color:#22c55e}}
  .footer{{text-align:center;margin-top:48px;padding:24px 0;border-top:1px solid #222;color:#555;font-size:0.8rem}}
  .footer a{{color:#3b82f6;text-decoration:none}}
</style>
</head>
<body>
<div class="container">
  <div class="hero">
    <h1>VeriGen AI</h1>
    <div class="sub">Data Cleaning Agent Environment</div>
    <div class="version">OpenEnv v2.0.0 &bull; Codecatalysts</div>
  </div>

  <div class="status-bar">
    <span class="status-pill status-live">LIVE</span>
    <span class="status-pill status-feat">Dynamic Generation</span>
    <span class="status-pill status-feat">Error Hints</span>
    <span class="status-pill status-feat">Undo/Redo</span>
    <span class="status-pill status-feat">Validation</span>
    <span class="status-pill status-feat">Episodes</span>
  </div>

  <h2>Tasks</h2>
  {tasks_html}

  <h2>API Endpoints</h2>
  <div class="endpoints">
    <div class="ep"><span class="method method-post">POST</span><span class="ep-path">/reset</span></div>
    <div class="ep"><span class="method method-post">POST</span><span class="ep-path">/step</span></div>
    <div class="ep"><span class="method method-get">GET</span><span class="ep-path">/state</span></div>
    <div class="ep"><span class="method method-get">GET</span><span class="ep-path">/hints</span></div>
    <div class="ep"><span class="method method-get">GET</span><span class="ep-path">/validate</span></div>
    <div class="ep"><span class="method method-post">POST</span><span class="ep-path">/undo</span></div>
    <div class="ep"><span class="method method-get">GET</span><span class="ep-path">/tasks</span></div>
    <div class="ep"><span class="method method-get">GET</span><span class="ep-path">/episodes</span></div>
    <div class="ep"><span class="method method-post">POST</span><span class="ep-path">/generate</span></div>
    <div class="ep"><span class="method method-get">GET</span><span class="ep-path">/health</span></div>
    <div class="ep"><span class="method method-get">GET</span><span class="ep-path">/metadata</span></div>
    <div class="ep"><span class="method method-get">GET</span><span class="ep-path">/schema</span></div>
  </div>

  <div class="try-section">
    <h3>Try It Live</h3>
    <div class="btn-row">
      <button class="btn" onclick="tryEndpoint('POST','/reset','{{\"task_id\":\"fix_dates_and_nulls\"}}')">Reset (Easy)</button>
      <button class="btn" onclick="tryEndpoint('POST','/reset','{{\"task_id\":\"dedup_and_normalize\"}}')">Reset (Medium)</button>
      <button class="btn" onclick="tryEndpoint('POST','/reset','{{\"task_id\":\"full_pipeline_clean\"}}')">Reset (Hard)</button>
      <button class="btn" onclick="tryEndpoint('GET','/hints')">Get Hints</button>
      <button class="btn" onclick="tryEndpoint('GET','/validate')">Validate</button>
      <button class="btn" onclick="tryEndpoint('GET','/state')">State</button>
      <button class="btn" onclick="tryEndpoint('GET','/tasks')">Tasks</button>
      <button class="btn" onclick="tryEndpoint('GET','/health')">Health</button>
      <button class="btn" onclick="tryEndpoint('POST','/generate','{{\"num_rows\":20,\"difficulty\":\"easy\",\"seed\":42}}')">Generate</button>
    </div>
    <div id="output">Click a button above to try the API...</div>
  </div>

  <div class="footer">
    Built by <strong>Codecatalysts</strong> for
    <a href="https://github.com/ayushap18/VeriGen-AI">OpenEnv Hackathon 2026</a>
    &bull; Train AI agents to clean messy real-world datasets
  </div>
</div>
<script>
async function tryEndpoint(method, path, body) {{
  const out = document.getElementById('output');
  out.textContent = `${{method}} ${{path}} ...`;
  try {{
    const opts = {{method, headers: {{'Content-Type': 'application/json'}}}};
    if (body) opts.body = body;
    const r = await fetch(path, opts);
    const data = await r.json();
    out.textContent = JSON.stringify(data, null, 2);
  }} catch(e) {{
    out.textContent = 'Error: ' + e.message;
  }}
}}
</script>
</body>
</html>"""


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
