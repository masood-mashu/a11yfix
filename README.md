---
title: A11yFix
emoji: "🛠️"
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
pinned: false
tags:
  - openenv
---

# A11yFix: Web Accessibility Repair Lab (OpenEnv)

A11yFix is an OpenEnv-style reinforcement learning environment where agents repair accessibility issues in a simplified JSON DOM.

Agents interact through a small action API and are scored by how many violations they resolve within a step budget.

Why RL here:

- Accessibility repair is sequential, not just classificatory: agents must decide when to spend a step on discovery, which issue to prioritize next, and when to stop.
- The environment rewards efficient repair under limited budget, which makes it a better fit for agent planning and policy evaluation than a one-shot static classifier benchmark.

## Judge Quick Read

- Real-world task: sequential web accessibility repair over a JSON DOM, not a game or toy environment.
- OpenEnv contract: typed action/observation models, `step()` / `reset()` / `state()` endpoints, `openenv.yaml`, 3 graded tasks.
- Submission readiness: Hugging Face Space deployment, Dockerfile, deterministic offline baseline, session continuity, and regression coverage.
- Review artifacts: [`artifacts/reproducibility_report.json`](artifacts/reproducibility_report.json) captures repeated baseline runs and seeded variant support.

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
	- `observation.score: float` (normalized, strictly bounded inside `(0, 1)`; currently `0.001` to `0.999`)
	- `observation.step_count: int`
	- `observation.max_steps: int`
	- `observation.audit: list` (non-empty only for `audit` action)
	- `reward: float`
	- `done: bool`

Notes:

- `audit` exposes hidden violations but consumes one environment step.
- `done` can terminate early; final score is based on violation reduction.
- Action history entries may include a `metadata` field inherited from openenv-core's Action base class. This field is always empty `{}` and can be ignored.

## Violation types currently modeled

- Missing image alt text (`missing_alt`)
- Missing input label (`missing_label`)
- Missing button text name (`missing_button_name`)
- Missing document language (`missing_lang`)

Fix quality rules:

- Placeholder values such as `fixed`, `test`, or one-character strings do not count as valid repairs.
- Text-based repairs must be meaningful enough to represent a plausible accessible name or description.
- Document language must be a plausible language tag such as `en` or `en-US`.

## Reward model

| Situation | Reward |
|---|---:|
| Valid fix (violation count decreases) | `+0.20` |
| `done` with all violations cleared | `+1.00` |
| `audit` action | `-0.05` |
| No-op edit (violation count unchanged) | `-0.05` |
| Invalid action (unknown element_id or operation) | `-0.10` |
| Regression (violation count increases) | `-0.50` |
| `done` with violations still remaining | `-1.00` |

Reward range: `[-1.0, 1.0]`

## Endpoints

OpenEnv app:

- Standard OpenEnv endpoints are provided by `create_fastapi_app(...)`.

`POST /step` payloads accepted:

- Canonical OpenEnv shape: `{ "action": { "operation": "audit" } }` - **used by OpenAPI schema and standard clients**
- Backward-compatible flat shape: `{ "operation": "audit" }` - compatibility layer for simplified payloads

_Note: The OpenAPI schema (`/openapi.json`) reflects the canonical form. Flat payloads are supported at runtime but not exposed in the OpenAPI schema._

Custom project endpoints:

- `GET /`: health payload (`status`, `version`, `docs`) plus task list and score bounds
- `GET /tasks`: task list + action schema
- `GET /baseline`: baseline run across easy/medium/hard tasks
- `POST /grader`: score a submitted action sequence
- `GET /state`: serialized current environment state

OpenEnv-injected endpoints:

- `POST /mcp`: injected by openenv-core for MCP tool protocol support. Not part of the A11yFix task interface and can be ignored.

## Tasks and difficulty

| Task | Violations at reset | Step budget | Optimal steps (no audit) | Baseline steps (audit-first) |
|---|---:|---:|---:|---:|
| Easy | 1 | 8 | 2 | 3 |
| Medium | 3 | 6 | 4 | 5 |
| Hard | 8 | 10 | 9 | 10 |

**Hard task note:** the audit-first baseline uses all 10 steps exactly (1 audit + 8 fixes + 1 done). An LLM agent that audits first has zero step slack - it must fix every violation without any wasted actions to reach the capped solved score of `0.999`. An agent that skips audit (like `OptimalAgent`) has 1 step of headroom.

Current task sources:

- `tasks/easy.py`
- `tasks/medium.py`
- `tasks/hard.py`

### Violation breakdown by task

**Easy** - 1 violation:
- `img1`: missing alt text

**Medium** - 3 violations:
- `img1`: missing alt text
- `btn1`: missing button name
- `input1`: missing input label

**Hard** - 8 violations:
- `img1`, `img2`, `img3`: missing alt text (x3)
- `btn1`, `btn2`: missing button name (x2)
- `input1`, `input2`: missing input label (x2)
- `root`: missing document language (x1)

## Baseline scores (verified, live + local)

`GET /baseline` and `python baseline_inference.py` report:

| Task | Score | steps_used | Budget | Total reward |
|---|---:|---:|---:|---:|
| Easy | 0.999 | 3 | 8 | 1.15 |
| Medium | 0.999 | 5 | 6 | 1.55 |
| Hard | 0.999 | 10 | 10 | 2.55 |

The baseline is an offline rule-based fallback: audit once, apply deterministic fixes in violation order, submit `done`. It runs in **offline_fallback mode** (rule-based, no LLM required). No API key or `HF_TOKEN` needed to reproduce baseline scores locally with `python baseline_inference.py`. Verified deterministic across 5 repeated runs (`reproducibility_report.py`). Verified live on the public HF Space.

### Baseline step trace

**Easy** (budget=8):
```
step 1: audit                          reward=-0.05  score=0.001
step 2: set_attribute(img1, alt)       reward=+0.20  score=0.999
step 3: done                           reward=+1.00  score=0.999
```

**Medium** (budget=6):
```
step 1: audit                          reward=-0.05  score=0.001
step 2: set_attribute(img1, alt)       reward=+0.20  score=0.333
step 3: set_attribute(btn1, text)      reward=+0.20  score=0.667
step 4: set_attribute(input1, aria-label) reward=+0.20 score=0.999
step 5: done                           reward=+1.00  score=0.999
```

**Hard** (budget=10):
```
step 1:  audit                           reward=-0.05  score=0.001
step 2:  set_attribute(img1, alt)        reward=+0.20  score=0.125
step 3:  set_attribute(img2, alt)        reward=+0.20  score=0.250
step 4:  set_attribute(img3, alt)        reward=+0.20  score=0.375
step 5:  set_attribute(btn1, text)       reward=+0.20  score=0.500
step 6:  set_attribute(btn2, text)       reward=+0.20  score=0.625
step 7:  set_attribute(input1, aria-label) reward=+0.20 score=0.750
step 8:  set_attribute(input2, aria-label) reward=+0.20 score=0.875
step 9:  set_attribute(root, lang)       reward=+0.20  score=0.999
step 10: done                            reward=+1.00  score=0.999
```

## Optional task variation

- The default task snapshots stay fixed so the published API contract and baseline scores remain stable.
- `tasks.easy.get_easy_elements(seed=...)`, `tasks.medium.get_medium_elements(seed=...)`, and `tasks.hard.get_hard_elements(seed=...)` support deterministic seeded variants for deeper evaluation and future benchmark expansion.

## Submission inference entrypoint

The hackathon submission entrypoint is root `inference.py`.

Supported environment variables:

- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`

Live LLM mode uses:

```python
OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
```

If `HF_TOKEN`/`API_KEY` is unavailable, or if the remote completion call fails, `inference.py` falls back to the deterministic offline baseline so the submission run can still complete cleanly.

Run it with:

```bash
python inference.py
```

For local setup, copy values from [`.env.example`](.env.example) into your environment before running the submission path.

## Session policy

- HTTP episode state is stored in memory per client session.
- Default session TTL is 30 minutes.
- Maximum active sessions is 128.
- Eviction is stale least-recently-used first, then least-recently-used if no stale session exists.

## Release verification (April 8, 2026)

Release status: GO - verified locally and on the live public HF Space.

Verified evidence:

- Local validation:
  - `python -m pytest -q`: 28 passed
  - `openenv validate`: `[OK] a11yfix: Ready for multi-mode deployment`
  - `python reproducibility_report.py`: deterministic summary `easy=0.999`, `medium=0.999`, `hard=0.999`
- Live HF Space verification (public endpoint, 3 consecutive runs):
  - `POST /reset` -> 200
  - `GET /baseline` -> baseline summary remained `easy=0.999`, `medium=0.999`, `hard=0.999`
  - Session continuity gate: pass (`state.step_count == 1` after audit step)
  - State schema gate: pass (`elements`, `score`, `step_count`, `max_steps`, `audit`, `done`, `reward`)
  - Baseline schema gate: pass (`model`, `mode`, `summary`, `results`)
  - Baseline value gate: pass (`easy=0.999`, `medium=0.999`, `hard=0.999`)
- Cookie hardening observed live:
  - `Set-Cookie` includes `HttpOnly`, `SameSite=lax`, `Secure`, `Max-Age=1800`

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
python -m demo.run_demo
python baseline_inference.py
python reproducibility_report.py
python inference.py
```

## Docker

```bash
docker build -t a11yfix .
docker run -p 7860:7860 a11yfix
```

Docker uses the checked-in [`requirements.txt`](requirements.txt) so local and container installs resolve from the same dependency list.

## Why this project is useful

A11yFix turns accessibility from static detection into sequential decision-making, making it a practical benchmark for repair-oriented agents.

