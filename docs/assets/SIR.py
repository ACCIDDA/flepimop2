"""SIR model plugin for flepimop2 demo."""

import numpy as np

from flepimop2.axis import AxisCollection
from flepimop2.parameter.abc import (
    ModelStateSpecification,
    ParameterValue,
)
from flepimop2.typing import Float64NDArray


def stepper(
    time: float,  # noqa: ARG001
    state: Float64NDArray,
    beta: ParameterValue,
    gamma: ParameterValue,
) -> Float64NDArray:
    """
    Compute dY/dt for the SIR model.

    Args:
        time: The current time (not used in this model, but included for compatibility).
        state: A numpy array containing the current values [S, I, R].
        beta: The infection rate.
        gamma: The recovery rate.

    Returns:
        A numpy array containing the derivatives [dS/dt, dI/dt, dR/dt].

    """
    y_s, y_i, _ = np.asarray(state, dtype=float)
    infection = (beta.item() * y_s * y_i) / np.sum(state)
    recovery = gamma.item() * y_i
    dydt = [-infection, infection - recovery, recovery]
    return np.array(dydt, dtype=float)


def model_state(axes: AxisCollection) -> ModelStateSpecification:  # noqa: ARG001
    """
    Declare how parameter entries assemble the SIR state vector.

    Returns:
        The model-state specification for the SIR system.
    """
    return ModelStateSpecification(
        parameter_names=("s0", "i0", "r0"),
        labels=("S", "I", "R"),
    )
