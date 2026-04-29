# Repository Guidelines

## Project Structure & Module Organization

This repository contains a `FastAPI` backend plus a `Next.js` frontend for turning uploaded drawings into illustrated children's stories. Backend code lives under `app/`: `app/main.py` wires the API, `app/routes/` exposes HTTP endpoints, `app/api/` contains OpenAI-backed generation helpers, `app/core/` holds config and client setup, `app/models/` keeps story-state logic, and `app/story.py` defines domain models. The frontend lives in `frontend/` using the App Router. Tests live in `tests/`, mirroring backend areas such as `tests/api/` and `tests/models/`.

## Build, Test, and Development Commands

Use `uv` for environment and dependency management.

- `uv sync`: install project dependencies from `pyproject.toml` and `uv.lock`.
- `uv run uvicorn app.main:app --reload`: start the FastAPI backend locally.
- `uv run pytest`: run the automated test suite.
- `cd frontend && npm install`: install frontend dependencies.
- `cd frontend && npm run dev`: start the Next.js client.

Run commands from the repository root.

## Coding Style & Naming Conventions

Target Python `>=3.14` and follow PEP 8 with 4-space indentation. Use `snake_case` for functions and variables, `PascalCase` for classes, and clear module names. Keep route handlers thin in `app/routes/`; place reusable business logic in `app/api/`, `app/core/`, or `app/models/`. In the frontend, use TypeScript, typed state, and small helper functions instead of embedding fetch logic everywhere. Keep Spanish user-facing copy consistent across backend prompts and UI labels.

## Testing Guidelines

Use `pytest`. Add tests under `tests/` using `test_*.py` filenames and `test_*` functions. Focus on deterministic units such as `app/models/story_engine.py`, prompt builders, and FastAPI route behavior. Mock OpenAI calls in tests; do not hit external APIs. Cover invalid uploads, fallback choices, streaming route payloads, and story phase transitions.

## Commit & Pull Request Guidelines

The Git history is minimal (`first commit`, `V1`, `Mejora interfaz`), so there is no strict convention yet. Prefer short, imperative commit messages such as `Add story engine edge-case tests`. Pull requests should include a concise summary, commands run (for example `uv run pytest`), linked issues when relevant, and screenshots or recordings for UI changes.

## Security & Configuration Tips

Never commit `.env`, `.env.local`, API keys, or raw user uploads. Treat generated images and story content as user data, and avoid logging sensitive payloads or base64 image bodies.
