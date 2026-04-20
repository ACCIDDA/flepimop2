# Creating A Release

This guide covers the `flepimop2` release process, from preparing the changelog to running the manual GitHub Actions release workflow.

## Prerequisites

- You have write access to the [`ACCIDDA/flepimop2`](https://github.com/ACCIDDA/flepimop2) repository.
- The version has already been updated in `pyproject.toml`.
- The release notes for that version have already been added to `CHANGELOG.md`.
- Your local environment is synced with a supported Python version via `uv sync --python 3.12 --group dev`.
- You have [GitHub's `gh` CLI](https://cli.github.com/) installed and authenticated.

## 1. Format The Changelog

The release workflow validates `CHANGELOG.md` using `scripts/release.py`, so the changelog format must match what that script expects.

For a release, the top section of `CHANGELOG.md` must:

- Not contain a `## [Unreleased]` heading.
- Start with a heading in the form `## [X.Y.Z] - YYYY-MM-DD`.
- Use the current release version and the current date.
- Contain at least one non-empty bullet point.

Example:

```md
## [0.1.0] - 2026-04-07

### Added

- Added packaging validation and release workflow infrastructure.
```

If the top heading, date, or bullet formatting is wrong, `just release-check` and the release workflow will fail before anything is published.

## 2. Run The Local Release Preflight

Use the `just release-validate` recipe to run the following checks locally:

- `build-check`: Build the source distribution and wheel, then run `twine check --strict` on the generated artifacts.
- `build-test`: Build the wheel, install it into a clean virtual environment, install the current development dependency set exported from `uv`, and run the non-integration test suite against the installed wheel.
- `release-check`: Run `uv run python scripts/release.py` without `--create` to ensure the `CHANGELOG.md` is formatted correctly and the version is releasable.

## 3. Run The Release Workflow

Releases are created through the manual GitHub Actions workflow in `.github/workflows/release.yaml`.

If you are testing the workflow before the pull request is merged, add `--ref <branch-name>` to the `gh workflow run` command. Without `--ref`, GitHub dispatches the workflow definition from the repository's default branch. Using `--ref <branch-name>` means the workflow validates, builds, and publishes artifacts from that branch rather than from `main`.

### Dry Run

Use this to validate the release end to end without publishing to TestPyPI, creating a GitHub release, or deploying docs:

```shell
gh workflow run release.yaml \
  --repo ACCIDDA/flepimop2 \
  --ref <branch-name> \
  --field publish-target=none \
  --field create-github-release=false \
  --field deploy-docs=false
```

This runs the `validate` job only. It still enforces the changelog and release metadata checks through `just release-validate`.

### TestPyPI

Use this to publish the built artifacts to TestPyPI without creating the GitHub release or deploying docs:

```shell
gh workflow run release.yaml \
  --repo ACCIDDA/flepimop2 \
  --ref <branch-name> \
  --field publish-target=testpypi \
  --field create-github-release=false \
  --field deploy-docs=false
```

This is the safest way to test the release workflow against a real package index before publishing to PyPI.

When testing from a branch, keep `create-github-release=false` and `deploy-docs=false`. The documentation deployment workflow checks out `main`, so it is not intended for pre-merge branch testing.

### PyPI

Use this to publish `flepimop2` to PyPI, create a GitHub release, and deploy the documentation:

```shell
gh workflow run release.yaml \
  --repo ACCIDDA/flepimop2 \
  --field publish-target=pypi \
  --field create-github-release=true \
  --field deploy-docs=true
```

## 4. Trusted Publishing Setup

The TestPyPI publish job uses PyPI Trusted Publishing rather than a stored API token. To enable publishing to TestPyPI, configure the trusted publisher entry for:

- Owner: `ACCIDDA`.
- Repository: `flepimop2`.
- Workflow file: `release.yaml`.

If that configuration is missing, the TestPyPI publish job will fail even if validation passes.
