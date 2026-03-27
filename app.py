from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional

from env.a11y_env import A11yEnv
from tasks.easy import run_task as easy, get_easy_elements, MAX_STEPS as EASY_MAX_STEPS
from tasks.medium import run_task as medium, get_medium_elements, MAX_STEPS as MEDIUM_MAX_STEPS
from tasks.hard import run_task as hard, get_hard_elements, MAX_STEPS as HARD_MAX_STEPS

# ✅ app defined
app = FastAPI()


# -------------------------------
# MODELS
# -------------------------------
class Action(BaseModel):
    action: str
    target: Optional[str] = None
    attribute: Optional[str] = None
    value: Optional[str] = None


class GradeRequest(BaseModel):
    task: str
    actions: List[Action]


# -------------------------------
# /tasks
# -------------------------------
@app.get("/tasks")
def get_tasks():
    return {
        "tasks": ["easy", "medium", "hard"],
        "action_schema": {
            "set_attribute": ["element_id", "attr", "value"],
            "audit": [],
            "done": []
        }
    }


# -------------------------------
# /baseline
# -------------------------------
@app.get("/baseline")
def run_baseline():
    return {
        "easy": easy(),
        "medium": medium(),
        "hard": hard()
    }


# -------------------------------
# /grader
# -------------------------------
@app.post("/grader")
def grader(req: GradeRequest):
    task_config = {
        "easy": (get_easy_elements, EASY_MAX_STEPS),
        "medium": (get_medium_elements, MEDIUM_MAX_STEPS),
        "hard": (get_hard_elements, HARD_MAX_STEPS),
    }

    config = task_config.get(req.task)
    if config is None:
        return {"error": "Invalid task"}

    get_elements, max_steps = config
    env = A11yEnv(get_elements(), max_steps=max_steps)
    state = env.reset()

    total_reward = 0
    done = False

    for act in req.actions:
        raw = act.model_dump()

        if raw["action"] == "set_attribute":
            action_tuple = (
                "set_attribute",
                raw.get("target"),
                raw.get("attribute"),
                raw.get("value")
            )

        elif raw["action"] == "audit":
            action_tuple = ("audit",)

        elif raw["action"] == "done":
            action_tuple = ("done",)

        else:
            continue

        state, reward, done, _ = env.step(action_tuple)
        total_reward += reward

        if done:
            break

    return {
        "score": state.get("score", 0) if isinstance(state, dict) else 0,
        "total_reward": total_reward,
        "done": done
    }