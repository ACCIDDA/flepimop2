"""Type-definition (Protocol) for engine runner functions."""

from typing import Any, Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray

from flepimop2.system import SystemProtocol


@runtime_checkable
class EngineProtocol(Protocol):
    """Type-definition (Protocol) for engine runner functions."""

    def __call__(
        self,
        stepper: SystemProtocol,
        times: NDArray[np.float64],
        state: NDArray[np.float64],
        params: dict[str, Any],
        **kwargs: Any,
    ) -> NDArray[np.float64]:
        """
        Protocol for engine runner functions.

        Args:
            stepper: The system stepper function.
            times: Array of time points.
            state: The current state array.
            params: Additional parameters for the stepper.
            **kwargs: Additional keyword arguments for the engine.

        Returns:
            The evolved time x state array.
        """
        ...
