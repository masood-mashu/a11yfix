from env.a11y_env import A11yEnv


MAX_STEPS = 12


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

    state = env.reset()

    VIOLATION_ATTR_MAP = {
        "missing_alt": "alt",
        "missing_label": "aria-label",
        "missing_button_name": "text",
        "missing_lang": "lang",
    }

    # 🔍 Audit ONCE
    state, _, _, _ = env.step(("audit",))
    violations = state.get("audit", [])

    # 🔧 Fix blindly (will likely run out of steps)
    for v in violations:
        attr = VIOLATION_ATTR_MAP.get(v["type"])
        if attr:
            state, _, done, _ = env.step(("set_attribute", v["element_id"], attr, "fixed"))

    # ✅ Finish
    state, _, _, _ = env.step(("done",))

    return {
        "score": state["score"],
        "steps": state["step_count"],
    }