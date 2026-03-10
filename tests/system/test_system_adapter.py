"""Tests for `SystemABC` and default `AdapterSystem`."""

import numpy as np
import pytest

from flepimop2.system.abc import SystemProtocol, build
from flepimop2.typing import Float64NDArray, with_flow


@with_flow("flow")
def stepper(time: float, state: Float64NDArray, offset: np.float64) -> Float64NDArray:
    """
    A dummy stepper function for testing purposes: (state + offset) * time.

    Args:
        time: The current time.
        state: The current state array.
        offset: An offset value to be added to the state.

    Returns:
        The updated state array after applying the stepper logic.
    """
    return (state + offset) * time


def bad_stepper(
    time: float, state: Float64NDArray, offset: np.float64
) -> Float64NDArray:
    """
    A dummy stepper function for testing purposes, unannotated with flow.

    Args:
        time: The current time.
        state: The current state array.
        offset: An offset value to be added to the state.

    Returns:
        The updated state array after applying the stepper logic.
    """
    return (state + offset) * time


@pytest.mark.parametrize("stepper", [stepper])
def test_wrapper_system(stepper: SystemProtocol) -> None:
    """Test `AdapterSystem` uses a `stepper` function directly."""
    system = build(stepper)
    time = np.float64(1.0)
    offset = 1.0
    init_state = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    result = system.step(time, init_state, offset=offset)
    expected = init_state + offset
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize("stepper", [bad_stepper])
def test_wrapper_system_bad_stepper(stepper: SystemProtocol) -> None:
    """Test `AdapterSystem` raises an error if the stepper is not properly annotated."""
    with pytest.raises(ValueError):
        build(stepper)
