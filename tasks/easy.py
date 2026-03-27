from agents.optimal_agent import OptimalAgent
from env.a11y_env import A11yEnv


MAX_STEPS = 8


def get_easy_elements():
    return [
        {"id": "img1", "type": "img", "attributes": {}}
    ]


def run_task():
    elements = get_easy_elements()
    env = A11yEnv(elements, max_steps=MAX_STEPS)
    result = OptimalAgent(env).run()
    return {"score": result["score"], "steps": result["steps"]}