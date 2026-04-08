from env.a11y_env import A11yAction, A11yEnv


def pretty_print(title, data):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)
    print(data)


def print_elements(elements):
    for el in elements:
        print(el)


elements = [
    {"id": "root", "type": "html", "attributes": {}},
    {"id": "img1", "type": "img", "attributes": {}},
    {"id": "btn1", "type": "button", "attributes": {}},
]

env = A11yEnv(elements)

print("\nA11yFix Demo Starting...\n")

obs = env.reset()

pretty_print("Initial State", obs)

print("\nInitial DOM:")
print_elements(obs.elements)

tried_wrong = False
VIOLATION_ATTR_MAP = {
    "missing_alt": "alt",
    "missing_label": "aria-label",
    "missing_button_name": "text",
    "missing_lang": "lang",
}
VIOLATION_VALUE_MAP = {
    "missing_alt": "Accessible image",
    "missing_label": "Search field",
    "missing_button_name": "Submit",
    "missing_lang": "en",
}

while not obs.done:
    obs = env.step(A11yAction(operation="audit"))
    pretty_print("Audit Result", obs.audit)
    print("Reward:", obs.reward)

    if not obs.audit:
        obs = env.step(A11yAction(operation="done"))
        print("\nDONE - Final Reward:", obs.reward)

        print("\nSummary:")
        print(f"Steps taken: {obs.step_count}")
        print(f"Final Score: {obs.score}")
        break

    v = obs.audit[0]

    if v["type"] == "missing_button_name" and not tried_wrong:
        wrong_action = A11yAction(
            operation="set_attribute",
            element_id=v["element_id"],
            attribute="class",
            value="highlight",
        )

        obs = env.step(wrong_action)

        print("\nTrying WRONG fix (non-accessibility attribute) ->", wrong_action)
        print("Score:", obs.score, "| Reward:", obs.reward)

        tried_wrong = True
        continue

    action = A11yAction(
        operation="set_attribute",
        element_id=v["element_id"],
        attribute=VIOLATION_ATTR_MAP[v["type"]],
        value=VIOLATION_VALUE_MAP[v["type"]],
    )

    obs = env.step(action)

    print(f"\nFixing {v['type']} -> {action}")
    print("Score:", obs.score, "| Reward:", obs.reward)

    print("\nUpdated DOM:")
    print_elements(obs.elements)
