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
"""A dummy stepper function for testing `WrapperEngine`."""

from typing import Any

import numpy as np

from flepimop2.system.abc import SystemProtocol
from flepimop2.typing import Float64NDArray, IdentifierString


def runner(
    f: SystemProtocol,
    times: Float64NDArray,
    state: Float64NDArray,
    params: dict[IdentifierString, Any],
    *,
    accumulate: bool,
) -> Float64NDArray:
    """
    A dummy runner function for testing purposes: only evaluates stepper at times.

    Args:
        f: The stepper function.
        times: Array of time points.
        state: The current state array.
        params: Additional parameters for the stepper.
        accumulate: Whether to accumulate results over time.

    Returns:
        The state array evaluated at each time point.
    """
    # numpy array to hold results - first column time, rest state
    res = np.zeros((len(times), len(state) + 1), dtype=np.float64)
    res[:, 0] = times
    res[0, 1:] = state
    for i, t in enumerate(times[1:]):
        if accumulate:
            res[i + 1, 1:] = res[i, 1:]
        res[i + 1, 1:] += f(t, res[i, 1:], **params)
    return res
