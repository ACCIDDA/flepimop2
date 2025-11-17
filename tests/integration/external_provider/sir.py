"""Stepper function for SIR model integration tests."""

from typing import Any

import numpy as np
from numpy.typing import NDArray

from flepimop2.configuration._module import ModuleModel
from flepimop2.system.system_base import SystemABC


def stepper(
    time: np.float64,  # noqa: ARG001
    state: NDArray[np.float64],
    *,
    beta: float = 0.3,
    gamma: float = 0.1,
    **kwargs: Any,  # noqa: ARG001
) -> NDArray[np.float64]:
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
