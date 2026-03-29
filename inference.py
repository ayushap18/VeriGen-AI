"""
Baseline inference script for the Data Cleaning Environment.
Uses OpenAI-compatible client to run an LLM agent that cleans datasets.

Required environment variables:
  - API_BASE_URL: Base URL for the OpenAI-compatible API
  - MODEL_NAME: Model to use (e.g., "meta-llama/Llama-3.1-8B-Instruct")
  - HF_TOKEN: Hugging Face token for authentication

Usage:
  API_BASE_URL=http://... MODEL_NAME=... HF_TOKEN=... python inference.py
"""

import os
import json
import time
import requests
from openai import OpenAI

# ---- Configuration ----
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.environ.get("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Environment server URL (the HF Space)
ENV_URL = os.environ.get("ENV_URL", "http://localhost:7860")

TASKS = ["fix_dates_and_nulls", "dedup_and_normalize", "full_pipeline_clean"]


def get_openai_client() -> OpenAI:
    """Create OpenAI-compatible client."""
    return OpenAI(
        base_url=API_BASE_URL,
        api_key=HF_TOKEN
    )


def call_llm(client: OpenAI, system_prompt: str, user_prompt: str) -> str:
    """Call the LLM and return its text response."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1024,
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  LLM call failed: {e}")
        return ""


def env_reset(task_id: str) -> dict:
    """Reset the environment."""
    resp = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id})
    resp.raise_for_status()
    return resp.json()


def env_step(action: dict) -> dict:
    """Take a step in the environment."""
    resp = requests.post(f"{ENV_URL}/step", json=action)
    resp.raise_for_status()
    return resp.json()


SYSTEM_PROMPT = """You are a data cleaning agent. You receive a dirty CSV dataset and must clean it by performing actions.

Available actions (respond with exactly ONE JSON object per turn):
- {"action_type": "fix_date", "row_index": N, "column_name": "col", "new_value": "YYYY-MM-DD"}
- {"action_type": "fill_missing", "row_index": N, "column_name": "col", "new_value": "value"}
- {"action_type": "delete_row", "row_index": N}
- {"action_type": "replace_value", "row_index": N, "column_name": "col", "new_value": "value"}
- {"action_type": "fix_type", "row_index": N, "column_name": "col", "new_value": "value"}
- {"action_type": "submit"} — when you think the dataset is clean

Rules:
- Row indices are 0-based and update after deletions
- Dates must be in YYYY-MM-DD format
- Missing string values should be filled with sensible defaults
- Missing numeric values should be filled with 0
- Duplicates should be deleted (keep the first occurrence)
- Category values should be normalized to Title Case
- Boolean values should be lowercase "true"/"false"
- Check that computed columns (like 'total') are correct

Respond with ONLY a JSON object. No explanation, no markdown, just the JSON action."""


def extract_json(text: str) -> dict:
    """Extract JSON object from LLM response."""
    # Try direct parse first
    text = text.strip()
    if text.startswith("```"):
        # Remove markdown code fences
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in the text
    import re
    match = re.search(r'\{[^{}]+\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {"action_type": "submit"}  # fallback


def run_task(client: OpenAI, task_id: str) -> float:
    """Run a single task and return the score."""
    print(f"\n{'='*50}")
    print(f"Task: {task_id}")
    print(f"{'='*50}")

    obs = env_reset(task_id)
    print(f"  Rows: {obs['num_rows']}, Columns: {obs['num_columns']}")
    print(f"  Column types: {obs['column_types']}")
    print(f"  Max steps: {obs['max_steps']}")

    for step_num in range(obs['max_steps']):
        if obs.get('done', False):
            break

        # Build prompt with current dataset state
        user_prompt = f"""Current dataset (CSV):
{obs['dataset_csv']}

Column types expected: {json.dumps(obs['column_types'])}
Step {obs['step_number']}/{obs['max_steps']}
Current score: {obs['score']}
Last action result: {obs['last_action_message']}

Analyze the dataset and perform ONE cleaning action. Look for:
1. Malformed dates (convert to YYYY-MM-DD)
2. Missing/empty values (fill appropriately)
3. Duplicate rows (delete duplicates, keep first)
4. Inconsistent categories (normalize to Title Case)
5. Incorrect computed values (like wrong totals)
6. Type errors (negative quantities, outlier prices)
7. Inconsistent boolean formats (normalize to lowercase true/false)

If the dataset looks clean, submit it.

Respond with ONLY a JSON action object."""

        llm_response = call_llm(client, SYSTEM_PROMPT, user_prompt)
        if not llm_response:
            print(f"  Step {step_num+1}: Empty LLM response, submitting...")
            action = {"action_type": "submit"}
        else:
            action = extract_json(llm_response)

        print(f"  Step {step_num+1}: {action.get('action_type', '?')} → ", end="")

        obs = env_step(action)
        print(f"score={obs['score']}, msg='{obs['last_action_message'][:60]}'")

        if action.get("action_type") == "submit":
            break

    final_score = obs.get("score", 0.0)
    print(f"\n  Final score for {task_id}: {final_score}")
    return final_score


def main():
    print("Data Cleaning Agent — Baseline Inference")
    print(f"  API: {API_BASE_URL}")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Environment: {ENV_URL}")
    print()

    client = get_openai_client()

    scores = {}
    for task_id in TASKS:
        try:
            score = run_task(client, task_id)
            scores[task_id] = score
        except Exception as e:
            print(f"  ERROR on {task_id}: {e}")
            scores[task_id] = 0.0

    # Print summary
    print(f"\n{'='*50}")
    print("RESULTS SUMMARY")
    print(f"{'='*50}")
    for task_id, score in scores.items():
        print(f"  {task_id}: {score:.4f}")
    avg = sum(scores.values()) / len(scores) if scores else 0
    print(f"\n  Average score: {avg:.4f}")

    # Save results
    with open("results.json", "w") as f:
        json.dump({"scores": scores, "average": avg}, f, indent=2)
    print("\nResults saved to results.json")


if __name__ == "__main__":
    main()
