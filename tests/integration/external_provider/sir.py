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
"""Stepper function for SIR model integration tests."""

import functools
import sys
from typing import Any, ParamSpec

import numpy as np

from flepimop2.configuration import ModuleModel
from flepimop2.system.abc import SystemABC
from flepimop2.typing import (
    Float64NDArray,
    IdentifierString,
    StateChangeEnum,
    SystemProtocol,
)

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


def sir_stepper(
    time: np.float64,  # noqa: ARG001
    state: Float64NDArray,
    beta: float = 0.3,
    gamma: float = 0.1,
) -> Float64NDArray:
    """
    ODE for an SIR model.

    Args:
        time: Current time (not used in this model).
        state: Current state array [S, I, R].
        beta: The infection rate.
        gamma: The recovery rate.

    Returns:
        Next state array after one step.
    """
    y_s, y_i, _ = np.asarray(state, dtype=float)
    infection = beta * y_s * y_i / np.sum(state)
    recovery = gamma * y_i
    return np.array([-infection, infection - recovery, recovery], dtype=float)


class SirSystem(SystemABC):
    """The SIR model system."""

    module = "flepimop2.system.sir"
    state_change = StateChangeEnum.FLOW

    P = ParamSpec("P")

    @override
    def _bind_impl(
        self, params: dict[IdentifierString, Any] | None = None
    ) -> SystemProtocol:
        return functools.partial(sir_stepper, **(params or {}))


def build(config: dict[str, Any] | ModuleModel) -> SirSystem:  # noqa: ARG001
    """
    Build an SIR system.

    Returns:
        An instance of the SIR system.
    """
    return SirSystem()
