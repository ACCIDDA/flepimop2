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
"""A wrapper-system asset with a stepper only."""

from flepimop2.typing import Float64NDArray


def stepper(
    time: float,  # noqa: ARG001
    state: Float64NDArray,
    beta: float,
    gamma: Float64NDArray,
) -> Float64NDArray:
    """
    A dummy stepper using both scalar and age-indexed parameters.

    Returns:
        The updated state.
    """
    return state + beta + gamma
