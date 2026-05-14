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
"""Unit tests for `_find_module_class` function."""

from pathlib import Path
from shutil import copy
from typing import Any, Final

import pytest

from flepimop2._utils._module import _find_module_class, _load_module
from flepimop2.module import ModuleBase

FIXTURE_DIR: Final = Path(__file__).parent / "_find_target_class_assets"


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("valid_basemodel.py", "TestModel"),
        ("no_classes.py", None),
    ],
)
def test_find_module_class(tmp_path: Path, fixture: str, expected: str | None) -> None:
    """Test `_find_module_class` returns with various fixtures."""
    module_name = fixture.split(".", maxsplit=1)[0]
    test_file = tmp_path / fixture
    copy(FIXTURE_DIR / fixture, test_file)
    mod = _load_module(test_file, module_name)
    if expected is None:
        with pytest.raises(
            AttributeError,
            match=(rf"Module '{module_name}' does not define a ModuleBase subclass"),
        ):
            _find_module_class(mod, module_name, ModuleBase)
    else:
        target_class: Any = _find_module_class(mod, module_name, ModuleBase)
        assert issubclass(target_class, ModuleBase)
        assert target_class.__name__ == expected
        assert hasattr(target_class, "model_validate")
