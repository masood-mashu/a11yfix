import json
import os
from typing import Any

from openai import OpenAI

from env.a11y_env import A11yAction, A11yEnv
from tasks.easy import MAX_STEPS as EASY_MAX_STEPS
from tasks.easy import get_easy_elements
from tasks.hard import MAX_STEPS as HARD_MAX_STEPS
from tasks.hard import get_hard_elements
from tasks.medium import MAX_STEPS as MEDIUM_MAX_STEPS
from tasks.medium import get_medium_elements


SYSTEM_PROMPT = """You are an RL agent fixing accessibility violations in a JSON DOM environment.

You can take exactly one action at a time.
Available actions:
1) set_attribute
   Required fields: element_id, attribute, value
2) audit
3) done

Violation-to-fix mapping:
- missing_alt -> set_attribute with attribute=\"alt\"
- missing_label -> set_attribute with attribute=\"aria-label\"
- missing_button_name -> set_attribute with attribute=\"text\"
- missing_lang -> set_attribute with attribute=\"lang\"

Respond with ONLY a JSON object and no markdown.
Example:
{\"operation\": \"set_attribute\", \"element_id\": \"img1\", \"attribute\": \"alt\", \"value\": \"Company logo\"}
"""


def _strip_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def _parse_llm_action(content: str) -> A11yAction:
    fallback = A11yAction(operation="audit")

    try:
        parsed = json.loads(_strip_markdown_fences(content))
    except json.JSONDecodeError:
        return fallback

    operation = str(parsed.get("operation", "")).strip()
    if operation not in {"set_attribute", "audit", "done"}:
        return fallback

    if operation == "set_attribute":
        element_id = str(parsed.get("element_id", "")).strip()
        attribute = str(parsed.get("attribute", "")).strip()
        value = str(parsed.get("value", "")).strip()

        if not element_id or not attribute:
            return fallback

        return A11yAction(
            operation="set_attribute",
            element_id=element_id,
            attribute=attribute,
            value=value,
        )

    return A11yAction(operation=operation)


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)


def _llm_choose_action(violations: list[dict[str, Any]], score: float, steps_remaining: int) -> A11yAction:
    user_prompt = (
        "Current violations:\n"
        f"{json.dumps(violations, indent=2)}\n\n"
        f"Current score: {score}\n"
        f"Steps remaining: {steps_remaining}\n\n"
        "Choose one next action."
    )

    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    return _parse_llm_action(content)


def run_task_with_llm(task_name: str, elements: list[dict[str, Any]], max_steps: int) -> dict[str, Any]:
    env = A11yEnv(elements, max_steps=max_steps)
    observation = env.reset()

    total_reward = 0.0
    history: list[dict[str, Any]] = []

    while not observation.done:
        audit_observation = env.step(A11yAction(operation="audit"))
        total_reward += float(audit_observation.reward or 0.0)

        if audit_observation.done:
            observation = audit_observation
            break

        violations = audit_observation.audit
        steps_remaining = max(0, audit_observation.max_steps - audit_observation.step_count)

        action = _llm_choose_action(
            violations=violations,
            score=float(audit_observation.score),
            steps_remaining=steps_remaining,
        )

        observation = env.step(action)
        total_reward += float(observation.reward or 0.0)

        history.append(
            {
                "step": int(observation.step_count),
                "action": action.model_dump(),
                "reward": float(observation.reward or 0.0),
                "score": float(observation.score),
                "done": bool(observation.done),
            }
        )

    return {
        "task": task_name,
        "final_score": float(observation.score),
        "total_reward": float(total_reward),
        "steps_used": int(observation.step_count),
        "max_steps": int(observation.max_steps),
        "done": bool(observation.done),
        "history": history,
    }


def run_all_tasks() -> dict[str, Any]:
    results = {
        "easy": run_task_with_llm("easy", get_easy_elements(), EASY_MAX_STEPS),
        "medium": run_task_with_llm("medium", get_medium_elements(), MEDIUM_MAX_STEPS),
        "hard": run_task_with_llm("hard", get_hard_elements(), HARD_MAX_STEPS),
    }

    summary = {
        "easy": results["easy"]["final_score"],
        "medium": results["medium"]["final_score"],
        "hard": results["hard"]["final_score"],
    }

    return {
        "model": "gpt-4o-mini",
        "summary": summary,
        "results": results,
    }


def run_baseline() -> dict:
    """Alias for run_all_tasks() - hackathon spec compatibility."""
    return run_all_tasks()


if __name__ == "__main__":
    output = run_all_tasks()
    print(json.dumps(output, indent=2))
