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
"""Tests `SystemABC` ability to bind static parameters."""

from pathlib import Path

import numpy as np
import pytest

from flepimop2.axis import ResolvedShape
from flepimop2.parameter.abc import ParameterValue
from flepimop2.system.abc import SystemABC, build
from flepimop2.typing import StateChangeEnum

TEST_SCRIPT = Path(__file__).parent / "system_wrapper_assets" / "dummy_system.py"
system = build({"script": TEST_SCRIPT, "state_change": StateChangeEnum.DELTA})

par = pytest.mark.parametrize("test_system", [system])


@par
def test_set_valid_static_parameters(test_system: SystemABC) -> None:
    """Confirm no errors when setting all valid parameters."""
    offset = ParameterValue(np.array(5.0), ResolvedShape())
    time = np.float64(1.0)
    initial_state = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    newproto = test_system.bind(offset=offset)
    assert all(newproto(time, initial_state) == (initial_state + offset.item()))
    doubled = ParameterValue(np.array(offset.item() * 2), ResolvedShape())
    newproto = test_system.bind(params={"offset": doubled})
    assert all(newproto(time, initial_state) == (initial_state + doubled.item()))


@par
def test_set_static_parameter_throws_error_on_fixed_state(
    test_system: SystemABC,
) -> None:
    """Confirm error thrown when attempting to fix state parameter."""
    with pytest.raises(TypeError):
        test_system.bind(time=100)
    with pytest.raises(TypeError):
        test_system.bind(state=[1.0, 2.0, 3.0])
    with pytest.raises(TypeError):
        test_system.bind(nonexistent_param=5.0)
    with pytest.raises(TypeError):
        test_system.bind(offset="invalid_string")
