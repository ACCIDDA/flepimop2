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
"""Runner function for SIR model integration tests."""

from collections.abc import Mapping
from typing import Any

import numpy as np

from flepimop2.configuration import ModuleModel
from flepimop2.engine.abc import EngineABC
from flepimop2.parameter.abc import ModelStateSpecification, ParameterValue
from flepimop2.system.abc import SystemProtocol
from flepimop2.typing import Float64NDArray, IdentifierString


def runner(
    stepper: SystemProtocol,
    times: Float64NDArray,
    initial_state: dict[IdentifierString, ParameterValue],
    params: Mapping[IdentifierString, ParameterValue],
    model_state: ModelStateSpecification | None = None,
    **kwargs: Any,  # noqa: ARG001
) -> Float64NDArray:
    """
    Simple Euler runner for the SIR model.

    Args:
        stepper: The system stepper function.
        times: Array of time points.
        initial_state: Structured initial-state entries.
        params: Additional parameters for the stepper.
        model_state: Specification describing how to order the initial-state
            entries into a numeric state array.
        **kwargs: Additional keyword arguments for the engine. Unused by this runner.

    Returns:
        The evolved time x state array.

    Raises:
        ValueError: If `model_state` is not provided.
    """
    if model_state is None:
        msg = "model_state must be provided to assemble the initial state."
        raise ValueError(msg)
    state = np.stack([
        initial_state[name].value for name in model_state.parameter_names
    ]).astype(np.float64)
    flat_size = state.size
    output = np.zeros((len(times), flat_size + 1), dtype=float)
    output[:, 0] = times
    output[0, 1:] = state.reshape(-1)
    current_state = state
    for i, t in enumerate(times[1:], start=1):
        dt = t - times[i - 1]
        dydt = stepper(times[i - 1], current_state, **params)
        current_state += dydt * dt
        output[i, 1:] = current_state.reshape(-1)
    return output


class EulerEngine(EngineABC):
    """SIR model runner."""

    module = "flepimop2.engine.euler"

    def __init__(self) -> None:
        """Initialize the SIR runner with the SIR runner function."""
        self._runner = runner


def build(config: dict[str, Any] | ModuleModel) -> EulerEngine:  # noqa: ARG001
    """
    Build an SIR engine.

    Returns:
        An instance of the SIR engine.
    """
    return EulerEngine()
