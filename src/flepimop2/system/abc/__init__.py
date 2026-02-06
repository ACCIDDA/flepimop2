"""Abstract class for Dynamic Systems."""

from typing import Any, Protocol, runtime_checkable

import numpy as np

from flepimop2._utils._module import _build
from flepimop2.configuration import ModuleModel
from flepimop2.typing import Float64NDArray


@runtime_checkable
class SystemProtocol(Protocol):
    """Type-definition (Protocol) for system stepper functions."""

    def __call__(
        self, time: np.float64, state: Float64NDArray, **kwargs: Any
    ) -> Float64NDArray:
        """Protocol for system stepper functions."""
        ...


def _no_step_function(
    time: np.float64,
    state: Float64NDArray,
    **kwargs: Any,
) -> Float64NDArray:
    msg = "SystemABC::stepper must be provided by a concrete implementation."
    raise NotImplementedError(msg)


class SystemABC:
    """Abstract class for Dynamic Systems."""

    _stepper: SystemProtocol

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        """
        Initialize the SystemABC.

        The default initialization sets the stepper to a no-op function. Concrete
        implementations should override this with a valid stepper function.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        self._stepper = _no_step_function

    def step(
        self, time: np.float64, state: Float64NDArray, **params: Any
    ) -> Float64NDArray:
        """
        Perform a single step of the system's dynamics.

        Args:
            time: The current time.
            state: The current state array.
            **params: Additional parameters for the stepper.

        Returns:
            The next state array after one step.
        """
        return self._stepper(time, state, **params)


def build(config: dict[str, Any] | ModuleModel) -> SystemABC:
    """
    Build a `SystemABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance.

    Returns:
        The constructed system instance.

    """
    return _build(config, "system", "flepimop2.system.wrapper", SystemABC)
