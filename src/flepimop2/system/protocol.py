"""Type-definition (Protocol) for system stepper functions."""

from typing import Any, Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray

__all__ = ["SystemProtocol"]


@runtime_checkable
class SystemProtocol(Protocol):
    """Type-definition (Protocol) for system stepper functions."""

    def __call__(
        self, time: np.float64, state: NDArray[np.float64], **kwargs: Any
    ) -> NDArray[np.float64]:
        """Protocol for system stepper functions.

        Args:
            time: The current time.
            state: The current state array.
            **kwargs: Additional keyword arguments for the stepper.

        Returns:
            The next state array after one step.
        """
        ...
