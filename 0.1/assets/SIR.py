"""SIR model plugin for flepimop2 demo."""

import numpy as np

from flepimop2.typing import Float64NDArray


def stepper(
    t: float,  # noqa: ARG001
    y: Float64NDArray,
    beta: float,
    gamma: float,
) -> Float64NDArray:
    """dY/dt for the SIR model."""
    y_s, y_i, _ = np.asarray(y, dtype=float)
    infection = (beta * y_s * y_i) / np.sum(y)
    recovery = gamma * y_i
    dydt = [-infection, infection - recovery, recovery]
    return np.array(dydt, dtype=float)
