# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Unit tests for `_load_module` function."""

from importlib import import_module
from pathlib import Path
from shutil import copy
from typing import Final
from unittest.mock import patch

import pytest

from flepimop2._utils._module import _load_module

FIXTURE_DIR: Final = Path(__file__).parent / "_load_module_assets"


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


def test_load_module_returns_package_module_for_package_scripts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A script inside an importable package shares that module's state (#339)."""
    package = tmp_path / "wrapperpkg_339"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    script = package / "engine.py"
    script.write_text("STATE: dict[str, int] = {}\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))

    canonical = import_module("wrapperpkg_339.engine")
    loaded = _load_module(script, "flepimop2.engine.wrapped")

    assert loaded is canonical
    canonical.STATE["rtol"] = 1
    assert loaded.STATE == {"rtol": 1}


def test_load_module_keeps_fresh_loading_for_standalone_scripts(tmp_path: Path) -> None:
    """Scripts outside any package are still executed under the given name."""
    script = tmp_path / "standalone_339.py"
    script.write_text("VALUE = 3\n", encoding="utf-8")

    first = _load_module(script, "flepimop2.engine.wrapped")
    second = _load_module(script, "flepimop2.engine.wrapped")

    assert first.__name__ == "flepimop2.engine.wrapped"
    assert first.VALUE == second.VALUE == 3


def test_load_module_falls_back_when_package_import_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A package whose import fails does not block loading the script itself."""
    package = tmp_path / "brokenpkg_339"
    package.mkdir()
    (package / "__init__.py").write_text(
        "raise ImportError('broken')\n", encoding="utf-8"
    )
    script = package / "engine.py"
    script.write_text("VALUE = 5\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))

    loaded = _load_module(script, "flepimop2.engine.wrapped")

    assert loaded.VALUE == 5
    assert loaded.__name__ == "flepimop2.engine.wrapped"
