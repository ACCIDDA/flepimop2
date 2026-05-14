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
"""Unit tests for `_find_module_class` function with ModuleBase subclasses."""

from pathlib import Path
from shutil import copy
from types import ModuleType
from typing import Any, Final

import pytest

from flepimop2._utils._module import _find_module_class, _load_module
from flepimop2.module import ModuleBase

FIXTURE_DIR: Final = Path(__file__).parent / "_load_builder_assets"


def test_find_module_class_attribute_error_when_no_module_base_subclass() -> None:
    """AttributeError is raised when the module has no ModuleBase subclass."""
    mock_module = ModuleType("test_module")
    with pytest.raises(
        AttributeError,
        match=r"Module 'test_module' does not define a ModuleBase subclass",
    ):
        _find_module_class(mock_module, "test_module", ModuleBase)


def test_find_module_class_finds_modulebase_subclass(tmp_path: Path) -> None:
    """_find_module_class should locate a ModuleBase subclass in a module."""
    fixture_file = tmp_path / "module_with_basemodel.py"
    copy(FIXTURE_DIR / "module_with_basemodel.py", fixture_file)

    mod = _load_module(fixture_file, "module_with_basemodel")
    target_class: Any = _find_module_class(mod, "module_with_basemodel", ModuleBase)

    assert issubclass(target_class, ModuleBase)
    assert hasattr(target_class, "model_validate")
    instance = target_class.model_validate({"name": "test", "value": 42})
    assert instance.name == "test"
    assert instance.value == 42
