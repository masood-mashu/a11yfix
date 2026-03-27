import json

from fastapi import HTTPException
from openenv.core import create_fastapi_app
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from env.a11y_env import A11yAction, A11yEnv, A11yObservation


def A11yEnv_factory():
    from tasks.hard import get_hard_elements, MAX_STEPS as HARD_MAX_STEPS

    return A11yEnv(get_hard_elements(), max_steps=HARD_MAX_STEPS)


app = create_fastapi_app(
    env=A11yEnv_factory,
    action_cls=A11yAction,
    observation_cls=A11yObservation,
)


def _normalize_step_payload(payload: dict) -> dict:
    action_payload = {
        "operation": payload.get("operation", ""),
        "element_id": payload.get("element_id", payload.get("target", "")),
        "attribute": payload.get("attribute", ""),
        "value": payload.get("value", ""),
    }

    normalized_payload = dict(payload)
    normalized_payload.pop("operation", None)
    normalized_payload.pop("element_id", None)
    normalized_payload.pop("target", None)
    normalized_payload.pop("attribute", None)
    normalized_payload.pop("value", None)
    normalized_payload["action"] = action_payload
    return normalized_payload


class StepPayloadCompatibilityMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        if scope.get("method") != "POST" or scope.get("path", "").rstrip("/") != "/step":
            await self.app(scope, receive, send)
            return

        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        content_type = headers.get("content-type", "")
        if "application/json" not in content_type:
            await self.app(scope, receive, send)
            return

        body = b""
        while True:
            message = await receive()
            if message["type"] != "http.request":
                break
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break

        normalized_body = body
        if body:
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = None

            if isinstance(payload, dict) and "action" not in payload and "operation" in payload:
                normalized_body = json.dumps(_normalize_step_payload(payload)).encode("utf-8")

        sent = False

        async def normalized_receive() -> Message:
            nonlocal sent
            if sent:
                return {"type": "http.request", "body": b"", "more_body": False}
            sent = True
            return {"type": "http.request", "body": normalized_body, "more_body": False}

        await self.app(scope, normalized_receive, send)


app.add_middleware(StepPayloadCompatibilityMiddleware)


class GradeAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    action: str = Field(validation_alias=AliasChoices("action", "type", "operation"))
    target: str = Field(default="", validation_alias=AliasChoices("target", "element_id"))
    attribute: str = ""
    value: str = ""


class GradeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    task: str = Field(validation_alias=AliasChoices("task", "task_id"))
    actions: list[GradeAction]


@app.get("/tasks")
def get_tasks():
    return {
        "tasks": ["easy", "medium", "hard"],
        "action_schema": {
            "set_attribute": ["element_id", "attribute", "value"],
            "audit": [],
            "done": [],
        },
    }


@app.get("/baseline")
def run_baseline():
    from tasks.easy import run_task as run_easy
    from tasks.medium import run_task as run_medium
    from tasks.hard import run_task as run_hard

    return {
        "easy": run_easy(),
        "medium": run_medium(),
        "hard": run_hard(),
    }


@app.post("/grader")
def grader(req: GradeRequest):
    from tasks.easy import get_easy_elements, MAX_STEPS as EASY_MAX_STEPS
    from tasks.medium import get_medium_elements, MAX_STEPS as MEDIUM_MAX_STEPS
    from tasks.hard import get_hard_elements, MAX_STEPS as HARD_MAX_STEPS

    task_config = {
        "easy": (get_easy_elements, EASY_MAX_STEPS),
        "medium": (get_medium_elements, MEDIUM_MAX_STEPS),
        "hard": (get_hard_elements, HARD_MAX_STEPS),
    }

    config = task_config.get(req.task)
    if config is None:
        raise HTTPException(status_code=400, detail="Invalid task")

    get_elements, max_steps = config
    env = A11yEnv(get_elements(), max_steps=max_steps)
    observation = env.reset()

    total_reward = 0.0
    done = observation.done

    for act in req.actions:
        action = A11yAction(
            operation=act.action,
            element_id=act.target,
            attribute=act.attribute,
            value=act.value,
        )

        observation = env.step(action)
        total_reward += float(observation.reward or 0.0)
        done = observation.done

        if done:
            break

    return {
        "score": float(observation.score),
        "total_reward": float(total_reward),
        "done": bool(done),
    }