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

## Observability model

- Violations are not included in normal observations.
- Violations are returned only in `audit` action responses.
- Element structure and attributes remain visible as part of the state.

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

Custom project endpoints:

- `GET /tasks`: task list + action schema
- `GET /baseline`: baseline run across easy/medium/hard tasks
- `POST /grader`: score a submitted action sequence

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
