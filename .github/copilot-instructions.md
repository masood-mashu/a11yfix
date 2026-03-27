# Project Guidelines

## Code Style
- Keep edits minimal and localized; avoid broad refactors unless requested.
- Follow existing Python style in this repo: simple functions, explicit dictionaries/tuples, and brief inline comments only where needed.
- Preserve environment contracts in `env/` and avoid changing reward or violation semantics unless explicitly requested.

## Architecture
- `app.py`: API surface for tasks, baseline, and grader flows.
- `env/`: core RL environment (`a11y_env.py`), reward shaping (`reward.py`), and violation detection (`violations.py`).
- `tasks/`: difficulty-specific task definitions and baseline `run_task()` implementations.
- `agents/`: baseline agent behaviors.
- `demo/`: local demonstration flow.

## Build and Test
- Local run: `python app.py`
- Run environment check: `python test_env.py`
- Run all tasks: `python tasks/run_all_tasks.py`
- Run baseline agent: `python agents/baseline_agent.py`
- Run demo: `python demo/run_demo.py`
- Docker build: `docker build -t a11yfix .`
- Docker run: `docker run -p 7860:7860 a11yfix`

## Conventions
- Actions passed to the environment must use tuple format:
  - `("audit",)`
  - `("set_attribute", element_id, attr, value)`
  - `("done",)`
- Element objects should keep the shape:
  - `{"id": str, "type": str, "attributes": dict}`
- Treat task modules as the source of truth for task-specific configuration (elements, step budgets, and task behavior) when wiring grader or baseline logic.
- Keep task difficulty consistency when editing `tasks/easy.py`, `tasks/medium.py`, and `tasks/hard.py`.

## References
- See `README.md` for API usage and project overview.
- See `openenv.yaml` for environment specification.
