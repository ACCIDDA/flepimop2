# Contributing to `flepimop2`

This document provides guidelines and instructions for contributing to `flepimop2`, including development conventions and tips for best practices.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Development Setup

### Prerequisites

- Python 3.10, 3.11, 3.12, or 3.13.
- [`uv`](https://docs.astral.sh/uv/) - Python package manager.
- [`just`](https://just.systems/) - Command runner (optional but strongly recommended).

### Initial Setup

1. Clone the repository:

```shell
git clone git@github.com:ACCIDDA/flepimop2.git
cd flepimop2
```

2. Create a virtual environment and install dependencies:

```shell
uv sync --dev
```

This creates a `.venv` virtual environment and installs the package along with all development dependencies (mypy, pytest, ruff, mkdocs). If you need to create an environment with a specific python version you can also run:

```shell
uv sync --dev --python 3.12
```

3. Verify your setup

```shell
just
```

This runs the default development checks:

- `ruff format` - Format code.
- `ruff check --fix` - Lint and auto-fix issues.
- `pytest --doctest-modules` - Run tests including doctests.
- `mypy --strict` - Type check with strict settings.

It is recommended that you run this command frequently as you do development work to catch issues early.

## Code Standards

### Style

We use [`ruff`](https://docs.astral.sh/ruff/) for both formatting and linting:

- **Formatting**: `ruff format` follows the Black code style.
- **Linting**: `ruff check` enforces code quality rules.

Run `just` to automatically format and lint your code before committing. Or you can run `just format` and `just check` to run just these steps.

## Testing

### Organization

Tests are organized to mirror the source code structure:

```
tests/
|-- {module}/
|   |-- {submodule}/
|   |   |-- test_{function}.py     # Tests for individual functions
|   |   |-- test_{class}_class.py  # Tests for classes
|   |-- test_{function}.py
```

**Examples:**

- `tests/logging/test_get_script_logger.py` - Tests for the `get_script_logger` function.
- `tests/logging/test_click_handler_class.py` - Tests for the `ClickHandler` class.
- `tests/_cli/_options/test_get_option.py` - Tests for the `get_option` function.
- `tests/configuration/test_fixed_parameter_specification_model_class.py` - Tests for the `FixedParameterSpecificationModel` class.

### Running Tests

Running all tests is a part of running `just` or if you want to run only the tests instead of all checks you can run `just pytest`. For more advanced running please use `pytest` directly:

```shell
uv run pytest tests/{module}/ -v                    # Run all tests in a module
uv run pytest tests/{module}/test_{function}.py -v  # Run specific test file
```

For more information on how to invoke pytest please refer to the [How to invoke pytest](https://docs.pytest.org/en/stable/how-to/usage.html) documentation.

### Writing Tests

- Any public API should have unit tests that reaffirm the documentation's description.
- If possible unit tests should use `@pytest.mark.parameterize` for generality and ease of adding new test cases.
- Use descriptive test names that explain what is being tested. In the case of testing exceptions also the type of exception.
- For smaller helper functions, especially internal helpers, doctests are sufficient.

### Type Checking

All code must pass strict type checking with `mypy` which can be invoked with `just mypy`. Note that `ruff` will catch missing type hints whereas `mypy` will check that those type hints are correct and consistent.

## Documentation

We use [MkDocs](https://www.mkdocs.org/) for documentation.

### Editing Documentation

Documentation files are located in the `docs/` directory:

```
docs/
|-- index.md                # Home page
|-- guides/
    |-- getting-started.md  # Getting started guide
```

The documentation structure is defined in `mkdocs.yml`.

### Viewing Documentation Locally

To preview documentation changes locally you can run `just serve` which will build the documentation and start a local server at `http://127.0.0.1:8000/`. To only build the documentation you can run `just build` which will generate the documentation site in the `site/` directory.

### Documentation Testing

In addition to unit tests and doctests, code contained in the documentation is also tested. This is ran as a part of `just`/`just pytest`. Each documentation page is treated as if it were one script so code blocks can reference previously created variables. To support this type of testing we use [`Sybil`](https://sybil.readthedocs.io/en/latest/).

## Pull Request Process

### Before Submitting

1. Run CI checks locally using `just ci`. This runs the same checks that CI will run:

- `ruff format --check` - Verify code formatting (no auto-fix).
- `ruff check --no-fix` - Lint without modifications.
- `pytest --doctest-modules` - Run test suite.
- `mypy --strict` - Type checking.

2. Update documentation if your changes affect user-facing functionality or add features that require usage guides.

3. Add tests for new functionality or bug fixes. Particularly for bug fixes, the test should be written before the fix and fail without the fix present.

### Submitting a Pull Request

1. Create a branch from `main` and make your changes on this branch using the code standards above. Please use clear and descriptive commit messages that explain the changes made and why. After your work is finished either push directly to `flepimop2` or your fork (depending on your permissions).

2. Create a pull request with:

- The motivation for and a clear description of the changes.
- Link any related issues (use "Fixes #123" to auto-close issues).
- Explicitly point out the relevant documentation changes.

### Pull Request Requirements

- PRs are tested against Python 3.10, 3.11, 3.12, and 3.13 using `just ci`.
- Documentation must build successfully with `just docs`.
- At least one maintainer approval is required before merging.
- Branches must be up to date against `main` before merging and have a linear history. Only rebases are allowed for merging.

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- Operating system and version.
- Python version (e.g., Python 3.12.1).
- `flepimop2` version as a git commit hash.
- A minimal, reproducible example that demonstrates the issue.
- An explanation of expected behavior vs actual behavior.
- Error messages or tracebacks if applicable.

### Feature Requests

For feature requests, please:

- Check existing issues to avoid duplicates.
- Clearly describe the use case and motivation.
- Provide examples of how the feature would be used.
- Be open to discussion about implementation approaches.

### Questions

For questions about using flepimop2:

- Check the documentation (which can be viewed locally with `just serve` for now).
- Search existing issues for similar questions.
- Open a new issue with the "question" label.
