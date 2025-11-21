"""Private testing utilities for `flepimop2`."""

import subprocess  # noqa: S404
from pathlib import Path
from shutil import which

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
        This fixture creates a temporary implicit namespace provider package that
        contributes modules under the `flepimop2.*` namespace. The directory structure
        looks like:
        ```
        ./
        ├── .venv/
        ├── external_provider/
        │   ├── pyproject.toml
        │   └── src/
        │       └── flepimop2/
        │           ├── engine/
        │           │   └── euler.py
        │           └── system/
        │               └── sir.py
        └── model_output/
        ```
        You can add additional source files by providing a mapping of source paths to
        destination paths via the `src_dest_map` argument. Both the namespace provider
        and `flepimop2` will be installed in the the top level `.venv` virtual
        environment, so when running commands using this temporary directory make sure
        to use this virtual environment's Python interpreter.

    """
    uv = uv or which_uv()
    external_provider_package = tmp_path / "external_provider"
    external_provider_package.mkdir(parents=True, exist_ok=True)
    (tmp_path / "model_output").mkdir(parents=True, exist_ok=True)
    flepimop = str(Path(__file__).parent.parent.parent)

    pyproject_text = """\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "example-provider"
version = "0.0.0"
requires-python = ">=3.11"
dependencies = ["numpy", "flepimop2"]

[tool.hatch.build.targets.wheel]
# Ensure implicit namespace packages under flepimop2.* are included.
packages = ["src/flepimop2"]
"""
    (external_provider_package / "pyproject.toml").write_text(pyproject_text)

    # Ensure namespace package directories exist even without __init__.py
    (external_provider_package / "src" / "flepimop2").mkdir(parents=True, exist_ok=True)

    # Add the namespace modules and configuration file
    src_dest_map = src_dest_map or {}
    for src, dest in src_dest_map.items():
        dest_path = tmp_path / dest
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(src.read_text())

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
