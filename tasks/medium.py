from agents.optimal_agent import OptimalAgent
from env.a11y_env import A11yEnv
from random import Random


MAX_STEPS = 6


def get_medium_elements(seed=None):
    if seed is None:
        return [
            {"id": "img1", "type": "img", "attributes": {}},
            {"id": "btn1", "type": "button", "attributes": {}},
            {"id": "input1", "type": "input", "attributes": {}}
        ]

    rng = Random(seed)
    return [
        {"id": rng.choice(["img1", "imgLead", "imgCard"]), "type": "img", "attributes": {}},
        {"id": rng.choice(["btn1", "btnSearch", "btnCheckout"]), "type": "button", "attributes": {}},
        {"id": rng.choice(["input1", "inputSearch", "inputEmail"]), "type": "input", "attributes": {}}
    ]


def run_task(seed=None):
    elements = get_medium_elements(seed=seed)
    env = A11yEnv(elements, max_steps=MAX_STEPS)
    result = OptimalAgent(env).run()
    return {"score": result["score"], "steps": result["steps"]}
