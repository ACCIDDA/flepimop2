"""SIR model plugin for flepimop2 demo."""

import numpy as np
from numpy.typing import NDArray


def stepper(
    t: float,  # noqa: ARG001
    y: NDArray[np.float64],
    beta: float,
    gamma: float,
) -> NDArray[np.float64]:
    """dY/dt for the SIR model."""
    y_s, y_i, _ = np.asarray(y, dtype=float)
    infection = (beta * y_s * y_i) / np.sum(y)
    recovery = gamma * y_i
    dydt = [-infection, infection - recovery, recovery]
    return np.array(dydt, dtype=float)
