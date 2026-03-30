"""
Smart inference agent for the Data Cleaning Environment.
Uses chain-of-thought reasoning, hint-driven planning, and self-verification.

Required environment variables:
  - API_BASE_URL: Base URL for the OpenAI-compatible API
  - MODEL_NAME: Model to use
  - HF_TOKEN: Hugging Face token for authentication

Usage:
  API_BASE_URL=http://... MODEL_NAME=... HF_TOKEN=... python inference.py
"""

import os
import json
import re
import requests
from openai import OpenAI

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.environ.get("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
ENV_URL = os.environ.get("ENV_URL", "http://localhost:7860")

CURATED_TASKS = ["fix_dates_and_nulls", "dedup_and_normalize", "full_pipeline_clean"]

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def get_openai_client() -> OpenAI:
    return OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)


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
    resp = requests.post(f"{ENV_URL}/step", json=action)
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
    """Sort hints by severity (high first), then by row index."""
    return sorted(hints, key=lambda h: (
        SEVERITY_ORDER.get(h.get("severity", "low"), 3),
        h.get("row_index", 0)
    ))


def build_analysis_prompt(obs: dict, hints_data: dict) -> str:
    """Build a detailed prompt with dataset state and detected errors."""
    sorted_hints = prioritize_hints(hints_data.get("hints", []))

    if sorted_hints:
        hints_lines = []
        for h in sorted_hints[:15]:
            hints_lines.append(
                f"  [{h['severity'].upper()}] Row {h['row_index']}, "
                f"col '{h['column_name']}': {h['description']} "
                f"(suggest: {h['suggested_action']})"
            )
        hints_text = "Detected errors (prioritized):\n" + "\n".join(hints_lines)
    else:
        hints_text = "No errors detected by the hint system."

    return f"""Current dataset (CSV):
{obs['dataset_csv']}

Column types expected: {json.dumps(obs['column_types'])}
Rows: {obs['num_rows']}
Step {obs['step_number']}/{obs['max_steps']}
Current score: {obs['score']}
Last action: {obs['last_action_message']}

{hints_text}

STRATEGY:
1. Fix HIGH severity errors first (malformed dates, missing values, type errors)
2. Then MEDIUM severity (duplicates, inconsistent casing, outliers)
3. Then LOW severity (minor formatting)
4. After all errors are fixed, SUBMIT

Pick the SINGLE most impactful action. If score is already high and few errors remain, consider submitting.
Row indices are 0-based and update after deletions.

Respond with ONLY a JSON action object."""


SYSTEM_PROMPT = """You are an expert data cleaning agent. You systematically clean dirty datasets using a structured approach:

1. SCAN: Analyze the dataset for all error types
2. PLAN: Prioritize fixes by severity and impact
3. EXECUTE: Fix one error at a time, starting with the highest impact
4. VERIFY: Check that each fix improved the score

Available actions (respond with exactly ONE JSON object):
- {"action_type": "fix_date", "row_index": N, "column_name": "col", "new_value": "YYYY-MM-DD"}
- {"action_type": "fill_missing", "row_index": N, "column_name": "col", "new_value": "value"}
- {"action_type": "delete_row", "row_index": N}
- {"action_type": "replace_value", "row_index": N, "column_name": "col", "new_value": "value"}
- {"action_type": "fix_type", "row_index": N, "column_name": "col", "new_value": "value"}
- {"action_type": "submit"} — when the dataset is clean

Rules:
- Dates must be YYYY-MM-DD format
- Missing strings: fill with sensible defaults (e.g., "Unknown", "unknown@example.com")
- Missing numbers: fill with 0
- Duplicates: delete the later occurrence (keep first)
- Categories: normalize to Title Case
- Booleans: normalize to lowercase "true"/"false"
- Computed columns (like total = quantity * unit_price): recalculate
- Negative quantities or extreme outlier prices: fix to reasonable values

Respond with ONLY a JSON object. No explanation."""


def extract_json(text: str) -> dict:
    """Extract JSON object from LLM response."""
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


def run_task(client: OpenAI, task_id: str, use_generate: bool = False,
             gen_config: dict = None) -> float:
    """Run a single task with the smart agent."""
    print(f"\n{'='*60}")
    print(f"Task: {task_id}")
    print(f"{'='*60}")

    if use_generate and gen_config:
        obs = env_generate(**gen_config)
        print(f"  [Generated] rows={gen_config.get('num_rows')}, "
              f"difficulty={gen_config.get('difficulty')}")
    else:
        obs = env_reset(task_id)

    print(f"  Rows: {obs['num_rows']}, Columns: {obs['num_columns']}")
    print(f"  Column types: {obs['column_types']}")
    print(f"  Max steps: {obs['max_steps']}")

    prev_score = 0.0
    stall_count = 0

    for step_num in range(obs['max_steps']):
        if obs.get('done', False):
            break

        try:
            hints_data = env_hints()
        except Exception:
            hints_data = {"total_errors": 0, "hints": []}

        if hints_data["total_errors"] == 0 and obs.get("score", 0) > 0.5:
            print(f"  Step {step_num+1}: No errors detected, submitting...")
            action = {"action_type": "submit"}
        else:
            user_prompt = build_analysis_prompt(obs, hints_data)
            llm_response = call_llm(client, SYSTEM_PROMPT, user_prompt)

            if not llm_response:
                print(f"  Step {step_num+1}: Empty LLM response, submitting...")
                action = {"action_type": "submit"}
            else:
                action = extract_json(llm_response)

        action_desc = action.get("action_type", "?")
        if action.get("row_index") is not None:
            action_desc += f" r{action['row_index']}"
        if action.get("column_name"):
            action_desc += f":{action['column_name']}"

        obs = env_step(action)
        current_score = obs.get("score", 0.0)
        delta = current_score - prev_score
        delta_str = f"+{delta:.4f}" if delta >= 0 else f"{delta:.4f}"

        print(f"  Step {step_num+1}: {action_desc:30s} "
              f"score={current_score:.4f} ({delta_str})")

        # Self-verification: undo if score dropped
        if delta < -0.01 and action.get("action_type") != "submit":
            print(f"  -> Score dropped! Undoing...")
            try:
                obs = env_undo()
                current_score = obs.get("score", 0.0)
            except Exception:
                pass

        # Stall detection
        if abs(delta) < 0.001:
            stall_count += 1
        else:
            stall_count = 0

        if stall_count >= 3 and current_score > 0.3:
            print(f"  -> Stalled for {stall_count} steps, submitting...")
            obs = env_step({"action_type": "submit"})
            break

        prev_score = current_score

        if action.get("action_type") == "submit":
            break

    final_score = obs.get("score", 0.0)
    print(f"\n  Final score for {task_id}: {final_score:.4f}")

    try:
        validation = env_validate()
        remaining = validation.get("error_breakdown", {})
        if remaining:
            print(f"  Remaining errors: {remaining}")
    except Exception:
        pass

    return final_score


def main():
    print("Data Cleaning Agent v2.0 — Smart Inference")
    print(f"  API: {API_BASE_URL}")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Environment: {ENV_URL}")
    print()

    client = get_openai_client()
    scores = {}

    for task_id in CURATED_TASKS:
        try:
            score = run_task(client, task_id)
            scores[task_id] = score
        except Exception as e:
            print(f"  ERROR on {task_id}: {e}")
            scores[task_id] = 0.0

    try:
        gen_config = {"num_rows": 30, "difficulty": "medium", "seed": 2024}
        score = run_task(client, "generated_medium_30r",
                         use_generate=True, gen_config=gen_config)
        scores["generated_medium_30r"] = score
    except Exception as e:
        print(f"  ERROR on generated task: {e}")
        scores["generated_medium_30r"] = 0.0

    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}")
    for task_id, score in scores.items():
        bar = "#" * int(score * 30)
        print(f"  {task_id:30s} {score:.4f} |{bar}")
    avg = sum(scores.values()) / len(scores) if scores else 0
    print(f"\n  Average score: {avg:.4f}")

    with open("results.json", "w") as f:
        json.dump({"scores": scores, "average": avg, "version": "2.0"}, f, indent=2)
    print("\nResults saved to results.json")


if __name__ == "__main__":
    main()
