"""A dummy stepper function for testing `WrapperSystem`."""

import numpy as np

from flepimop2.typing import Float64NDArray


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
