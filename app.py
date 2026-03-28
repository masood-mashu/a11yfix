import json
import time
from contextvars import ContextVar
from http.cookies import SimpleCookie
from typing import Protocol
from uuid import uuid4

from fastapi import HTTPException
from openenv.core import create_fastapi_app
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from env.a11y_env import A11yAction, A11yEnv, A11yObservation, A11yState


SESSION_COOKIE_NAME = "a11yfix_session_id"
CURRENT_SESSION_ID: ContextVar[str | None] = ContextVar("a11yfix_session_id", default=None)
SESSION_TTL_SECONDS = 30 * 60
MAX_ACTIVE_SESSIONS = 128


def create_default_a11y_env() -> A11yEnv:
    from tasks.hard import get_hard_elements, MAX_STEPS as HARD_MAX_STEPS

    return A11yEnv(get_hard_elements(), max_steps=HARD_MAX_STEPS)


class SessionBoundEnvProxy:
    def __init__(self, env: A11yEnv):
        self._env = env

    def __getattr__(self, name: str):
        return getattr(self._env, name)

    def close(self) -> None:
        # openenv-core closes after every HTTP call; keep the real env alive
        # until the session manager explicitly evicts it.
        return None


class EnvHandle(Protocol):
    def reset(self, *args, **kwargs): ...
    def step(self, *args, **kwargs): ...
    def close(self) -> None: ...


class SessionEnvManager:
    def __init__(
        self,
        *,
        ttl_seconds: int = SESSION_TTL_SECONDS,
        max_sessions: int = MAX_ACTIVE_SESSIONS,
        clock=time.monotonic,
    ):
        self._envs: dict[str, A11yEnv] = {}
        self._last_access: dict[str, float] = {}
        self._ttl_seconds = ttl_seconds
        self._max_sessions = max_sessions
        self._clock = clock

    def get_current_env(self) -> EnvHandle:
        session_id = CURRENT_SESSION_ID.get()
        if not session_id:
            # Fallback for non-request call sites.
            return create_default_a11y_env()

        self._evict_expired_sessions()
        env = self._envs.get(session_id)
        if env is None:
            self._ensure_capacity()
            env = create_default_a11y_env()
            self._envs[session_id] = env
        self._last_access[session_id] = self._clock()
        return SessionBoundEnvProxy(env)

    def get_current_state(self) -> A11yState:
        session_id = CURRENT_SESSION_ID.get()
        if not session_id:
            return create_default_a11y_env().state

        self._evict_expired_sessions()
        env = self._envs.get(session_id)
        if env is None:
            self._ensure_capacity()
            env = create_default_a11y_env()
            self._envs[session_id] = env
        self._last_access[session_id] = self._clock()
        return env.state

    def session_count(self) -> int:
        self._evict_expired_sessions()
        return len(self._envs)

    def reset_for_tests(self) -> None:
        for session_id in list(self._envs):
            self._evict_session(session_id)

    def _evict_expired_sessions(self) -> None:
        cutoff = self._clock() - self._ttl_seconds
        expired = [
            session_id
            for session_id, last_access in self._last_access.items()
            if last_access <= cutoff
        ]
        for session_id in expired:
            self._evict_session(session_id)

    def _ensure_capacity(self) -> None:
        if len(self._envs) < self._max_sessions:
            return

        cutoff = self._clock() - self._ttl_seconds
        stale_sessions = [
            session_id
            for session_id, last_access in self._last_access.items()
            if last_access <= cutoff
        ]
        candidates = stale_sessions or list(self._last_access)
        lru_session = min(candidates, key=lambda session_id: self._last_access[session_id])
        self._evict_session(lru_session)

    def _evict_session(self, session_id: str) -> None:
        env = self._envs.pop(session_id, None)
        self._last_access.pop(session_id, None)
        if env is not None:
            try:
                super(A11yEnv, env).close()
            except AttributeError:
                close = getattr(env, "close", None)
                if callable(close):
                    close()


session_env_manager = SessionEnvManager()


app = create_fastapi_app(
    env=session_env_manager.get_current_env,
    action_cls=A11yAction,
    observation_cls=A11yObservation,
)

# openenv-core registers /state with the base State response model, which strips
# environment-specific fields from our richer state payload. Replace only that
# route with a typed local handler while keeping the session-managed env flow.
app.router.routes = [
    route
    for route in app.router.routes
    if not (getattr(route, "path", None) == "/state" and "GET" in getattr(route, "methods", set()))
]


@app.get("/state", response_model=A11yState, tags=["State Management"])
def get_state():
    return session_env_manager.get_current_state()

class SessionContextMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        cookie_header = headers.get("cookie", "")
        cookies = SimpleCookie()
        if cookie_header:
            cookies.load(cookie_header)

        session_id = cookies.get(SESSION_COOKIE_NAME).value if SESSION_COOKIE_NAME in cookies else None
        should_set_cookie = session_id is None
        if session_id is None:
            session_id = str(uuid4())

        token = CURRENT_SESSION_ID.set(session_id)

        async def session_send(message: Message):
            if should_set_cookie and message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers.append(
                    (
                        b"set-cookie",
                        f"{SESSION_COOKIE_NAME}={session_id}; Path=/; HttpOnly; SameSite=lax".encode("latin-1"),
                    )
                )
                message["headers"] = response_headers
            await send(message)

        try:
            await self.app(scope, receive, session_send)
        finally:
            CURRENT_SESSION_ID.reset(token)


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
app.add_middleware(SessionContextMiddleware)


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
    from baseline_inference import run_all_tasks
    return run_all_tasks()


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
