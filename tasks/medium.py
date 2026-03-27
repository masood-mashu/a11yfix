from env.a11y_env import A11yAction, A11yEnv


MAX_STEPS = 3


def get_medium_elements():
    return [
        {"id": "img1", "type": "img", "attributes": {}},
        {"id": "btn1", "type": "button", "attributes": {}},
        {"id": "input1", "type": "input", "attributes": {}}
    ]


def run_task():
    elements = get_medium_elements()

    # 🔥 tighter steps → creates imperfection
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

    # 🔧 Fix blindly (no re-audit)
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