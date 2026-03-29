from env.a11y_env import A11yEnv

elements = [
    {"id": "btn1", "type": "button", "attributes": {}}
]

env = A11yEnv(elements)

# Step 0: Reset
obs = env.reset()
print("Initial State:", obs)

# Step 1: Audit (see violation)
obs = env.step(("audit",))
print("\nAfter Audit:")
print("Audit:", obs["audit"])
print("Reward:", obs.reward)

# Step 2: WRONG action (non-accessibility attribute)
obs = env.step(("set_attribute", "btn1", "class", "highlight"))
print("\nAfter WRONG action (class first):")
print("Score:", obs["score"])
print("Reward:", obs.reward)

# Step 3: CORRECT action (text)
obs = env.step(("set_attribute", "btn1", "text", "Click Me"))
print("\nAfter CORRECT action (text):")
print("Score:", obs["score"])
print("Reward:", obs.reward)
