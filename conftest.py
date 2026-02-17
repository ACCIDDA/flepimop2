"""Pytest test configuration."""

from collections.abc import Generator
from os import chdir
from pathlib import Path

import pytest
from sybil import Sybil
from sybil.parsers.markdown import PythonCodeBlockParser, SkipParser


def _find_repo_root(start: Path) -> Path:
    """
    Find the repository root by searching for a parent with `pyproject.toml`.

    Args:
        start: The starting directory to search from.

    Returns:
        The path to the repository root directory.

    Raises:
        FileNotFoundError: If no repository root is found.

    """
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    msg = f"Could not find repository root from {start} (missing `pyproject.toml`)."
    raise FileNotFoundError(msg)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """
    Get the repository root directory containing `pyproject.toml`.

    Returns:
        The path to the repository root directory.

    """
    return _find_repo_root(Path(__file__).resolve())


@pytest.fixture(autouse=True)
def doctest_tmpdir(request: pytest.FixtureRequest) -> Generator[None]:
    """
    Create and change to a temporary directory for doctests.

    Args:
        request: The pytest fixture request object.

    Notes:
        [See this StackOverflow answer for details.](https://stackoverflow.com/q/46962007)

    """
    doctest_plugin = request.config.pluginmanager.getplugin("doctest")
    if isinstance(
        request.node,
        doctest_plugin.DoctestItem,
    ):
        tmpdir = request.getfixturevalue("tmpdir")
        with tmpdir.as_cwd():
            yield
    else:
        yield


@pytest.fixture(autouse=True)
def docs_tmpdir(request: pytest.FixtureRequest, tmp_path: Path) -> Generator[None]:
    """
    Run docs tests from a temp working directory and restore cwd afterwards.

    Args:
        request: The pytest fixture request object.
        tmp_path: The temporary working directory.

    Yields:
        `None`, but ensures the current working directory is changed to `tmp_path`
    """
    if request.node.nodeid.startswith("docs/"):
        old_cwd = Path.cwd()
        chdir(tmp_path)
        try:
            yield
        finally:
            chdir(old_cwd)
    else:
        yield


pytest_collect_file = Sybil(
    parsers=[
        PythonCodeBlockParser(),
        SkipParser(),
    ],
    path=str(Path(__file__).parent / "docs"),
    pattern="**/*.md",
).pytest()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """
    Automatically mark tests in tests/integration as integration tests.

    Args:
        items: The list of collected pytest items to modify.

    """
    integration_prefix = "tests/integration/"
    marker = pytest.mark.integration
    for item in items:
        if item.nodeid.startswith(integration_prefix):
            item.add_marker(marker)
