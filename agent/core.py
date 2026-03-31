"""Event-driven agent core. Yields events for the dashboard to consume."""

import json
import re
import time
import requests
from dataclasses import dataclass, field
from typing import Generator
from openai import OpenAI

from agent.events import StepResult, TaskStart, TaskEnd, RunComplete
from agent.token_tracker import TokenTracker

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

SYSTEM_PROMPT = """You are an expert data cleaning agent. Fix ONE error per step.

Available actions (respond with exactly ONE JSON object):
- {"action_type": "fix_date", "row_index": N, "column_name": "col", "new_value": "YYYY-MM-DD"}
- {"action_type": "fill_missing", "row_index": N, "column_name": "col", "new_value": "value"}
- {"action_type": "delete_row", "row_index": N}
- {"action_type": "replace_value", "row_index": N, "column_name": "col", "new_value": "value"}
- {"action_type": "fix_type", "row_index": N, "column_name": "col", "new_value": "value"}
- {"action_type": "submit"}

CRITICAL RULES:
- Dates: convert to YYYY-MM-DD (e.g. "03/15/2024" -> "2024-03-15", "15-Mar-2024" -> "2024-03-15")
- Missing strings: "Unknown" for names/cities, "unknown@example.com" for emails
- Missing numbers: "0" for integers, "0.0" for floats
- Booleans: must be exactly "true" or "false" (lowercase)
- Duplicates: use delete_row on the LATER duplicate (higher row index), keep first
- Computed columns: if total = quantity * unit_price, recalculate (e.g. qty=3, price=10.0 -> total="30.0")
- Negative quantities: replace with absolute value
- Outlier prices (>50000): replace with median of other prices in that column
- Categories: normalize to Title Case (e.g. "ELECTRONICS" -> "Electronics")

IMPORTANT: After delete_row, all row indices shift down! Re-examine indices.
Row indices are 0-based.

Respond with ONLY a JSON object. No markdown, no explanation."""


@dataclass
class AgentConfig:
    api_key: str
    base_url: str
    model: str
    env_url: str = "http://localhost:7860"
    max_undos: int = 5
    max_stalls: int = 5
    curated_tasks: list = field(default_factory=lambda: [
        "fix_dates_and_nulls", "dedup_and_normalize", "full_pipeline_clean"
    ])
    gen_rows: int = 30
    gen_difficulty: str = "medium"
    gen_seed: int = 2024


def build_action_target(action: dict) -> str:
    if action.get("row_index") is not None:
        target = f"r{action['row_index']}"
        if action.get("column_name"):
            target += f":{action['column_name']}"
        return target
    return ""


def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{[^{}]+\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"action_type": "submit"}


def prioritize_hints(hints: list[dict]) -> list[dict]:
    return sorted(hints, key=lambda h: (
        SEVERITY_ORDER.get(h.get("severity", "low"), 3),
        h.get("row_index", 0)
    ))


def clean_action(action: dict) -> dict:
    clean = {"action_type": action.get("action_type", "submit")}
    if action.get("row_index") is not None:
        clean["row_index"] = int(action["row_index"])
    if action.get("column_name"):
        clean["column_name"] = str(action["column_name"])
    if action.get("new_value") is not None:
        clean["new_value"] = str(action["new_value"])
    return clean


def build_prompt(obs: dict, hints_data: dict) -> str:
    sorted_hints = prioritize_hints(hints_data.get("hints", []))
    if sorted_hints:
        hints_lines = []
        for h in sorted_hints[:20]:
            line = f"  [{h['severity'].upper()}] Row {h['row_index']}"
            if h.get('column_name'):
                line += f", col '{h['column_name']}'"
            line += f": {h['description']}"
            line += f" -> {h['suggested_action']}"
            hints_lines.append(line)
        hints_text = f"Detected {len(sorted_hints)} errors:\n" + "\n".join(hints_lines)
    else:
        hints_text = "No errors detected."

    return f"""Dataset (CSV):
{obs['dataset_csv']}

Column types: {json.dumps(obs['column_types'])}
Rows: {obs['num_rows']} | Step {obs['step_number']}/{obs['max_steps']} | Score: {obs['score']}

{hints_text}

Pick the SINGLE highest-priority fix from the hints above.
Priority: duplicate_row > wrong_computed > malformed_date > missing_value > negative_value > outlier > invalid_boolean > type_error
Row indices are 0-based. After delete_row, indices shift down.

Respond with ONLY a JSON object."""


def _env_post(env_url: str, path: str, payload: dict = None) -> dict:
    resp = requests.post(f"{env_url}{path}", json=payload or {})
    resp.raise_for_status()
    return resp.json()


def _env_get(env_url: str, path: str) -> dict:
    resp = requests.get(f"{env_url}{path}")
    resp.raise_for_status()
    return resp.json()


def run_agent(config: AgentConfig, tracker: TokenTracker
              ) -> Generator[StepResult | TaskStart | TaskEnd | RunComplete, None, None]:
    """Run the full agent pipeline, yielding events for each step."""
    client = OpenAI(base_url=config.base_url, api_key=config.api_key)
    scores = {}
    start_time = time.time()

    all_tasks = [(tid, False, None) for tid in config.curated_tasks]
    gen_config = {"num_rows": config.gen_rows, "difficulty": config.gen_difficulty,
                  "seed": config.gen_seed}
    gen_id = f"generated_{config.gen_difficulty}_{config.gen_rows}r"
    all_tasks.append((gen_id, True, gen_config))

    total_tasks = len(all_tasks)

    for task_idx, (task_id, use_gen, gen_cfg) in enumerate(all_tasks):
        try:
            if use_gen and gen_cfg:
                obs = _env_post(config.env_url, "/generate", gen_cfg)
            else:
                obs = _env_post(config.env_url, "/reset", {"task_id": task_id})
        except Exception:
            scores[task_id] = 0.0
            yield TaskEnd(task_id=task_id, final_score=0.0, steps_taken=0,
                          remaining_errors={}, task_index=task_idx, total_tasks=total_tasks)
            continue

        yield TaskStart(task_id=task_id, num_rows=obs["num_rows"],
                        num_columns=obs["num_columns"], column_types=obs["column_types"],
                        max_steps=obs["max_steps"], task_index=task_idx, total_tasks=total_tasks)

        prev_score = 0.0
        stall_count = 0
        undo_count = 0
        failed_actions = set()
        step_num = 0

        for step_num in range(obs["max_steps"]):
            if obs.get("done", False):
                break

            try:
                hints_data = _env_get(config.env_url, "/hints")
            except Exception:
                hints_data = {"total_errors": 0, "hints": []}

            tokens_in = 0
            tokens_out = 0

            if hints_data["total_errors"] == 0 and obs.get("score", 0) > 0.5:
                action = {"action_type": "submit"}
            else:
                if failed_actions:
                    filtered = [h for h in hints_data.get("hints", [])
                                if f"{h['row_index']}:{h['column_name']}" not in failed_actions]
                    hints_data = dict(hints_data)
                    hints_data["hints"] = filtered
                    hints_data["total_errors"] = len(filtered)

                if not hints_data.get("hints"):
                    action = {"action_type": "submit"}
                else:
                    user_prompt = build_prompt(obs, hints_data)
                    try:
                        response = client.chat.completions.create(
                            model=config.model,
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": user_prompt}
                            ],
                            max_tokens=2048,
                            temperature=0.1
                        )
                        llm_text = response.choices[0].message.content.strip()
                        tokens_in = getattr(response.usage, "prompt_tokens", 0)
                        tokens_out = getattr(response.usage, "completion_tokens", 0)
                        tracker.record(tokens_in, tokens_out)
                        action = extract_json(llm_text)
                    except Exception:
                        action = {"action_type": "submit"}

            obs = _env_post(config.env_url, "/step", clean_action(action))
            current_score = obs.get("score", 0.0)
            delta = current_score - prev_score
            undone = False

            if delta < -0.01 and action.get("action_type") != "submit":
                undo_count += 1
                action_key = f"{action.get('row_index')}:{action.get('column_name', '*')}"
                failed_actions.add(action_key)
                try:
                    obs = _env_post(config.env_url, "/undo")
                    current_score = obs.get("score", 0.0)
                except Exception:
                    pass
                undone = True

                if undo_count >= config.max_undos:
                    yield StepResult(task_id=task_id, step=step_num + 1,
                                     action_type=action.get("action_type", "?"),
                                     target=build_action_target(action),
                                     new_value=action.get("new_value", "") or "",
                                     score=current_score, delta=delta, undone=True,
                                     tokens_in=tokens_in, tokens_out=tokens_out)
                    obs = _env_post(config.env_url, "/step", {"action_type": "submit"})
                    break
            else:
                undo_count = 0

            yield StepResult(task_id=task_id, step=step_num + 1,
                             action_type=action.get("action_type", "?"),
                             target=build_action_target(action),
                             new_value=action.get("new_value", "") or "",
                             score=current_score, delta=delta, undone=undone,
                             tokens_in=tokens_in, tokens_out=tokens_out)

            if abs(delta) < 0.001:
                stall_count += 1
            else:
                stall_count = 0

            if stall_count >= config.max_stalls and current_score > 0.3:
                obs = _env_post(config.env_url, "/step", {"action_type": "submit"})
                break

            prev_score = current_score
            if action.get("action_type") == "submit":
                break

        final_score = obs.get("score", 0.0)
        scores[task_id] = final_score

        remaining = {}
        try:
            validation = _env_get(config.env_url, "/validate")
            remaining = validation.get("error_breakdown", {})
        except Exception:
            pass

        yield TaskEnd(task_id=task_id, final_score=final_score,
                      steps_taken=step_num + 1,
                      remaining_errors=remaining,
                      task_index=task_idx, total_tasks=total_tasks)

    avg = sum(scores.values()) / len(scores) if scores else 0
    elapsed = time.time() - start_time

    yield RunComplete(scores=scores, average=avg,
                      total_tokens_in=tracker.total_in,
                      total_tokens_out=tracker.total_out,
                      total_cost=tracker.total_cost,
                      elapsed_seconds=elapsed)
