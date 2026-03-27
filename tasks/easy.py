from env.a11y_env import A11yAction, A11yEnv


MAX_STEPS = 8


def get_easy_elements():
    return [
        {"id": "img1", "type": "img", "attributes": {}}
    ]


def run_task():
    elements = get_easy_elements()

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

    # 🔧 Fix blindly
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

    # ✅ Finish
    if not observation.done:
        observation = env.step(A11yAction(operation="done"))

    return {
        "score": observation.score,
        "steps": observation.step_count,
    }