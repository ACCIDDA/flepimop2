"""Public testing utilities for `flepimop2`."""

__all__ = ["external_provider_package", "flepimop2_run", "project_skeleton"]

import re
import subprocess  # noqa: S404
from pathlib import Path
from shutil import which


def _which_python() -> str:
    """
    Find the 'python' executable in the system PATH.

    Returns:
        The absolute path to the 'python' executable as a string.

    Raises:
        RuntimeError: If the 'python' executable is not found in PATH.

    """
    result = which("python")
    if result is None:
        msg = "python executable not found in PATH"
        raise RuntimeError(msg)
    return str(Path(result).absolute())


def _find_project_root_candidate(start: Path) -> Path | None:
    """
    Traverse upward from `start` to find a directory containing `pyproject.toml`.

    Args:
        start: Path to begin searching from.

    Returns:
        The project root directory if found, otherwise `None`.

    """
    start = start.resolve()
    candidates = [start, *start.parents]
    for candidate in candidates:
        if (candidate / "pyproject.toml").exists():
            return candidate
    return None


def _find_project_root(start: Path) -> Path:
    """
    Traverse upward from `start` to find a directory containing `pyproject.toml`.

    Args:
        start: Path to begin searching from.

    Returns:
        The project root directory.

    Raises:
        FileNotFoundError: If no `pyproject.toml` is found.

    """
    if (root := _find_project_root_candidate(start)) is not None:
        return root

    module_path = Path(__file__).resolve()
    if (root := _find_project_root_candidate(module_path)) is not None:
        return root

    msg = "Could not locate pyproject.toml in parent directories"
    raise FileNotFoundError(msg)


def _venv_python_path(parent_directory: Path) -> Path:
    """
    Find the python executable within the `.venv` directory of `parent_directory`.

    Args:
        parent_directory: Directory in which to search for the python executable.

    Returns:
        The path to the python executable within the `.venv` directory.

    Raises:
        FileNotFoundError: If the python executable is not found in `.venv`.

    """
    if (py := (parent_directory / ".venv" / "bin" / "python")).exists():
        return py
    msg = "Could not find python executable in .venv"
    raise FileNotFoundError(msg)


def _create_venv(python: str, parent_directory: Path) -> str:
    """
    Create a virtual environment and install `flepimop2` into it.

    Args:
        python: Path to the python executable.
        parent_directory: Directory in which to create the venv at `.venv`.

    Returns:
        The python executable path from the newly created venv.

    """
    parent_directory = parent_directory.resolve()
    project_root = _find_project_root(parent_directory)
    venv_dir = parent_directory / ".venv"

    subprocess.run(  # noqa: S603
        [python, "-m", "venv", str(venv_dir)],
        capture_output=True,
        text=True,
        cwd=parent_directory,
        check=True,
    )

    venv_python = _venv_python_path(parent_directory)
    subprocess.run(  # noqa: S603
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            str(project_root),
        ],
        capture_output=True,
        text=True,
        cwd=parent_directory,
        check=True,
    )
    return str(venv_python)


def _resolve_dependencies(
    dependencies: list[str] | None, *, require_flepimop2: bool
) -> list[str]:
    """
    Resolve the list of dependencies.

    Args:
        dependencies: List of dependencies to include in the provider package.
        require_flepimop2: Whether to ensure that "flepimop2" is included in the
            dependencies.

    Returns:
        The resolved list of dependencies, which could be empty.

    Examples:
        >>> from flepimop2.testing import _resolve_dependencies
        >>> _resolve_dependencies(None, require_flepimop2=True)
        ['flepimop2']
        >>> _resolve_dependencies(None, require_flepimop2=False)
        []
        >>> _resolve_dependencies(["numpy"], require_flepimop2=True)
        ['numpy', 'flepimop2']
        >>> _resolve_dependencies(["numpy"], require_flepimop2=False)
        ['numpy']
        >>> _resolve_dependencies(["flepimop2"], require_flepimop2=True)
        ['flepimop2']
        >>> _resolve_dependencies(["flepimop2"], require_flepimop2=False)
        ['flepimop2']
        >>> _resolve_dependencies(["flepimop2>=0.1.0"], require_flepimop2=True)
        ['flepimop2>=0.1.0']
        >>> _resolve_dependencies(
        ...     ["flepimop2[extra]~=0.1.0"], require_flepimop2=True
        ... )
        ['flepimop2[extra]~=0.1.0']
        >>> _resolve_dependencies(["flepimop2-extra"], require_flepimop2=True)
        ['flepimop2-extra', 'flepimop2']

    """
    dependencies = dependencies or []
    if require_flepimop2:
        pattern = re.compile(r"^flepimop2(\[[^\]]+])?($|[<>=~].*)")
        has_flepimop2 = any(pattern.match(dep.strip()) for dep in dependencies)
        if not has_flepimop2:
            dependencies.append("flepimop2")
    return dependencies


def external_provider_package(
    parent_directory: Path,
    copy_files: dict[Path, Path] | None = None,
    dependencies: list[str] | None = None,
    project_name: str = "example-provider",
    project_requires_python: str = ">=3.11",
) -> str:
    """
    Set up an external provider package and install it into a fresh venv.

    Args:
        parent_directory: Directory in which to set up the provider package and venv.
        copy_files: Optional mapping of source files to destination paths
            within `parent_directory`.
        dependencies: Optional list of dependencies to include in the provider
            package. If omitted, defaults to `["flepimop2"]`.
        project_name: Optional name for the provider package. Defaults to
            "example-provider".
        project_requires_python: Optional Python version specifier for the provider
            package. Defaults to ">=3.11".

    Returns:
        The python executable path from the newly created venv.

    """
    parent_directory = parent_directory.resolve()
    python = _which_python()
    venv_python = _create_venv(python, parent_directory)

    external_provider_root = parent_directory / "external_provider"
    external_provider_root.mkdir(parents=True, exist_ok=True)
    (parent_directory / "model_output").mkdir(parents=True, exist_ok=True)

    dependencies_text = ", ".join(
        f'"{dep}"'
        for dep in _resolve_dependencies(dependencies, require_flepimop2=True)
    )
    pyproject_text = f"""\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{project_name}"
version = "0.0.1"
requires-python = "{project_requires_python}"
dependencies = [{dependencies_text}]

[tool.hatch.build.targets.wheel]
# Ensure implicit namespace packages under flepimop2.* are included.
packages = ["src/flepimop2"]
"""
    (external_provider_root / "pyproject.toml").write_text(pyproject_text)

    # Ensure namespace package directories exist even without __init__.py
    (external_provider_root / "src" / "flepimop2").mkdir(parents=True, exist_ok=True)

    copy_files = copy_files or {}
    for src, dest in copy_files.items():
        dest_path = parent_directory / dest
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(src.read_text())

    subprocess.run(  # noqa: S603
        [
            venv_python,
            "-m",
            "pip",
            "install",
            str(external_provider_root),
        ],
        capture_output=True,
        text=True,
        cwd=parent_directory,
        check=True,
    )
    return venv_python


def project_skeleton(
    parent_directory: Path,
    copy_files: dict[Path, Path] | None = None,
    dependencies: list[str] | None = None,
) -> str:
    """
    Create a project skeleton in ``parent_directory`` and optionally copy files.

    Args:
        parent_directory: Directory in which to create the project skeleton and venv.
        copy_files: Optional mapping of source files to destination paths
            within ``parent_directory``.
        dependencies: Optional list of dependencies to install into the venv.

    Returns:
        The python executable path from the newly created venv.

    """
    parent_directory = parent_directory.resolve()
    python = _which_python()
    venv_python = _create_venv(python, parent_directory)

    if dependencies := _resolve_dependencies(dependencies, require_flepimop2=False):
        subprocess.run(  # noqa: S603
            [venv_python, "-m", "pip", "install", *dependencies],
            capture_output=True,
            text=True,
            cwd=parent_directory,
            check=True,
        )

    flepimop2_run("skeleton", args=[], cwd=parent_directory)

    copy_files = copy_files or {}
    for src, dest in copy_files.items():
        dest_path = parent_directory / dest
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(src.read_text())

    return venv_python


def flepimop2_run(
    action: str,
    args: list[str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    Run a flepimop2 CLI command via subprocess.

    Args:
        action: CLI action name (e.g. "process", "simulate", etc). For a full list of
            available actions, see `flepimop2 --help`.
        args: Additional command arguments to pass to the CLI command.
        cwd: Optional working directory for the command.

    Returns:
        The completed process from running the CLI.

    Raises:
        ValueError: If the action is empty.

    """
    if not action:
        msg = "Action must be a non-empty string"
        raise ValueError(msg)

    args = args or []
    if cwd is not None and ((venv_bin := cwd / ".venv" / "bin" / "flepimop2").exists()):
        command = [str(venv_bin), action, *args]
    else:
        command = ["flepimop2", action, *args]

    return subprocess.run(  # noqa: S603
        command,
        capture_output=True,
        text=True,
        cwd=cwd,
        check=True,
    )
