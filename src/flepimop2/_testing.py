"""Private testing utilities for `flepimop2`."""

import subprocess  # noqa: S404
from pathlib import Path
from shutil import which
from textwrap import dedent

import pytest


def which_uv() -> str:
    """
    Find the 'uv' executable in the system PATH.

    This function checks for the presence of the 'uv' executable, which is required
    for setting up the external provider project for testing. If 'uv' is not found,
    the test is skipped. The return type is a string instead of a Path object to make
    it easier to use in subprocess calls.

    Returns:
        The absolute path to the 'uv' executable as a string.
    """
    result = which("uv")
    if result is None:
        pytest.skip("uv executable not found in PATH")
    return str(Path(result).absolute())


def _configure_namespace_pyproject(project_root: Path) -> None:
    """Configure the external provider package as a namespace distribution."""
    pyproject = project_root / "pyproject.toml"
    content = dedent(
        """
        [build-system]
        requires = ["setuptools>=68"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "flepimop2-external-provider"
        version = "0.1.0"
        description = "Example components for flepimop2 integration tests."
        readme = "README.md"
        requires-python = ">=3.11"

        [tool.setuptools.packages.find]
        where = ["src"]
        include = ["flepimop2*"]
        namespaces = true
        """
    )
    pyproject.write_text(content, encoding="utf-8")


def external_provider_project(
    tmp_path: Path, uv: str | None = None, src_dest_map: dict[Path, Path] | None = None
) -> None:
    """
    Set up the external provider project for testing.

    Args:
        tmp_path: Temporary directory provided by pytest.
        uv: Path to the `uv` executable.
        src_dest_map: Optional mapping of source files to destination paths within
            the external provider package.

    Notes:
        This fixture creates a temporary external provider package called
        `external_provider` using `uv`, configures it as a namespace package rooted
        at `flepimop2`, and installs it in a virtual environment. The directory
        structure looks like:
        ```
        ./
        ├── .venv/
        ├── external_provider/
        │   ├── .python-version
        │   ├── .venv/
        │   ├── pyproject.toml
        │   ├── README.md
        │   ├── src/
        │   │   └── flepimop2/
        │   │       ├── engine/
        │   │       └── system/
        │   └── uv.lock
        └── model_output/

        7 directories, 5 files
        ```
        You can then add additional source files to the package by providing a
        mapping of source paths to destination paths via the `src_dest_map`
        argument. Both `external_provider` and `flepimop2` will be installed in the
        the top level `.venv` virtual environment, so when running commands using this
        temporary directory make sure to use this virtual environment's Python
        interpreter.

    """
    # Create a temporary external provider package
    uv = uv or which_uv()
    external_provider_package = tmp_path / "external_provider"
    external_provider_package.mkdir(parents=True, exist_ok=True)
    (tmp_path / "model_output").mkdir(parents=True, exist_ok=True)
    flepimop = str(Path(__file__).parent.parent.parent)
    # Initialize the package using 'uv'
    subprocess.run(  # noqa: S603
        [uv, "init", "--package", "--vcs", "none"],
        capture_output=True,
        text=True,
        cwd=external_provider_package,
        check=True,
    )
    _configure_namespace_pyproject(external_provider_package)
    # Add the stepper & runner modules and configuration file
    src_dest_map = src_dest_map or {}
    for src, dest in src_dest_map.items():
        (tmp_path / dest).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / dest).write_text(src.read_text())
    # Install the package
    subprocess.run(  # noqa: S603
        [uv, "venv"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(  # noqa: S603
        [
            uv,
            "pip",
            "install",
            "--python",
            str(tmp_path / ".venv" / "bin" / "python"),
            flepimop,
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(  # noqa: S603
        [
            uv,
            "pip",
            "install",
            "--python",
            str(tmp_path / ".venv" / "bin" / "python"),
            str(external_provider_package),
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=True,
    )
