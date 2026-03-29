from agents.optimal_agent import OptimalAgent
from env.a11y_env import A11yEnv
from random import Random


MAX_STEPS = 8


def get_easy_elements(seed=None):
    if seed is None:
        return [
            {"id": "img1", "type": "img", "attributes": {}}
        ]

    rng = Random(seed)
    image_id = rng.choice(["img1", "imgHero", "imgPromo", "imgBanner"])
    return [
        {"id": image_id, "type": "img", "attributes": {}}
    ]


def run_task(seed=None):
    elements = get_easy_elements(seed=seed)
    env = A11yEnv(elements, max_steps=MAX_STEPS)
    result = OptimalAgent(env).run()
    return {"score": result["score"], "steps": result["steps"]}
