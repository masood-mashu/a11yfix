from env.a11y_env import A11yAction


class BaselineAgent:
    """
    Simple rule-based baseline agent.

    Behavior:
    - Audits ONLY once
    - Fixes violations in order
    - Does NOT re-audit
    - May run out of steps on harder tasks

    This creates meaningful score differences across tasks.
    """

    def __init__(self, env):
        self.env = env

    def run(self):
        observation = self.env.reset()
        total_reward = 0

        # 🔍 Step 1: Audit ONCE
        observation = self.env.step(A11yAction(operation="audit"))
        total_reward += float(observation.reward or 0.0)

        violations = observation.audit

        # Mapping: violation → attribute
        VIOLATION_ATTR_MAP = {
            "missing_alt": "alt",
            "missing_label": "aria-label",
            "missing_button_name": "text",
            "missing_lang": "lang",
        }

        # 🔧 Step 2: Fix in order (no re-audit)
        for v in violations:
            if observation.done:
                break

            attr = VIOLATION_ATTR_MAP.get(v["type"])

            if attr:
                action = A11yAction(
                    operation="set_attribute",
                    element_id=v["element_id"],
                    attribute=attr,
                    value="fixed",
                )
                observation = self.env.step(action)
                total_reward += float(observation.reward or 0.0)

        # ✅ Step 3: Finish
        if not observation.done:
            observation = self.env.step(A11yAction(operation="done"))
            total_reward += float(observation.reward or 0.0)

        return {
            "score": observation.score,
            "total_reward": round(total_reward, 3),
            "steps": observation.step_count,
        }