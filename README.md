---
title: A11yFix
emoji: "🛠️"
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
pinned: false
---

# A11yFix: Web Accessibility Repair Lab (OpenEnv)

A11yFix is an OpenEnv-style reinforcement learning environment where agents repair accessibility issues in a simplified JSON DOM.

Agents interact through a small action API and are scored by how many violations they resolve within a step budget.

## What the environment does

- Represents a DOM-like state as JSON elements.
- Supports hidden violation discovery via an explicit `audit` action.
- Supports iterative repair with `set_attribute`.
- Uses shaped rewards to encourage valid, effective fixes.
- Ends when agent submits `done` or step budget is exhausted.

## Action API (implemented)

- `set_attribute(element_id, attribute, value)`
- `audit()`
- `done()`

## Action space (formal)

- Type: discrete operation + optional string arguments
- Canonical shape (OpenEnv `A11yAction`):
	- `operation: str`
	- `element_id: str = ""`
	- `attribute: str = ""`
	- `value: str = ""`
- Valid operations:
	- `audit`
	- `set_attribute`
	- `done`

Examples:

```json
{ "operation": "audit" }
```

```json
{ "operation": "set_attribute", "element_id": "img1", "attribute": "alt", "value": "Company logo" }
```

```json
{ "operation": "done" }
```

## Observability model

- Violations are not included in normal observations.
- Violations are returned only in `audit` action responses.
- Element structure and attributes remain visible as part of the state.

## Observation space (formal)

- OpenEnv response payload includes:
	- `observation.elements: list[dict]`
	- `observation.score: float` (normalized, `0.0` to `1.0`)
	- `observation.step_count: int`
	- `observation.max_steps: int`
	- `observation.audit: list` (non-empty only for `audit` action)
	- `reward: float`
	- `done: bool`

Notes:

- `audit` exposes hidden violations but consumes one environment step.
- `done` can terminate early; final score is based on violation reduction.

## Violation types currently modeled

- Missing image alt text (`missing_alt`)
- Missing input label (`missing_label`)
- Missing button text name (`missing_button_name`)
- Missing document language (`missing_lang`)

## Reward model (current)

- Positive reward for reducing violation count.
- Mild penalty for no-op edits and `audit` usage.
- Strong penalty for regressions and invalid actions.
- `done` gives strong positive reward only when all violations are fixed.

## Endpoints

OpenEnv app:

- Standard OpenEnv endpoints are provided by `create_fastapi_app(...)`.

`POST /step` payloads accepted:

- Canonical OpenEnv shape: `{ "action": { "operation": "audit" } }` — **used by OpenAPI schema and standard clients**
- Backward-compatible flat shape: `{ "operation": "audit" }` — compatibility layer for simplified payloads

_Note: The OpenAPI schema (`/openapi.json`) reflects the canonical form. Flat payloads are supported at runtime but not exposed in the OpenAPI schema._

Custom project endpoints:

- `GET /tasks`: task list + action schema
- `GET /baseline`: baseline run across easy/medium/hard tasks
- `POST /grader`: score a submitted action sequence

## Tasks and difficulty

| Task | Violations at reset | Step budget | Difficulty intent |
|---|---:|---:|---|
| Easy | 1 | 8 | Basic single-fix flow |
| Medium | 3 | 5 | Tight budget, requires efficient sequence |
| Hard | 8 | 12 | Multi-element repair under full-budget pressure |

Current task sources:

- `tasks/easy.py`
- `tasks/medium.py`
- `tasks/hard.py`

## Baseline scores (current)

`GET /baseline` and `python -m tasks.run_all_tasks` currently report:

| Task | Score | Steps used |
|---|---:|---:|
| Easy | 1.0 | 1 |
| Medium | 1.0 | 4 |
| Hard | 1.0 | 9 |

Interpretation:

- Baseline uses a task-aware optimal strategy for this benchmark configuration.
- Medium and hard still remain useful for model evaluation because generic agents can waste steps (for example, unnecessary audit or incorrect attribute guesses).

### `/grader` payload examples (current schema)

Valid example (returns `200`):

```json
{
	"task": "easy",
	"actions": [
		{
			"action": "audit",
			"target": "",
			"attribute": "",
			"value": ""
		},
		{
			"action": "set_attribute",
			"target": "img1",
			"attribute": "alt",
			"value": "A scenic mountain view"
		}
	]
}
```

Alias-compatible example (also returns `200`):

```json
{
	"task_id": "easy",
	"actions": [
		{
			"type": "audit"
		},
		{
			"type": "set_attribute",
			"element_id": "img1",
			"attribute": "alt",
			"value": "A scenic mountain view"
		}
	]
}
```

Truly invalid example (returns `422`, missing required action field):

```json
{
	"task": "easy",
	"actions": [
		{
			"target": "img1",
			"attribute": "alt",
			"value": "A scenic mountain view"
		}
	]
}
```

## Local run

```bash
python -m uvicorn app:app --host 0.0.0.0 --port 7860
uvicorn app:app --host 0.0.0.0 --port 7860
```

## Useful checks

```bash
python test_env.py
python -m tasks.run_all_tasks
python demo/run_demo.py
python baseline_inference.py
```

## Docker

```bash
docker build -t a11yfix .
docker run -p 7860:7860 a11yfix
```

## Why this project is useful

A11yFix turns accessibility from static detection into sequential decision-making, making it a practical benchmark for repair-oriented agents.
