import json
import os
from dataclasses import dataclass
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

def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    runner = LLMRunnerConfig(client=client, model_name=MODEL_NAME)

    for task_name, get_elements, max_steps in TASKS:
        print(f"[START] task={task_name} env={BENCHMARK} model={MODEL_NAME}", flush=True)

        result = run_task_with_runner(task_name, get_elements(), max_steps, runner=runner)
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

if __name__ == "__main__":
    main()