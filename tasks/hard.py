from env.a11y_env import A11yAction, A11yEnv


MAX_STEPS = 8


def get_hard_elements():
    return [
        {"id": "root",   "type": "html",   "attributes": {}},

        {"id": "img1",   "type": "img",    "attributes": {}},
        {"id": "img2",   "type": "img",    "attributes": {}},
        {"id": "img3",   "type": "img",    "attributes": {}},

        {"id": "btn1",   "type": "button", "attributes": {}},
        {"id": "btn2",   "type": "button", "attributes": {}},

        {"id": "input1", "type": "input",  "attributes": {}},
        {"id": "input2", "type": "input",  "attributes": {}},
    ]


def run_task():
    elements = get_hard_elements()

    # 🔥 very tight steps → baseline struggles
    env = A11yEnv(elements, max_steps=MAX_STEPS)

    observation = env.reset()

    VIOLATION_ATTR_MAP = {
        "missing_alt": "alt",
        "missing_label": "aria-label",
        "missing_button_name": "text",
        "missing_lang": "lang",
    }

    # 🔍 Audit ONCE
    observation = env.step(A11yAction(operation="audit"))
    violations = observation.audit

    # 🔧 Fix blindly (will likely run out of steps)
    i = 0
    while not observation.done and i < len(violations):
        v = violations[i]
        i += 1
        attr = VIOLATION_ATTR_MAP.get(v["type"])
        if attr:
            observation = env.step(
                A11yAction(
                    operation="set_attribute",
                    element_id=v["element_id"],
                    attribute=attr,
                    value="fixed",
                )
            )

    return {
        "score": observation.score,
        "steps": observation.step_count,
    }