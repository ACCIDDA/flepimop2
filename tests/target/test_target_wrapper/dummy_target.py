"""A dummy stepper function for testing `WrapperSystem`."""

import numpy as np

from flepimop2.typing import Float64NDArray


def evaluator(simulated: Float64NDArray, standard: Float64NDArray) -> Float64NDArray:
    """
    A dummy evaluator function for testing purposes: RMSE(simulated, standard).

    Args:
        simulated: The simulated state array.
        standard: The standard state array.
        state: The current state array.
        offset: An offset value to be added to the state.

    Returns:
        The updated state array after applying the evaluator logic.
    """
    return np.sqrt(np.mean((simulated - standard) ** 2))
