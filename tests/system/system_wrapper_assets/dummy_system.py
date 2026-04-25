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
"""A dummy stepper function for testing `WrapperSystem`."""

import numpy as np

from flepimop2.typing import Float64NDArray


def stepper(time: float, state: Float64NDArray, offset: np.float64) -> Float64NDArray:
    """
    A dummy stepper function for testing purposes: (state + offset) * time.

    Args:
        time: The current time.
        state: The current state array.
        offset: An offset value to be added to the state.

    Returns:
        The updated state array after applying the stepper logic.
    """
    return (state + offset) * time
