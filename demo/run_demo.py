import time
from env.a11y_env import A11yEnv


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

state = env.reset()

pretty_print("Initial State", state)

print("\n🧾 Initial DOM:")
print_elements(state["elements"])

done = False
tried_wrong = False   # 👈 ensures wrong action runs only once
VIOLATION_ATTR_MAP = {
    "missing_alt": "alt",
    "missing_label": "aria-label",
    "missing_button_name": "text",
    "missing_lang": "lang",
}

while not done:

    # ---------- AUDIT ----------
    state, reward, done, _ = env.step(("audit",))
    pretty_print("🔍 Audit Result", state["audit"])
    print("Reward:", reward)

    if not state["audit"]:
        state, reward, done, _ = env.step(("done",))
        print("\n✅ DONE — Final Reward:", reward)

        print("\n📊 Summary:")
        print(f"Steps taken: {state['step_count']}")
        print(f"Final Score: {state['score']}")
        break

    v = state["audit"][0]

    # ---------- WRONG ACTION (ONLY ONCE) ----------
    if v["type"] == "missing_button_name" and not tried_wrong:
        wrong_action = ("set_attribute", v["element_id"], "aria-label", "wrong")

        state, reward, done, _ = env.step(wrong_action)

        print("\n❌ Trying WRONG fix →", wrong_action)
        print("📈 Score:", state["score"], "| Reward:", reward)

        tried_wrong = True
        continue   # 👈 go back to audit again

    # ---------- CORRECT ACTION ----------
    action = ("set_attribute", v["element_id"], VIOLATION_ATTR_MAP[v["type"]], "fixed")

    state, reward, done, _ = env.step(action)

    print(f"\n🔧 Fixing {v['type']} → {action}")
    print("📈 Score:", state["score"], "| Reward:", reward)

    print("\n🧾 Updated DOM:")
    print_elements(state["elements"])