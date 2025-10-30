"""Tests for `EngineABC` and default `WrapperEngine`."""

from typing import Any, cast

import numpy as np
import pytest
from numpy.typing import NDArray

from flepimop2.engine import EngineABC


def sample_step(
    time: np.float64, state: NDArray[np.float64], **kwargs: Any
) -> NDArray[np.float64]:
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


@pytest.mark.parametrize("engine", [EngineABC()])
def test_abstraction_error(engine: EngineABC) -> None:
    """Test `EngineABC` raises `NotImplementedError` when not overridden."""
    with pytest.raises(NotImplementedError):
        engine._runner(
            sample_step,
            np.array([0.0], dtype=np.float64),
            np.array([1.0, 2.0, 3.0], dtype=np.float64),
            {},
        )
