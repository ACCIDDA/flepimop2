"""A wrapper-system asset with a stepper only."""

from flepimop2.typing import Float64NDArray


def stepper(
    time: float,  # noqa: ARG001
    state: Float64NDArray,
    beta: float,
    gamma: Float64NDArray,
) -> Float64NDArray:
    """
    A dummy stepper using both scalar and age-indexed parameters.

    Returns:
        The updated state.
    """
    return state + beta + gamma
