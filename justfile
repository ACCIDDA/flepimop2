# Run all default tasks for local development
default: dev lint

# Run all default dev tasks
dev: ruff mypy test

# Run all default lint tasks
lint: yamllint changelog

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
[unix]
clean:
    rm -rf .*cache
    rm -rf .venv
    rm -rf site
    rm -f uv.lock

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
[unix]
reference:
    uv run scripts/authors.py
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

# Lint YAML files using `yamllint`
[group('lint')]
yamllint:
    uv run yamllint --strict --config-file .yamllint.yaml .

# Check that CHANGELOG.md was updated relative to main
[group('lint')]
[unix]
changelog:
    #!/usr/bin/env bash
    set -euo pipefail
    BASE_REF="main"
    if ! git show-ref --verify --quiet "refs/heads/${BASE_REF}"; then
        git fetch origin "${BASE_REF}:${BASE_REF}"
    fi
    COMMIT_COUNT=$(git rev-list --count "${BASE_REF}..HEAD")
    if [[ "${COMMIT_COUNT}" -eq 1 ]]; then
        COMMIT_MSG=$(git log -1 --pretty=format:"%s %b")
        SKIP_REGEX='no[[:space:]]+major[[:space:]]+changes'
        if echo "${COMMIT_MSG}" | tr '\n' ' ' | grep -Eiq "${SKIP_REGEX}"; then
            echo "Bypassing changelog check: single commit contains 'no major changes'"
            exit 0
        fi
    fi
    if ! git diff --name-only "${BASE_REF}...HEAD" | grep -q '^CHANGELOG\.md$'; then
        echo "Error: Please update CHANGELOG.md"
        exit 1
    fi
    echo "CHANGELOG.md check passed"
