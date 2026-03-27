from env.a11y_env import A11yAction, A11yEnv


def pretty_print(title, data):
    print("\n" + "="*50)
    print(title)
    print("="*50)
    print(data)


def print_elements(elements):
    for el in elements:
        print(el)


elements = [
    {"id": "root", "type": "html", "attributes": {}},
    {"id": "img1", "type": "img", "attributes": {}},
    {"id": "btn1", "type": "button", "attributes": {}}
]

env = A11yEnv(elements)

print("\n🚀 A11yFix Demo Starting...\n")

obs = env.reset()

pretty_print("Initial State", obs)

print("\n🧾 Initial DOM:")
print_elements(obs.elements)

tried_wrong = False   # 👈 ensures wrong action runs only once
VIOLATION_ATTR_MAP = {
    "missing_alt": "alt",
    "missing_label": "aria-label",
    "missing_button_name": "text",
    "missing_lang": "lang",
}

while not obs.done:

    # ---------- AUDIT ----------
    obs = env.step(A11yAction(operation="audit"))
    pretty_print("🔍 Audit Result", obs.audit)
    print("Reward:", obs.reward)

    if not obs.audit:
        obs = env.step(A11yAction(operation="done"))
        print("\n✅ DONE — Final Reward:", obs.reward)

        print("\n📊 Summary:")
        print(f"Steps taken: {obs.step_count}")
        print(f"Final Score: {obs.score}")
        break

    v = obs.audit[0]

    # ---------- WRONG ACTION (ONLY ONCE) ----------
    if v["type"] == "missing_button_name" and not tried_wrong:
        wrong_action = A11yAction(
            operation="set_attribute",
            element_id=v["element_id"],
            attribute="aria-label",
            value="wrong",
        )

        obs = env.step(wrong_action)

        print("\n❌ Trying WRONG fix →", wrong_action)
        print("📈 Score:", obs.score, "| Reward:", obs.reward)

        tried_wrong = True
        continue   # 👈 go back to audit again

    # ---------- CORRECT ACTION ----------
    action = A11yAction(
        operation="set_attribute",
        element_id=v["element_id"],
        attribute=VIOLATION_ATTR_MAP[v["type"]],
        value="fixed",
    )

    obs = env.step(action)

    print(f"\n🔧 Fixing {v['type']} → {action}")
    print("📈 Score:", obs.score, "| Reward:", obs.reward)

    print("\n🧾 Updated DOM:")
    print_elements(obs.elements)