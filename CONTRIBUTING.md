# Contributing to SocialConnector

Thank you for your interest in contributing! Every contribution - bug fixes, new providers, docs, tests - is appreciated.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Adding a New Provider](#adding-a-new-provider)
- [Code Standards](#code-standards)
- [Running Tests](#running-tests)
- [Pull Request Process](#pull-request-process)

---

## Development Setup

```bash
# 1. Fork and clone the repo
git clone https://github.com/naveenairani/socialconnect.git
cd socialconnect

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows

# 3. Install in editable mode with all dev dependencies
pip install -e ".[dev,all]"

# 4. Install pre-commit hooks
pre-commit install
```

Copy `.env.example` to `.env` and fill in your credentials for local testing:

```bash
cp .env.example .env
```

---

## Project Structure

```
socialconnect/
|-- src/socialconnector/
|   |-- __init__.py          # SocialConnector factory + public API
|   |-- core/                # BaseAdapter, models, exceptions
|   |-- providers/           # One module/package per platform (x/, telegram.py, ...)
|   |-- utils/               # Shared helpers
|   `-- webhooks/            # Webhook handling infrastructure
|-- tests/
|   `-- providers/           # One test file per provider
|-- docs/                    # Architecture and provider guides
|-- pyproject.toml
`-- CHANGELOG.md
```

---

## Adding a New Provider

1. **Create the adapter** - `src/socialconnector/providers/my_platform.py` (or a package directory)
   - Inherit from `BaseAdapter` in `src/socialconnector/core/base_adapter.py`
   - Implement all abstract methods: `post()`, `direct_message()`, `upload_media()`

2. **Register it** - add to `src/socialconnector/providers/__init__.py` and the factory in `src/socialconnector/__init__.py`

3. **Add optional dependencies** - in `pyproject.toml` under `[project.optional-dependencies]`

4. **Write tests** - `tests/providers/test_my_platform.py`

5. **Add docs** - `docs/providers/MY_PLATFORM.md`

6. **Update the README** - add a row to the Supported Platforms table

See `docs/ARCHITECTURE.md` for the full adapter interface specification.

---

## Code Standards

| Tool | Command | Requirement |
|------|---------|-------------|
| Ruff (linting) | `ruff check .` | Must pass |
| Ruff (formatting) | `ruff format .` | Must pass |
| Mypy (type checking) | `mypy src/` | Must pass |
| Pytest (tests) | `pytest` | Must pass, >80% coverage |

- **Type hints**: All public functions must have complete type annotations
- **Docstrings**: Google-style on all public classes and methods
- **No secrets in code**: Use environment variables, never hardcode credentials

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=socialconnector --cov-report=term-missing

# Run a specific provider's tests
pytest tests/providers/test_x.py -v

# Run linting
ruff check .

# Run type checking
mypy src/
```

---

## Pull Request Process

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/add-instagram-provider
   ```

2. **Make your changes** with tests and type annotations

3. **Update `CHANGELOG.md`** - add an entry under `[Unreleased]`

4. **Push and open a PR** using the provided template

5. **A maintainer will review** - please be patient and responsive to feedback

### Commit Message Style

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Instagram provider
fix: handle rate limit retry in X adapter
docs: update architecture diagram
test: add coverage for Telegram DM edge case
```

---

## Questions?

Open a [GitHub Discussion](https://github.com/naveenairani/socialconnect/discussions) or see [SUPPORT.md](SUPPORT.md).

