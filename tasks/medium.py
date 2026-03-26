from env.a11y_env import A11yEnv


def run_task():
    elements = [
        {"id": "img1", "type": "img", "attributes": {}},
        {"id": "btn1", "type": "button", "attributes": {}}
    ]

    env = A11yEnv(elements)

    state = env.reset()
    done = False

    while not done:
        state, _, _, _ = env.step(("audit",))

        if not state["audit"]:
            state, reward, done, _ = env.step(("done",))
            break

        v = state["audit"][0]
        action = ("set_attribute", v["element_id"], v["fix"]["attr"], "fixed")

        state, _, done, _ = env.step(action)

    return state["score"]