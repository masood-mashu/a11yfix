from env.a11y_env import A11yAction
from env.violations import detect_violations


VIOLATION_ATTR_MAP = {
    "missing_alt": "alt",
    "missing_label": "aria-label",
    "missing_button_name": "text",
    "missing_lang": "lang",
}


class OptimalAgent:
    """Task-aware rule agent that skips audit and applies direct fixes."""

    def __init__(self, env):
        self.env = env

    def run(self):
        observation = self.env.reset()

        total_reward = 0.0

        # Use deterministic state inspection to avoid spending a step on audit.
        violations = detect_violations(observation.elements)

        for violation in violations:
            if observation.done:
                break

            attr = VIOLATION_ATTR_MAP.get(violation.get("type", ""))
            element_id = violation.get("element_id", "")
            if not attr or not element_id:
                continue

            observation = self.env.step(
                A11yAction(
                    operation="set_attribute",
                    element_id=element_id,
                    attribute=attr,
                    value="fixed",
                )
            )
            total_reward += float(observation.reward or 0.0)

        if not observation.done:
            observation = self.env.step(A11yAction(operation="done"))
            total_reward += float(observation.reward or 0.0)

        return {
            "score": observation.score,
            "total_reward": round(total_reward, 3),
            "steps": observation.step_count,
        }
