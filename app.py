from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional

from env.a11y_env import A11yEnv
from tasks.easy import run_task as easy
from tasks.medium import run_task as medium
from tasks.hard import run_task as hard

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

    if req.task == "easy":
        elements = [
            {"id": "img_1", "type": "img", "attributes": {}}
        ]

    elif req.task == "medium":
        elements = [
            {"id": "img_1", "type": "img", "attributes": {}},
            {"id": "btn_1", "type": "button", "attributes": {}}
        ]

    elif req.task == "hard":
        elements = [
            {"id": "root", "type": "html", "attributes": {}},
            {"id": "img_1", "type": "img", "attributes": {}},
            {"id": "btn_1", "type": "button", "attributes": {}}
        ]

    else:
        return {"error": "Invalid task"}

    env = A11yEnv(elements)
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