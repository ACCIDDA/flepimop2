"""Tests for `EngineABC` and default `WrapperEngine`."""

from typing import Any, cast

import numpy as np
import pytest

from flepimop2.engine.abc import EngineABC
from flepimop2.system.abc import SystemABC
from flepimop2.typing import Float64NDArray, StateChangeEnum


class DummySystem(SystemABC):
    """A dummy system for testing purposes."""

    module = "dummy"
    state_change = StateChangeEnum.FLOW


class DummyEngine(EngineABC):
    """A dummy engine for testing purposes."""

    module = "dummy"


def sample_step(
    time: np.float64, state: Float64NDArray, **kwargs: Any
) -> Float64NDArray:
    """
    A simple stepper function for testing purposes.

    Args:
        time: The current time as a float64.
        state: The current state as a numpy array.
        **kwargs: Additional keyword arguments, including 'offset'.

    Returns:
        The updated state after applying the stepper logic.
    """
    return (state + cast("float", kwargs["offset"])) * time


@pytest.mark.parametrize("engine", [DummyEngine()])
def test_abstraction_error(engine: EngineABC) -> None:
    """Test `EngineABC` raises `NotImplementedError` when not overridden."""
    system = DummySystem()
    system._stepper = sample_step
    with pytest.raises(NotImplementedError):
        engine.run(
            system,
            np.array([0.0], dtype=np.float64),
            np.array([1.0, 2.0, 3.0], dtype=np.float64),
            {},
        )
