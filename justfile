# Run all default tasks for local development
default: dev lint

# Run all default dev tasks
dev: ruff mypy test

# Run all default lint tasks
lint: yamllint

# Run all default CI tasks
ci: quality test docs

# Format code using `ruff`
[group('dev')]
ruff:
    uv run ruff format
    uv run ruff check --fix

# Run coverage tests
[group('dev')]
cov:
    uv run pytest -m "not integration" --cov=src/flepimop2 --cov-report=term-missing

# Run integration tests
[group('dev')]
integration:
    uv run pytest -m "integration"

# Run full pytest suite, including integration tests, without coverage report
[group('ci')]
pytest:
    uv run pytest

# Run coverage and integration tests
[group('dev')]
test: cov integration

# Type check using `mypy`
[group('dev')]
mypy:
    uv run mypy

# Clean up generated lock files, venvs, and caches
[group('dev')]
clean:
    rm -f uv.lock
    rm -rf .*_cache
    rm -rf .venv
    rm -rf site

# Lint YAML files using `yamllint`
[group('lint')]
yamllint:
    uv run yamllint --strict --config-file .yamllint.yaml .

# Run CI `ruff` formatting/linting checks
[group('ci')]
ci-ruff:
    uv run ruff format --check
    uv run ruff check --no-fix

# Run CI quality checks (format/lint/type check)
[group('ci')]
quality: ci-ruff mypy

# Generate API reference documentation
[group('docs')]
reference:
    uv run scripts/api-reference.py
    cp CHANGELOG.md docs/changelog.md
    cp CONTRIBUTING.md docs/development/contributing.md

# Build the documentation using `mkdocs`
[group('docs')]
docs: reference
    uv run mkdocs build --verbose --strict

# Serve the documentation locally using `mkdocs`
[group('docs')]
serve: reference
    uv run mkdocs serve --livereload
