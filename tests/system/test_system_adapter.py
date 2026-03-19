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
"""Tests for `SystemABC` and default `AdapterSystem`."""

import numpy as np
import pytest

from flepimop2.axis import ResolvedShape
from flepimop2.parameter.abc import ParameterValue
from flepimop2.system.abc import SystemProtocol, wrap
from flepimop2.typing import Float64NDArray, StateChangeEnum


def stepper(
    time: np.float64, state: Float64NDArray, offset: ParameterValue
) -> Float64NDArray:
    """
    A dummy stepper function for testing purposes: (state + offset) * time.

    Args:
        time: The current time.
        state: The current state array.
        offset: An offset value to be added to the state.

    Returns:
        The updated state array after applying the stepper logic.
    """
    return (state + offset.item()) * time


@pytest.mark.parametrize("stepper", [stepper])
@pytest.mark.parametrize("state_change", [StateChangeEnum.STATE])
def test_wrapper_system(stepper: SystemProtocol, state_change: StateChangeEnum) -> None:
    """Test `AdapterSystem` uses a `stepper` function directly."""
    system = wrap(stepper, state_change)
    time = np.float64(1.0)
    offset = ParameterValue(np.array(1.0), ResolvedShape())
    init_state = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    result = system.step(time, init_state, offset=offset)
    expected = (init_state + offset.item()) * time
    np.testing.assert_array_equal(result, expected)
