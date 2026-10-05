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
"""Euler engine implementation."""

import sys
from typing import Any, ClassVar

import numpy as np
from pydantic import PrivateAttr

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from flepimop2.engine.abc import EngineABC
from flepimop2.exceptions import ValidationIssue
from flepimop2.parameter.abc import ModelStateSpecification, ParameterValue
from flepimop2.system.abc import SystemABC, SystemProtocol
from flepimop2.typing import (
    ArrayBackend,
    Float64NDArray,
    IdentifierString,
    StateChangeEnum,
)


def runner(
    stepper: SystemProtocol,
    times: Float64NDArray,
    initial_state: dict[IdentifierString, ParameterValue],
    params: dict[IdentifierString, ParameterValue],
    model_state: ModelStateSpecification | None = None,
    **kwargs: Any,  # noqa: ARG001
) -> Float64NDArray:
    """
    Simple Euler runner for the SIR model.

    Args:
        stepper: The system stepper function.
        times: Array of time points.
        initial_state: Structured initial-state parameters.
        params: Additional structured parameters for the stepper.
        model_state: Specification describing how to order the initial state.
        **kwargs: Additional keyword arguments for the engine. Unused by this runner.

    Returns:
        The evolved time x state array.
    """
    state_vector = (
        model_state.vectorize_state(initial_state)
        if model_state
        else np.array([
            initial_state["S0"].item(),
            initial_state["I0"].item(),
            initial_state["R0"].item(),
        ])
    )

    n_times = len(times)
    output = np.empty((n_times, 4))
    output[0, 0] = times[0]
    output[0, 1:] = state_vector

    current_state = state_vector.copy()
    for i in range(1, n_times):
        dt = times[i] - times[i - 1]
        derivatives = stepper(
            time=times[i - 1],
            state=current_state,
            beta=params["beta"],
            gamma=params["gamma"],
        )
        current_state += dt * derivatives
        output[i, 0] = times[i]
        output[i, 1:] = current_state
    return output


class EulerEngine(EngineABC, module="euler"):
    """Euler integration engine."""

    backend: ClassVar[ArrayBackend | str] = ArrayBackend.NUMPY
    _runner: Any = PrivateAttr(default=None)

    def model_post_init(self, __context: Any, /) -> None:  # noqa: ANN401
        """Set the Euler runner function."""
        super().model_post_init(__context)
        self.__pydantic_private__["_runner"] = runner

    @override
    def validate_system(self, system: SystemABC) -> list[ValidationIssue] | None:
        """
        Validation hook for system properties.

        Args:
            system: The system to validate.

        Returns:
            A list of validation issues, or `None` if not implemented.
        """
        if system.state_change != StateChangeEnum.FLOW:
            return [
                ValidationIssue(
                    msg=(
                        "Engine state change type, 'flow', is not "
                        "compatible with system state change type "
                        f"'{system.state_change}'."
                    ),
                    kind="incompatible_system",
                )
            ]
        return None
