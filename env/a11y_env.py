from copy import deepcopy
from typing import Any

from openenv.core import Action, Environment, Observation, State
from pydantic import Field

from env.reward import compute_reward
from env.violations import detect_violations


class A11yAction(Action):
    operation: str
    element_id: str = ""
    attribute: str = ""
    value: str = ""


class A11yObservation(Observation):
    elements: list[dict]
    score: float
    step_count: int
    max_steps: int
    audit: list = Field(default_factory=list)

    # Backward-compatible helpers for existing dict-like call sites.
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


try:
    A11yEnvironmentBase = Environment[A11yAction, A11yObservation]
except TypeError:
    A11yEnvironmentBase = Environment[A11yAction, A11yObservation, State]


class A11yEnv(A11yEnvironmentBase):
    def __init__(self, elements, max_steps=20):
        super().__init__()
        # Store an immutable episode template to prevent cross-episode drift.
        self.initial_elements = deepcopy(elements)
        self.max_steps = max_steps
        self._terminated = False
        self.reset()

    def reset(self, seed=None, episode_id=None, **kwargs) -> A11yObservation:
        self.elements = deepcopy(self.initial_elements)
        self.step_count = 0
        self._terminated = False

        self.violations = detect_violations(self.elements)
        self.initial_violation_count = len(self.violations)

        self._last_observation = self._get_observation()
        return self._last_observation

    @property
    def state(self) -> A11yObservation:
        return self._get_observation(done=self._terminated, reward=0.0, audit=[])

    def _get_observation(self, done: bool = False, reward=None, audit=None) -> A11yObservation:
        reward_value = 0.0 if reward is None else float(reward)
        return A11yObservation(
            elements=deepcopy(self.elements),
            score=self._compute_score(),
            step_count=self.step_count,
            max_steps=self.max_steps,
            audit=deepcopy(audit or []),
            done=done,
            reward=reward_value,
        )

    def _compute_score(self):
        current = len(detect_violations(self.elements))

        if self.initial_violation_count == 0:
            return 1.0

        return round(
            (self.initial_violation_count - current) / self.initial_violation_count,
            2,
        )

    def _normalize_action(self, action: A11yAction) -> A11yAction:
        if isinstance(action, A11yAction):
            return action

        if isinstance(action, tuple) and len(action) > 0:
            operation = action[0]
            if operation == "set_attribute":
                element_id = action[1] if len(action) > 1 else ""
                attribute = action[2] if len(action) > 2 else ""
                value = action[3] if len(action) > 3 else ""
                return A11yAction(
                    operation=operation,
                    element_id=element_id,
                    attribute=attribute,
                    value=value,
                )

            if operation in {"audit", "done"}:
                return A11yAction(operation=operation)

        return A11yAction(operation="invalid")

    def step(self, action: A11yAction, **kwargs) -> A11yObservation:
        if self._terminated:
            # Terminal latch: keep returning the same terminal state.
            return self._last_observation.model_copy(deep=True)

        action = self._normalize_action(action)
        self.step_count += 1

        done = False
        action_type = action.operation

        prev_violations = len(detect_violations(self.elements))
        valid_action = True

        if action_type == "set_attribute":
            found = False

            for el in self.elements:
                if el["id"] == action.element_id:
                    found = True
                    el.setdefault("attributes", {})[action.attribute] = action.value

            if not found:
                valid_action = False

        elif action_type == "audit":
            audit_result = detect_violations(self.elements)
            reward = compute_reward(
                prev_violations,
                prev_violations,
                action_type,
                True,
            )

            if self.step_count >= self.max_steps:
                done = True

            obs = self._get_observation(done=done, reward=reward, audit=audit_result)
            if done:
                self._terminated = True
            self._last_observation = obs
            return obs

        elif action_type == "done":
            done = True

        else:
            valid_action = False

        curr_violations = len(detect_violations(self.elements))

        reward = compute_reward(
            prev_violations,
            curr_violations,
            action_type,
            valid_action,
        )

        if self.step_count >= self.max_steps:
            done = True

        obs = self._get_observation(done=done, reward=reward, audit=[])
        if done:
            self._terminated = True
        self._last_observation = obs
        return obs


def create_default_env() -> "A11yEnv":
    from tasks.hard import MAX_STEPS as HARD_MAX_STEPS
    from tasks.hard import get_hard_elements

    return A11yEnv(get_hard_elements(), max_steps=HARD_MAX_STEPS)