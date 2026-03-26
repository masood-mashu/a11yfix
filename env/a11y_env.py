from env.violations import detect_violations
from env.reward import compute_reward


class A11yEnv:
    def __init__(self, elements, max_steps=20):
        self.initial_elements = elements
        self.max_steps = max_steps
        self.reset()

    def reset(self):
        self.elements = [el.copy() for el in self.initial_elements]
        self.step_count = 0

        self.violations = detect_violations(self.elements)
        self.initial_violation_count = len(self.violations)
        self.last_audit = []

        return self._get_state()

    # ✅ NEW (OpenEnv compliance)
    def state(self):
        return self._get_state()

    def _get_state(self):
        return {
            "elements": self.elements,
            "score": self._compute_score(),
            "step_count": self.step_count,
            "max_steps": self.max_steps,
            "audit": self.last_audit
        }

    def _compute_score(self):
        current = len(detect_violations(self.elements))

        if self.initial_violation_count == 0:
            return 1.0

        return round(
            (self.initial_violation_count - current) / self.initial_violation_count,
            2
        )

    def step(self, action):
        self.step_count += 1

        done = False
        action_type = action[0]

        prev_violations = len(detect_violations(self.elements))
        valid_action = True

        # ---------- ACTION HANDLING ----------

        if action_type == "set_attribute":
            _, element_id, attr, value = action

            found = False

            for el in self.elements:
                if el["id"] == element_id:
                    found = True
                    el.setdefault("attributes", {})[attr] = value

            if not found:
                valid_action = False

        elif action_type == "audit":
            self.last_audit = detect_violations(self.elements)

        elif action_type == "done":
            done = True

        else:
            valid_action = False

        curr_violations = len(detect_violations(self.elements))

        # ---------- REWARD ----------
        reward = compute_reward(
            prev_violations,
            curr_violations,
            action_type,
            valid_action
        )

        # ---------- TERMINATION ----------
        if self.step_count >= self.max_steps:
            done = True

        # ✅ NEW (info dict for compliance)
        info = {
            "violations": curr_violations
        }

        return self._get_state(), reward, done, info