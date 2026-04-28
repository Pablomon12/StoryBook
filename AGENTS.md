# Repository Guidelines

## Project Structure & Module Organization

This repository contains a Python Streamlit app for turning uploaded drawings into illustrated children's stories.

- `app.py` is the Streamlit entry point and UI flow.
- `main.py` is the default scaffold entry point and currently only prints a greeting.
- `app/api/` contains OpenAI-facing story and character generation helpers.
- `app/core/` contains shared configuration and OpenAI client/agent setup.
- `app/models/` contains story state transition logic.
- `app/story.py` defines domain models used across the app.
- `.env.example` documents required environment variables; keep real secrets in `.env`.

There is no dedicated `tests/` directory yet. Add tests under `tests/`, mirroring source paths, for example `tests/models/test_story_engine.py`.

## Build, Test, and Development Commands

Use `uv` for dependency and environment management.

- `uv sync` installs dependencies from `pyproject.toml` and `uv.lock`.
- `uv run streamlit run app.py` starts the local Streamlit app.
- `uv run python main.py` runs the scaffold CLI entry point.
- `uv run pytest` runs the test suite once tests are added.

Before running the Streamlit app, create `.env` from `.env.example` and set `OPENAI_API_KEY`.

## Coding Style & Naming Conventions

Use Python 3.14+ and follow PEP 8: 4-space indentation, snake_case for functions and variables, PascalCase for classes, and clear module names. Keep UI orchestration in `app.py`; put reusable business logic in `app/api/`, `app/core/`, or `app/models/`.

Prefer typed function signatures. Keep prompts readable as multiline string construction, and keep Spanish user-facing copy consistent with the current app.

## Testing Guidelines

Use `pytest`. Focus first on deterministic code such as `app/models/story_engine.py` and prompt-building helpers like `build_character_image_prompt`. Mock OpenAI calls; do not call external APIs in automated tests.

Name test files `test_*.py` and test functions `test_*`. Include edge cases for empty user input, fallback choices, and story phase transitions.

## Commit & Pull Request Guidelines

This repository has no committed history yet, so no project-specific commit convention is established. Use short imperative messages, for example `Add story engine tests` or `Refine Streamlit upload flow`.

Pull requests should include a concise description, commands run (`uv run pytest`, manual Streamlit checks), linked issues if relevant, and screenshots or screen recordings for UI changes.

## Security & Configuration Tips

Never commit `.env` or API keys. Keep `.env.example` limited to placeholder values. Treat uploaded images and generated story content as user data; avoid logging raw image data or secrets.
