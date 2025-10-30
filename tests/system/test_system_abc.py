"""Tests for `SystemABC` and default `WrapperSystem`."""

from typing import Any, cast

import numpy as np
import pytest
from numpy.typing import NDArray

import flepimop2.system as system_module
from flepimop2.system import SystemABC


def stepper(
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


@pytest.mark.parametrize("system", [SystemABC()])
def test_abstraction_error(system: SystemABC) -> None:
    """Test `SystemABC` raises `NotImplementedError` when not overridden."""
    with pytest.raises(NotImplementedError):
        system.step(np.float64(0.0), np.array([1.0, 2.0, 3.0], dtype=np.float64))


def test_build_with_protocol() -> None:
    """Test `build` constructs a `SystemABC` when given a `SystemProtocol`."""
    system = system_module.build(stepper)
    result = system.step(
        np.float64(1.0), np.array([1.0, 2.0, 3.0], dtype=np.float64), offset=1.0
    )
    expected = np.array([2.0, 3.0, 4.0], dtype=np.float64)
    np.testing.assert_array_equal(result, expected)
