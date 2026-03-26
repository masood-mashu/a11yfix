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
        state = self.env.reset()
        done = False
        total_reward = 0

        # 🔍 Step 1: Audit ONCE
        state, reward, done, _ = self.env.step(("audit",))
        total_reward += reward

        violations = state.get("audit", [])

        # Mapping: violation → attribute
        VIOLATION_ATTR_MAP = {
            "missing_alt": "alt",
            "missing_label": "aria-label",
            "missing_button_name": "text",
            "missing_lang": "lang",
        }

        # 🔧 Step 2: Fix in order (no re-audit)
        for v in violations:
            if done:
                break

            attr = VIOLATION_ATTR_MAP.get(v["type"])

            if attr:
                action = ("set_attribute", v["element_id"], attr, "fixed")
                state, reward, done, _ = self.env.step(action)
                total_reward += reward

        # ✅ Step 3: Finish
        if not done:
            state, reward, done, _ = self.env.step(("done",))
            total_reward += reward

        return {
            "score": state["score"],
            "total_reward": round(total_reward, 3),
            "steps": state["step_count"]
        }