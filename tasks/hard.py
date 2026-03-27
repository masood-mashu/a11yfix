from agents.optimal_agent import OptimalAgent
from env.a11y_env import A11yEnv


MAX_STEPS = 8


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
    env = A11yEnv(elements, max_steps=MAX_STEPS)
    result = OptimalAgent(env).run()
    return {"score": result["score"], "steps": result["steps"]}