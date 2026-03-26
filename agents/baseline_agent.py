from env.a11y_env import A11yEnv


class BaselineAgent:
    def __init__(self, env):
        self.env = env

    def run(self):
        state = self.env.reset()
        print("Initial State:", state)

        done = False

        while not done:
            # Step 1: audit
            state, reward, done, _ = self.env.step(("audit",))
            print("\nAudit:", state["audit"], "Reward:", reward)

            violations = state["audit"]

            if not violations:
                state, reward, done, _ = self.env.step(("done",))
                print("\nDone. Reward:", reward)
                break

            # Step 2: fix first violation
            v = violations[0]
            element_id = v["element_id"]
            attr = v["fix"]["attr"]

            # simple value
            value = "fixed"

            action = ("set_attribute", element_id, attr, value)
            state, reward, done, _ = self.env.step(action)

            print(f"\nFixing {v['type']} →", action)
            print("Score:", state["score"], "Reward:", reward)