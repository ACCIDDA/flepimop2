"""Stepper function for SIR model integration tests."""

from typing import Any

import numpy as np

from flepimop2.configuration import ModuleModel
from flepimop2.system.abc import SystemABC
from flepimop2.typing import Float64NDArray, StateChangeEnum


def stepper(
    time: np.float64,  # noqa: ARG001
    state: Float64NDArray,
    *,
    beta: float = 0.3,
    gamma: float = 0.1,
    **kwargs: Any,  # noqa: ARG001
) -> Float64NDArray:
    """
    ODE for an SIR model.

    Args:
        time: Current time (not used in this model).
        state: Current state array [S, I, R].
        beta: The infection rate.
        gamma: The recovery rate.
        **kwargs: Additional parameters (beta, gamma).

    Returns:
        Next state array after one step.
    """
    y_s, y_i, _ = np.asarray(state, dtype=float)
    infection = beta * y_s * y_i / np.sum(state)
    recovery = gamma * y_i
    return np.array([-infection, infection - recovery, recovery], dtype=float)


class SirSystem(SystemABC):
    """SIR model system."""

    module = "flepimop2.system.sir"
    state_change = StateChangeEnum.FLOW

    def __init__(self) -> None:
        """Initialize the SIR system with the SIR stepper."""
        self._stepper = stepper


def build(config: dict[str, Any] | ModuleModel) -> SirSystem:  # noqa: ARG001
    """
    Build an SIR system.

    Returns:
        An instance of the SIR system.
    """
    return SirSystem()
