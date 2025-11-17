# Run all default tasks for local development
default: format check pytest mypy yamllint

# Format code using `ruff`
format:
    uv run ruff format --preview

# Check code using `ruff`
check:
    uv run ruff check --preview --fix

# Run tests using `pytest`
pytest:
    uv run pytest --doctest-modules

# Type check using `mypy`
mypy:
    uv run mypy --strict src/

# Lint YAML files using `yamllint`
yamllint:
    uv run yamllint --strict --config-file .yamllint.yaml .

# Run all CI checks
ci:
    uv run ruff format --preview --check
    uv run ruff check --preview --no-fix
    uv run pytest --doctest-modules
    uv run mypy --strict src/

# Clean up generated lock files, venvs, and caches
clean:
    rm -f uv.lock
    rm -rf .*_cache
    rm -rf .venv
    rm -rf site
    find . -type d -name "__pycache__" -prune -exec rm -rf {} +

# Generate API reference documentation
reference:
    uv run scripts/api-reference.py
    cp CHANGELOG.md docs/changelog.md
    cp CONTRIBUTING.md docs/development/contributing.md

# Build the documentation using `mkdocs`
docs: reference
    uv run mkdocs build --verbose --strict

# Serve the documentation locally using `mkdocs`
serve: reference
    uv run mkdocs serve
