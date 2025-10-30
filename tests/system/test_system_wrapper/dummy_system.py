"""A dummy stepper function for testing `WrapperSystem`."""

import numpy as np
from numpy.typing import NDArray


def stepper(
    time: float, state: NDArray[np.float64], offset: np.float64
) -> NDArray[np.float64]:
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
