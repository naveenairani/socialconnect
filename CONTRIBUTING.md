# Contributing to SocialConnector

Thank you for your interest in contributing! This document outlines the process for contributing to SocialConnector.

## Development Setup

```bash
git clone https://github.com/yourusername/socialconnector.git
cd socialconnector
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev,all]"
pre-commit install
```

## Adding a New Provider

1. Create a new file in `src/socialconnector/providers/` (e.g., `my_platform.py`)
2. Implement the `BaseAdapter` abstract class
3. Register the provider in `src/socialconnector/providers/__init__.py`
4. Add provider-specific dependencies to `pyproject.toml` under `[project.optional-dependencies]`
5. Write tests in `tests/providers/test_my_platform.py`
6. Add documentation in `docs/providers/MY_PLATFORM.md`

See `docs/ARCHITECTURE.md` for the full design pattern and adapter interface.

## Code Standards

- **Type hints**: All public functions must have complete type annotations
- **Docstrings**: Google-style docstrings on all public classes/methods
- **Linting**: `ruff check .` must pass
- **Type checking**: `mypy src/` must pass
- **Tests**: `pytest` must pass with >80% coverage

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/add-new-provider`)
3. Write tests for your changes
4. Ensure all linting/type checks pass
5. Submit a PR with a clear description
