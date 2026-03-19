"""Pytest test configuration."""

# ruff: noqa: DOC201

import re
import sys
from collections.abc import Generator
from importlib.util import module_from_spec, spec_from_file_location
from os import chdir
from pathlib import Path
from typing import cast

import pytest
from _pytest.doctest import DoctestModule
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


REPO_ROOT = _find_repo_root(Path(__file__).resolve())
SOURCE_ROOT = REPO_ROOT / "src" / "flepimop2"


def _doctest_module_name(file_path: Path) -> str:
    """
    Build a synthetic module name for path-based doctest imports.

    This avoids collisions with stdlib modules such as `abc`.
    """
    relative_path = file_path.relative_to(SOURCE_ROOT)
    sanitized = re.sub(r"[^0-9A-Za-z_]", "_", relative_path.as_posix())
    return f"_flepimop2_doctest_{sanitized}"


class SourceDoctestModule(DoctestModule):
    """
    Doctest collector that imports source files by file path.

    Pytest's normal module-name inference collapses several `*/abc/__init__.py`
    files to the stdlib `abc` module when using namespace packages. Importing
    by path avoids that collision.
    """

    def _getobj(self) -> object:
        module_name = _doctest_module_name(self.path)
        spec = spec_from_file_location(module_name, self.path)
        if spec is None or spec.loader is None:
            msg = f"Could not create an import spec for {self.path!r}."
            raise ImportError(msg)

        module = module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(module_name, None)
            raise
        return module


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


_sybil_collect_file = Sybil(
    parsers=[
        PythonCodeBlockParser(),
        SkipParser(),
    ],
    path=str(Path(__file__).parent / "docs"),
    pattern="**/*.md",
).pytest()


def pytest_collect_file(
    file_path: Path, parent: pytest.Collector
) -> pytest.Collector | None:
    """Collect doctests from source modules and Sybil docs files."""
    if file_path.suffix == ".py" and file_path.is_relative_to(SOURCE_ROOT):
        return SourceDoctestModule.from_parent(parent, path=file_path)
    return cast("pytest.Collector | None", _sybil_collect_file(file_path, parent))


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
