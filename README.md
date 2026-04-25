# flepimop2

The next generation of the flexible epidemic modeling pipeline.

## Installation

`flepimop2` is published on [PyPI](https://pypi.org/project/flepimop2/) and can be installed with:

```bash
pip install flepimop2
```

If you are adding `flepimop2` as a dependency in another project, see the [installation guide](docs/guides/install.md).

## Local Development

1. Clone the repository

```bash
git clone git@github.com:ACCIDDA/flepimop2.git
cd flepimop2
```

2. Create a virtual environment and install dependencies using [`uv`](https://docs.astral.sh/uv/). To create a `.venv` with the package installed:

```bash
uv sync --dev
```

This will create a virtual environment and install the package along with development dependencies (mypy, pytest, ruff).

3. Run default checks using [`just`](https://just.systems/). To run the default development tasks:

```bash
just
```

This will run:

- `ruff format` - Format code.
- `ruff check --fix` - Lint and auto-fix issues.
- `pytest --doctest-modules` - Run tests including doctests.
- `mypy --strict` - Type check with strict settings.
- `yamllint --strict` - Lint YAML files.

4. CI runs on pull requests to `main` and tests against Python 3.11, 3.12, 3.13, and 3.14. The CI checks are defined in `just ci` and include:

- `ruff format --check` - Verify code formatting (no auto-fix).
- `ruff check --no-fix` - Lint without modifications.
- `pytest --doctest-modules` - Run test suite.
- `mypy --strict` - Type checking.

To run the same checks locally that run in CI (say for diagnosing CI failures):

```bash
just ci
```

There is a separate CI check which will run `just yamllint` and `just docs` to check YAML file formatting and that the documentation builds successfully.

## Funding Acknowledgement

This project was made possible by the Insight Net cooperative agreement CDC-RFA-FT-23-0069 from the CDC’s Center for Forecasting and Outbreak Analytics. Its contents are solely the responsibility of the authors and do not necessarily represent the official views of the Centers for Disease Control and Prevention.
