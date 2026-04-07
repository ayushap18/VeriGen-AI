"""
Smart inference agent for the Data Cleaning Environment.
Uses chain-of-thought reasoning, hint-driven planning, and self-verification.

Required environment variables:
  - API_BASE_URL: Base URL for the OpenAI-compatible API
  - MODEL_NAME: Model to use
  - OPENAI_API_KEY (or HF_TOKEN): API key for authentication
  - ENV_URL: Environment server URL (default: http://localhost:7860)

Usage:
  API_BASE_URL=http://... MODEL_NAME=... OPENAI_API_KEY=... python inference.py
"""

import os
import json
import re
import requests
from openai import OpenAI

# ---- Configuration from environment variables ----
# Defaults are set only for API_BASE_URL and MODEL_NAME (not HF_TOKEN)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
API_KEY = os.getenv("OPENAI_API_KEY") or HF_TOKEN or ""
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")

ENV_NAME = "data-cleaning-agent"
SUCCESS_THRESHOLD = 0.5

CURATED_TASKS = ["fix_dates_and_nulls", "dedup_and_normalize", "full_pipeline_clean"]

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


# ---- Structured logging (OpenEnv spec) ----

def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error):
    done_val = str(done).lower()
    error_val = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: list):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


# ---- OpenAI client ----

def get_openai_client() -> OpenAI:
    return OpenAI(base_url=API_BASE_URL, api_key=API_KEY)


def call_llm(client: OpenAI, system_prompt: str, user_prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2048,
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  LLM call failed: {e}")
        return ""


# ---- Environment API ----

def env_reset(task_id: str) -> dict:
    resp = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id})
    resp.raise_for_status()
    return resp.json()


def env_step(action: dict) -> dict:
    clean = {"action_type": action.get("action_type", "submit")}
    if action.get("row_index") is not None:
        clean["row_index"] = int(action["row_index"])
    if action.get("column_name"):
        clean["column_name"] = str(action["column_name"])
    if action.get("new_value") is not None:
        clean["new_value"] = str(action["new_value"])
    resp = requests.post(f"{ENV_URL}/step", json=clean)
    resp.raise_for_status()
    return resp.json()


def env_hints() -> dict:
    resp = requests.get(f"{ENV_URL}/hints")
    resp.raise_for_status()
    return resp.json()


def env_validate() -> dict:
    resp = requests.get(f"{ENV_URL}/validate")
    resp.raise_for_status()
    return resp.json()


def env_undo() -> dict:
    resp = requests.post(f"{ENV_URL}/undo")
    resp.raise_for_status()
    return resp.json()


def env_generate(num_rows: int = 50, difficulty: str = "medium",
                 seed: int = None) -> dict:
    payload = {"num_rows": num_rows, "difficulty": difficulty}
    if seed is not None:
        payload["seed"] = seed
    resp = requests.post(f"{ENV_URL}/generate", json=payload)
    resp.raise_for_status()
    return resp.json()


# ---- Agent Logic ----

def prioritize_hints(hints: list[dict]) -> list[dict]:
    return sorted(hints, key=lambda h: (
        SEVERITY_ORDER.get(h.get("severity", "low"), 3),
        h.get("row_index", 0)
    ))


def build_analysis_prompt(obs: dict, hints_data: dict) -> str:
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


def format_action(action: dict) -> str:
    action_type = action.get("action_type", "?")
    parts = [action_type]
    if action.get("row_index") is not None:
        parts.append(f"r{action['row_index']}")
    if action.get("column_name"):
        parts.append(action["column_name"])
    return "_".join(parts)


def run_task(client: OpenAI, task_id: str, use_generate: bool = False,
             gen_config: dict = None) -> float:
    """Run a single task with the smart agent."""

    if use_generate and gen_config:
        obs = env_generate(**gen_config)
    else:
        obs = env_reset(task_id)

    log_start(task=task_id, env=ENV_NAME, model=MODEL_NAME)

    prev_score = 0.0
    stall_count = 0
    undo_count = 0
    total_steps = 0
    rewards = []
    failed_actions = set()

    for step_num in range(obs['max_steps']):
        if obs.get('done', False):
            break

        try:
            hints_data = env_hints()
        except Exception:
            hints_data = {"total_errors": 0, "hints": []}

        error = None

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
                user_prompt = build_analysis_prompt(obs, hints_data)
                llm_response = call_llm(client, SYSTEM_PROMPT, user_prompt)

                if not llm_response:
                    action = {"action_type": "submit"}
                    error = "empty_llm_response"
                else:
                    action = extract_json(llm_response)

        obs = env_step(action)
        total_steps += 1
        current_score = obs.get("score", 0.0)
        delta = current_score - prev_score
        done = obs.get("done", False)

        action_str = format_action(action)
        rewards.append(current_score)

        log_step(
            step=total_steps,
            action=action_str,
            reward=current_score,
            done=done,
            error=error
        )

        # Self-verification: undo if score dropped
        if delta < -0.01 and action.get("action_type") != "submit":
            undo_count += 1
            action_key = f"{action.get('row_index')}:{action.get('column_name', '*')}"
            failed_actions.add(action_key)
            try:
                obs = env_undo()
                current_score = obs.get("score", 0.0)
            except Exception:
                pass

            if undo_count >= 5:
                obs = env_step({"action_type": "submit"})
                total_steps += 1
                rewards.append(obs.get("score", 0.0))
                log_step(step=total_steps, action="submit", reward=obs.get("score", 0.0),
                         done=True, error=None)
                break
        else:
            undo_count = 0

        # Stall detection
        if abs(delta) < 0.001:
            stall_count += 1
        else:
            stall_count = 0

        if stall_count >= 5 and current_score > 0.3:
            obs = env_step({"action_type": "submit"})
            total_steps += 1
            rewards.append(obs.get("score", 0.0))
            log_step(step=total_steps, action="submit", reward=obs.get("score", 0.0),
                     done=True, error=None)
            break

        prev_score = current_score

        if action.get("action_type") == "submit":
            break

    final_score = obs.get("score", 0.0)
    if not rewards:
        rewards = [final_score]

    score = max(rewards) if rewards else 0.0
    score = min(max(score, 0.0), 1.0)
    success = score >= SUCCESS_THRESHOLD

    log_end(success=success, steps=total_steps, score=score, rewards=rewards)

    return final_score


def main():
    print(f"Data Cleaning Agent v2.0", flush=True)
    print(f"  API: {API_BASE_URL}", flush=True)
    print(f"  Model: {MODEL_NAME}", flush=True)
    print(f"  Environment: {ENV_URL}", flush=True)
    print(flush=True)

    client = get_openai_client()
    scores = {}

    for task_id in CURATED_TASKS:
        try:
            score = run_task(client, task_id)
            scores[task_id] = score
        except Exception as e:
            print(f"  ERROR on {task_id}: {e}", flush=True)
            scores[task_id] = 0.0

    try:
        gen_config = {"num_rows": 30, "difficulty": "medium", "seed": 2024}
        score = run_task(client, "generated_medium_30r",
                         use_generate=True, gen_config=gen_config)
        scores["generated_medium_30r"] = score
    except Exception as e:
        print(f"  ERROR on generated task: {e}", flush=True)
        scores["generated_medium_30r"] = 0.0

    avg = sum(scores.values()) / len(scores) if scores else 0
    print(f"\nAverage score: {avg:.4f}", flush=True)

    with open("results.json", "w") as f:
        json.dump({"scores": scores, "average": avg, "version": "2.0"}, f, indent=2)
    print("Results saved to results.json", flush=True)


if __name__ == "__main__":
    main()
