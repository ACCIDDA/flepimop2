"""Unit tests for `_load_module` function."""

from pathlib import Path
from shutil import copy
from typing import Final
from unittest.mock import patch

import pytest

from flepimop2._utils._module import _load_module

FIXTURE_DIR: Final = Path(__file__).with_suffix("")


def test_load_module_file_not_found(tmp_path: Path) -> None:
    """Test that FileNotFoundError is raised when file doesn't exist."""
    non_existent_file = tmp_path / "does_not_exist.py"
    assert not non_existent_file.exists()
    with pytest.raises(
        FileNotFoundError, match=r"No file found at: .*does_not_exist\.py"
    ):
        _load_module(non_existent_file, "test_module")


def test_load_module_not_python_file(tmp_path: Path) -> None:
    """Test that FileNotFoundError is raised when file is not a Python file."""
    txt_file = tmp_path / "not_python.txt"
    txt_file.write_text("This is not a Python file", encoding="utf-8")
    assert txt_file.exists()
    assert txt_file.suffix != ".py"
    with pytest.raises(
        FileNotFoundError, match=r"No valid Python file found at: .*not_python\.txt"
    ):
        _load_module(txt_file, "test_module")


def test_load_module_import_error(tmp_path: Path) -> None:
    """Test that ImportError is raised when module cannot be loaded from spec."""
    # Create a valid .py file (needed to pass existence and suffix checks)
    test_file = tmp_path / "valid.py"
    test_file.write_text("# Valid Python file", encoding="utf-8")

    # Mock spec_from_file_location to return None to trigger the ImportError path
    # This is an edge case that's difficult to trigger without mocking
    with (
        patch("flepimop2._utils._module.spec_from_file_location", return_value=None),
        pytest.raises(
            ImportError, match=r"Could not load module from spec at: .*valid\.py"
        ),
    ):
        _load_module(test_file, "test_module")


@pytest.mark.parametrize(
    "fixture",
    [
        "simple_module.py",
        "module_with_class.py",
    ],
)
def test_load_module_success(tmp_path: Path, fixture: str) -> None:
    """Test that valid modules are loaded successfully."""
    # Prepare test module
    module_name = fixture.split(".", maxsplit=1)[0]
    test_file = tmp_path / fixture
    copy(FIXTURE_DIR / fixture, test_file)

    # Load module
    mod = _load_module(test_file, module_name)

    # Verify module was loaded
    assert mod is not None
    assert mod.__name__ == module_name
