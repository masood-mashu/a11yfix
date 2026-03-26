from env.a11y_env import A11yEnv


def run_task():
    elements = [
        {"id": "img1", "type": "img", "attributes": {}}
    ]

    env = A11yEnv(elements, max_steps=5)

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

    # 🔧 Fix blindly
    for v in violations:
        attr = VIOLATION_ATTR_MAP.get(v["type"])
        if attr:
            state, _, done, _ = env.step(("set_attribute", v["element_id"], attr, "fixed"))

    # ✅ Finish
    state, _, _, _ = env.step(("done",))

    return state["score"]