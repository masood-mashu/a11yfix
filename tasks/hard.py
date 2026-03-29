from agents.optimal_agent import OptimalAgent
from env.a11y_env import A11yEnv
from random import Random


MAX_STEPS = 10


def get_hard_elements(seed=None):
    if seed is None:
        return [
            {"id": "root",   "type": "html",   "attributes": {}},
            {"id": "img1",   "type": "img",    "attributes": {}},
            {"id": "img2",   "type": "img",    "attributes": {}},
            {"id": "img3",   "type": "img",    "attributes": {}},
            {"id": "img4",   "type": "img",    "attributes": {}},
            {"id": "btn1",   "type": "button", "attributes": {}},
            {"id": "btn2",   "type": "button", "attributes": {}},
            {"id": "input1", "type": "input",  "attributes": {}},
            {"id": "input2", "type": "input",  "attributes": {}},
        ]

    rng = Random(seed)
    image_ids = rng.sample(["img1", "img2", "img3", "img4", "imgHero", "imgPromo"], 4)
    button_ids = rng.sample(["btn1", "btn2", "btn3", "btnSearch", "btnCheckout"], 2)
    input_ids = rng.sample(["input1", "input2", "input3", "inputSearch", "inputEmail"], 2)

    return (
        [{"id": "root", "type": "html", "attributes": {}}]
        + [{"id": element_id, "type": "img", "attributes": {}} for element_id in image_ids]
        + [{"id": element_id, "type": "button", "attributes": {}} for element_id in button_ids]
        + [{"id": element_id, "type": "input", "attributes": {}} for element_id in input_ids]
    )


def run_task(seed=None):
    elements = get_hard_elements(seed=seed)
    env = A11yEnv(elements, max_steps=MAX_STEPS)
    result = OptimalAgent(env).run()
    return {"score": result["score"], "steps": result["steps"]}
