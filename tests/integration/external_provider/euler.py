"""Runner function for SIR model integration tests."""

from typing import Any

import numpy as np
from numpy.typing import NDArray

from flepimop2.configuration import IdentifierString, ModuleModel
from flepimop2.engine.abc import EngineABC
from flepimop2.system.abc import SystemProtocol


def runner(
    stepper: SystemProtocol,
    times: NDArray[np.float64],
    state: NDArray[np.float64],
    params: dict[IdentifierString, Any],
    **kwargs: Any,  # noqa: ARG001
) -> NDArray[np.float64]:
    """
    Simple Euler runner for the SIR model.

    Args:
        stepper: The system stepper function.
        times: Array of time points.
        state: The current state array.
        params: Additional parameters for the stepper.
        **kwargs: Additional keyword arguments for the engine. Unused by this runner.

    Returns:
        The evolved time x state array.
    """
    output = np.zeros((len(times), len(state)), dtype=float)
    output[0] = state
    for i, t in enumerate(times[1:]):
        if i == 0:
            continue
        dt = t - times[i - 1]
        dydt = stepper(times[i - 1], output[i - 1], **params)
        output[i] = output[i - 1] + (dydt * dt)
    return np.hstack((times.reshape(-1, 1), output))


class EulerEngine(EngineABC):
    """SIR model runner."""

    def __init__(self) -> None:
        """Initialize the SIR runner with the SIR runner function."""
        self._runner = runner


def build(config: dict[str, Any] | ModuleModel) -> EulerEngine:  # noqa: ARG001
    """
    Build an SIR engine.

    Returns:
        An instance of the SIR engine.
    """
    return EulerEngine()
