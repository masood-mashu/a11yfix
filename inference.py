import json
import os
import sys
from openai import OpenAI
from baseline_inference import LLMRunnerConfig, run_task_with_runner
from tasks.easy import get_easy_elements, MAX_STEPS as EASY_MAX_STEPS
from tasks.medium import get_medium_elements, MAX_STEPS as MEDIUM_MAX_STEPS
from tasks.hard import get_hard_elements, MAX_STEPS as HARD_MAX_STEPS

API_BASE_URL = os.getenv("API_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta/llama-3.1-8b-instruct")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
BENCHMARK = "a11yfix"

TASKS = [
    ("easy",   get_easy_elements,   EASY_MAX_STEPS),
    ("medium", get_medium_elements, MEDIUM_MAX_STEPS),
    ("hard",   get_hard_elements,   HARD_MAX_STEPS),
]

def build_runner():
    if not HF_TOKEN:
        return None

    try:
        client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    except Exception as exc:
        print(f"[WARN] Failed to initialize OpenAI client: {exc}", file=sys.stderr, flush=True)
        return None

    return LLMRunnerConfig(client=client, model_name=MODEL_NAME)


def emit_result(result):
    history = result["history"]
    rewards = [h["reward"] for h in history]
    success = result["final_score"] >= 1.0

    for h in history:
        action_str = json.dumps(h["action"])
        done_str = str(h["done"]).lower()
        print(
            f"[STEP] step={h['step']} action={action_str} "
            f"reward={h['reward']:.2f} done={done_str} error=null",
            flush=True,
        )

    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={result['steps_used']} "
        f"score={result['final_score']:.3f} rewards={rewards_str}",
        flush=True,
    )


def main():
    runner = build_runner()

    for task_name, get_elements, max_steps in TASKS:
        print(f"[START] task={task_name} env={BENCHMARK} model={MODEL_NAME}", flush=True)

        elements = get_elements()
        try:
            result = run_task_with_runner(task_name, elements, max_steps, runner=runner)
        except Exception as exc:
            print(
                f"[WARN] Falling back to offline baseline for task '{task_name}': {exc}",
                file=sys.stderr,
                flush=True,
            )
            result = run_task_with_runner(task_name, elements, max_steps, runner=None)

        emit_result(result)

if __name__ == "__main__":
    main()
