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
    rm -rf dist
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
    printf '# License\n\n```\n' > docs/license.md && cat LICENSE >> docs/license.md && printf '```\n' >> docs/license.md

# Build the documentation using `mkdocs`
[group('docs')]
docs: reference
    uv run mkdocs build --verbose --strict

# Serve the documentation locally using `mkdocs`
[group('docs')]
serve: reference
    uv run mkdocs serve --livereload

# Build sdist and wheel, then validate package metadata
[unix]
[group('build')]
build-check:
    rm -rf dist/
    uv run python -m build
    uv run python -m twine check --strict dist/*

# Install the built wheel into a clean room and run non-integration tests
[unix]
[group('build')]
build-test:
    #!/usr/bin/env bash
    set -euo pipefail
    CLEANROOM="$(mktemp -d)"
    HAD_LOCK='false'
    if [ -f uv.lock ]; then
        HAD_LOCK='true'
    fi
    trap 'rm -rf "${CLEANROOM}"; if [ "${HAD_LOCK}" = "false" ]; then rm -f uv.lock; fi' EXIT
    uv lock --python "${UV_PYTHON_VERSION:-3.12}"
    uv export --frozen --only-group dev --no-emit-project --format requirements.txt --no-hashes --output-file "${CLEANROOM}/dev-requirements.txt" >/dev/null
    uv run python -m build --wheel --outdir "${CLEANROOM}/dist"
    uv venv --python "${UV_PYTHON_VERSION:-3.12}" "${CLEANROOM}/venv"
    uv pip install --python "${CLEANROOM}/venv/bin/python" "${CLEANROOM}"/dist/*.whl
    uv pip install --python "${CLEANROOM}/venv/bin/python" -r "${CLEANROOM}/dev-requirements.txt"
    cp pyproject.toml "${CLEANROOM}/pyproject.toml"
    cp -R tests "${CLEANROOM}/tests"
    cp conftest.py "${CLEANROOM}/conftest.py"
    cd "${CLEANROOM}"
    "${CLEANROOM}/venv/bin/pytest" --import-mode=importlib tests --quiet --exitfirst -m "not integration"

# Run all package build validations
[group('build')]
build-all: build-check build-test

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

# Validate release metadata without creating a GitHub release
[group('release')]
release-check:
    uv run python scripts/release.py

# Create the GitHub release after all checks pass
[group('release')]
release +FLAGS='':
    uv run python scripts/release.py {{FLAGS}}

# Run the full local release preflight
[group('release')]
release-validate: build-all release-check
