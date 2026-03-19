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
"""Tests for `EngineABC` and default `WrapperEngine`."""

import numpy as np
import pytest

from flepimop2.axis import ResolvedShape
from flepimop2.engine.abc import EngineABC
from flepimop2.parameter.abc import ModelStateSpecification, ParameterValue
from flepimop2.system.abc import SystemABC
from flepimop2.system.abc import wrap as system_wrap
from flepimop2.typing import Float64NDArray, StateChangeEnum, as_system_protocol


@as_system_protocol
def sample_step(
    time: np.float64,
    state: Float64NDArray,
    /,
    **kwargs: ParameterValue,
) -> Float64NDArray:
    """
    A simple stepper function for testing purposes.

    Args:
        time: The current time as a float64.
        state: The current state as a numpy array.
        **kwargs: Additional keyword arguments, including `offset`.

    Returns:
        The updated state after applying the stepper logic.
    """
    return (state + kwargs["offset"].item()) * time


DummySystem = system_wrap(sample_step, StateChangeEnum.STATE)


class DummyEngine(EngineABC):
    """A dummy engine for testing purposes."""

    module = "dummy"


@pytest.mark.parametrize("engine", [DummyEngine()])
@pytest.mark.parametrize("system", [DummySystem])
def test_abstraction_error(engine: EngineABC, system: SystemABC) -> None:
    """Test `EngineABC` raises `NotImplementedError` when not overridden."""
    with pytest.raises(NotImplementedError):
        engine.run(
            system,
            np.array([0.0], dtype=np.float64),
            {
                "s0": ParameterValue(np.array(1.0), ResolvedShape()),
                "i0": ParameterValue(np.array(2.0), ResolvedShape()),
                "r0": ParameterValue(np.array(3.0), ResolvedShape()),
            },
            {},
            model_state=ModelStateSpecification(parameter_names=("s0", "i0", "r0")),
        )
