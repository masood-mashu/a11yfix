from agents.optimal_agent import OptimalAgent
from env.a11y_env import A11yEnv


MAX_STEPS = 5


def get_medium_elements():
    return [
        {"id": "img1", "type": "img", "attributes": {}},
        {"id": "btn1", "type": "button", "attributes": {}},
        {"id": "input1", "type": "input", "attributes": {}}
    ]


def run_task():
    elements = get_medium_elements()
    env = A11yEnv(elements, max_steps=MAX_STEPS)
    result = OptimalAgent(env).run()
    return {"score": result["score"], "steps": result["steps"]}