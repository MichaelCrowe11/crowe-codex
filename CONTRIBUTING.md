# Contributing to crowe-codex

Thanks for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/MichaelCrowe11/crowe-codex.git
cd crowe-codex
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Lint

```bash
ruff check src/ tests/
```

## Adding a Strategy

1. Create a new file in `src/crowe_codex/strategies/`
2. Subclass `Strategy` from `crowe_codex.strategies.base`
3. Implement `execute()` and `stages_needed()`
4. Add tests in `tests/`
5. Register in `src/crowe_codex/strategies/__init__.py`

## Pull Requests

- One feature per PR
- Include tests
- Run `ruff check` before submitting
- Keep commits focused
