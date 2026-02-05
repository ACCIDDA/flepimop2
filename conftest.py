"""Pytest test configuration."""

from collections.abc import Generator
from os import chdir
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest
from sybil import Sybil
from sybil.parsers.markdown import PythonCodeBlockParser, SkipParser


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


def documentation_setup(documentation_setup: dict[str, Any]) -> None:  # noqa: ARG001
    """Create and change to a temporary directory for documentation tests."""
    directory = Path(TemporaryDirectory().name)
    directory.mkdir(parents=True, exist_ok=True)
    chdir(directory)


pytest_collect_file = Sybil(
    parsers=[
        PythonCodeBlockParser(),
        SkipParser(),
    ],
    path=str(Path(__file__).parent / "docs"),
    pattern="**/*.md",
    setup=documentation_setup,
).pytest()
