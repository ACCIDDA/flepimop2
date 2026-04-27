"""SIR model plugin for flepimop2 demo."""

import numpy as np

from flepimop2.typing import Float64NDArray


def stepper(
    t: float,  # noqa: ARG001
    y: Float64NDArray,
    beta: float,
    gamma: float,
) -> Float64NDArray:
    """
    Compute dY/dt for the SIR model.

    Args:
        t: The current time (not used in this model, but included for compatibility).
        y: A numpy array containing the current values [S, I, R].
        beta: The infection rate.
        gamma: The recovery rate.

    Returns:
        A numpy array containing the derivatives [dS/dt, dI/dt, dR/dt].

    """
    y_s, y_i, _ = np.asarray(y, dtype=float)
    infection = (beta * y_s * y_i) / np.sum(y)
    recovery = gamma * y_i
    dydt = [-infection, infection - recovery, recovery]
    return np.array(dydt, dtype=float)
