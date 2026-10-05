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
"""SIR system implementation."""

from typing import Any

import numpy as np
from pydantic import PrivateAttr

from flepimop2.parameter.abc import ParameterValue
from flepimop2.system.abc import SystemABC, SystemProtocol
from flepimop2.typing import Float64NDArray, StateChangeEnum


def global_sir(
    time: np.float64,  # noqa: ARG001
    state: Float64NDArray,
    beta: ParameterValue,
    gamma: ParameterValue,
) -> Float64NDArray:
    """
    SIR model stepper function.

    Args:
        time: Current time point (unused in this autonomous system).
        state: Array of [S, I, R] populations.
        beta: Transmission rate.
        gamma: Recovery rate.

    Returns:
        Array of state derivatives [dS/dt, dI/dt, dR/dt].
    """
    return np.array([
        -beta.item() * state[0] * state[1],
        beta.item() * state[0] * state[1] - gamma.item() * state[1],
        gamma.item() * state[1],
    ])


class SirSystem(SystemABC, module="sir"):
    """SIR model system."""

    state_change: StateChangeEnum = StateChangeEnum.FLOW

    _stepper: SystemProtocol = PrivateAttr(default=None)

    def model_post_init(self, __context: Any, /) -> None:  # noqa: ANN401
        """Set the stepper function after model initialization."""
        super().model_post_init(__context)
        self.__pydantic_private__["_stepper"] = global_sir
