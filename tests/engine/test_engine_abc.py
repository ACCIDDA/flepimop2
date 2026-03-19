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
