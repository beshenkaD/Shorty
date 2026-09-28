# AGENTS.md

Guide for AI assistants working on shorty

## Toolchain

**Local dev:** Python 3.12 (see [.python-version](.python-version)), [uv](https://docs.astral.sh/uv/). Copy [.env.example](.env.example) to `.env`, then:

```sh
uv sync
uv run shorty-bot
```

**Docker:** `docker compose up --build` runs the bot in a container (reads the same `.env`).

## Definition of done

Changes are not done until all of the following pass on the touched code (and the repo as a whole):

```sh
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

- **Ruff** — lint and format (line-length 100, py312). Config in [pyproject.toml](pyproject.toml).
- **mypy** — strict static typing on the same paths.
- **Tests** — no regressions.

Avoid `# type: ignore` unless unavoidable. Prefer `assert` over suppression for mypy false positives. For ruff, use `# noqa: CODE` with the specific rule. Fix root causes over suppressing warnings.

## Style

**Fail fast.** No fallback stubs, no `try/except ImportError` shims, no "environments without X installed" workarounds. Missing dependencies must crash at import time.

**Don't guess library APIs.** Search docs or ask. Speculative code that compiles is worse than stopping to verify.

**Comments** only for hacky workarounds, non-obvious intent, or known limitations (TODO/FIXME). NEVER narrate obvious code.

**Reuse what exists.** Check the codebase before adding classes, abstractions, or DI wiring. If the user says "use X", use X directly.

## Versioning

Semantic versioning. Canonical version in [pyproject.toml](pyproject.toml) `version` in sync.

## Version control

Do not commit, push or merge PRs unless explicitly said to do so.

## Testing

Tests should utilize `pytest` and only verify business logic. Tests must never rely on static files. If you want to add a test you should explain why it's needed and what exactly it verifies.
