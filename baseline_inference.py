import json
from dataclasses import dataclass
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
- missing_alt -> set_attribute with attribute=\"alt\", value=\"Descriptive image\"
- missing_label -> set_attribute with attribute=\"aria-label\", value=\"Form input\"
- missing_button_name -> set_attribute with attribute=\"text\", value=\"Submit\"
- missing_lang -> set_attribute with attribute=\"lang\", value=\"en\"

Respond with ONLY a JSON object and no markdown.
Example:
{\"operation\": \"set_attribute\", \"element_id\": \"img1\", \"attribute\": \"alt\", \"value\": \"Company logo\"}
"""

DEFAULT_MODEL_NAME = "offline-rule-baseline"
VIOLATION_ATTR_MAP = {
    "missing_alt": "alt",
    "missing_label": "aria-label",
    "missing_button_name": "text",
    "missing_lang": "lang",
}

VIOLATION_VALUE_MAP = {
    "missing_alt": "Accessible image",
    "missing_label": "Search field",
    "missing_button_name": "Submit",
    "missing_lang": "en",
}


@dataclass
class LLMRunnerConfig:
    client: OpenAI
    model_name: str


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


def _llm_choose_action(
    violations: list[dict[str, Any]],
    score: float,
    steps_remaining: int,
    runner: LLMRunnerConfig,
) -> A11yAction:
    user_prompt = (
        "Current violations:\n"
        f"{json.dumps(violations, indent=2)}\n\n"
        f"Current score: {score}\n"
        f"Steps remaining: {steps_remaining}\n\n"
        "Choose one next action."
    )

    request_kwargs = {
        "model": runner.model_name,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        response = runner.client.chat.completions.create(
            response_format={"type": "json_object"},
            **request_kwargs,
        )
    except Exception:
        try:
            response = runner.client.chat.completions.create(**request_kwargs)
        except Exception:
            return A11yAction(operation="audit")

    # Be defensive against provider-specific or malformed response shapes.
    choices = response.get("choices") if isinstance(response, dict) else getattr(response, "choices", None)
    if not isinstance(choices, (list, tuple)) or not choices:
        return A11yAction(operation="audit")

    first_choice = choices[0]
    if isinstance(first_choice, dict):
        message = first_choice.get("message")
        content = message.get("content") if isinstance(message, dict) else None
    else:
        message = getattr(first_choice, "message", None)
        content = getattr(message, "content", None) if message is not None else None

    if not isinstance(content, str):
        return A11yAction(operation="audit")

    return _parse_llm_action(content or "{}")


def _offline_run_task(task_name: str, elements: list[dict[str, Any]], max_steps: int) -> dict[str, Any]:
    env = A11yEnv(elements, max_steps=max_steps)
    observation = env.reset()

    total_reward = 0.0
    history: list[dict[str, Any]] = []

    observation = env.step(A11yAction(operation="audit"))
    total_reward += float(observation.reward or 0.0)
    history.append(
        {
            "step": int(observation.step_count),
            "action": {"operation": "audit"},
            "reward": float(observation.reward or 0.0),
            "score": float(observation.score),
            "done": bool(observation.done),
        }
    )

    violations = list(observation.audit)
    for violation in violations:
        if observation.done:
            break

        attr = VIOLATION_ATTR_MAP.get(violation.get("type", ""))
        if not attr:
            continue

        action = A11yAction(
            operation="set_attribute",
            element_id=str(violation.get("element_id", "")),
            attribute=attr,
            value=VIOLATION_VALUE_MAP.get(str(violation.get("type", "")), "Accessible value"),
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

    if not observation.done:
        done_action = A11yAction(operation="done")
        observation = env.step(done_action)
        total_reward += float(observation.reward or 0.0)
        history.append(
            {
                "step": int(observation.step_count),
                "action": done_action.model_dump(),
                "reward": float(observation.reward or 0.0),
                "score": float(observation.score),
                "done": bool(observation.done),
            }
        )

    return {
        "task": task_name,
        "mode": "offline_fallback",
        "final_score": float(observation.score),
        "total_reward": float(total_reward),
        "steps_used": int(observation.step_count),
        "max_steps": int(observation.max_steps),
        "done": bool(observation.done),
        "history": history,
    }


def run_task_with_runner(
    task_name: str,
    elements: list[dict[str, Any]],
    max_steps: int,
    runner: LLMRunnerConfig | None = None,
) -> dict[str, Any]:
    if runner is None:
        return _offline_run_task(task_name, elements, max_steps)

    env = A11yEnv(elements, max_steps=max_steps)
    observation = env.reset()

    total_reward = 0.0
    history: list[dict[str, Any]] = []

    observation = env.step(A11yAction(operation="audit"))
    total_reward += float(observation.reward or 0.0)
    history.append(
        {
            "step": int(observation.step_count),
            "action": {"operation": "audit"},
            "reward": float(observation.reward or 0.0),
            "score": float(observation.score),
            "done": bool(observation.done),
        }
    )

    violations = list(observation.audit)
    attr_violation_map = {value: key for key, value in VIOLATION_ATTR_MAP.items()}

    while not observation.done and violations:
        steps_remaining = max(0, observation.max_steps - observation.step_count)

        action = _llm_choose_action(
            violations=violations,
            score=float(observation.score),
            steps_remaining=steps_remaining,
            runner=runner,
        )

        if action.operation != "set_attribute":
            candidate = violations[0]
            action = A11yAction(
                operation="set_attribute",
                element_id=str(candidate.get("element_id", "")),
                attribute=VIOLATION_ATTR_MAP.get(str(candidate.get("type", "")), ""),
                value=VIOLATION_VALUE_MAP.get(str(candidate.get("type", "")), "Accessible value"),
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

        if action.operation == "set_attribute":
            fixed_violation_type = attr_violation_map.get(action.attribute, "")
            violations = [
                violation
                for violation in violations
                if not (
                    str(violation.get("element_id", "")) == action.element_id
                    and str(violation.get("type", "")) == fixed_violation_type
                )
            ]

    if not observation.done:
        done_action = A11yAction(operation="done")
        observation = env.step(done_action)
        total_reward += float(observation.reward or 0.0)
        history.append(
            {
                "step": int(observation.step_count),
                "action": done_action.model_dump(),
                "reward": float(observation.reward or 0.0),
                "score": float(observation.score),
                "done": bool(observation.done),
            }
        )

    return {
        "task": task_name,
        "mode": "llm",
        "final_score": float(observation.score),
        "total_reward": float(total_reward),
        "steps_used": int(observation.step_count),
        "max_steps": int(observation.max_steps),
        "done": bool(observation.done),
        "history": history,
    }


def run_all_tasks(
    runner: LLMRunnerConfig | None = None,
    *,
    model_name: str | None = None,
) -> dict[str, Any]:
    results = {
        "easy": run_task_with_runner("easy", get_easy_elements(), EASY_MAX_STEPS, runner=runner),
        "medium": run_task_with_runner("medium", get_medium_elements(), MEDIUM_MAX_STEPS, runner=runner),
        "hard": run_task_with_runner("hard", get_hard_elements(), HARD_MAX_STEPS, runner=runner),
    }

    summary = {
        "easy": results["easy"]["final_score"],
        "medium": results["medium"]["final_score"],
        "hard": results["hard"]["final_score"],
    }

    return {
        "model": model_name or DEFAULT_MODEL_NAME,
        "mode": "llm" if runner is not None else "offline_fallback",
        "summary": summary,
        "results": results,
    }


def run_baseline() -> dict[str, Any]:
    """Alias for the reproducible local baseline used by the API."""
    return run_all_tasks()


if __name__ == "__main__":
    print(json.dumps(run_baseline(), indent=2))
