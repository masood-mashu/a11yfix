from env.a11y_env import A11yEnv

elements = [
    {"id": "btn1", "type": "button", "attributes": {}}
]

env = A11yEnv(elements)

# Step 0: Reset
state = env.reset()
print("Initial State:", state)

# Step 1: Audit (see violation)
state, reward, done, _ = env.step(("audit",))
print("\nAfter Audit:")
print("Audit:", state["audit"])
print("Reward:", reward)

# Step 2: WRONG action (aria-label first)
state, reward, done, _ = env.step(("set_attribute", "btn1", "aria-label", "Click"))
print("\nAfter WRONG action (aria-label first):")
print("Score:", state["score"])
print("Reward:", reward)

# Step 3: CORRECT action (text)
state, reward, done, _ = env.step(("set_attribute", "btn1", "text", "Click Me"))
print("\nAfter CORRECT action (text):")
print("Score:", state["score"])
print("Reward:", reward)