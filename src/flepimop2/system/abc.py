"""Abstract class for Dynamic Systems."""

from abc import ABC
from typing import Any

import numpy as np
from numpy.typing import NDArray

from flepimop2._utils import _load_builder
from flepimop2.system.protocol import SystemProtocol


def _no_step_function(
    time: np.float64,
    state: NDArray[np.float64],
    **kwargs: Any,
) -> NDArray[np.float64]:
    msg = "SystemABC::stepper must be provided by a concrete implementation."
    raise NotImplementedError(msg)


class SystemABC(ABC):
    """Abstract class for Dynamic Systems."""

    # f(t, Y, params) -> dYdt
    _stepper: SystemProtocol

    def __init__(self, f: SystemProtocol = _no_step_function) -> None:
        """
        Initialize a `SystemABC` from a stepper function.

        Args:
            f: The stepper function for the system. Defaults to a function that
                raises `NotImplementedError`.
        """
        self.stepper = f

    def step(
        self, time: np.float64, state: NDArray[np.float64], **params: Any
    ) -> NDArray[np.float64]:
        """
        Perform a single step of the system's dynamics.

        Args:
            time: The current time.
            state: The current state array.
            **params: Additional parameters for the stepper.

        Returns:
            The next state array after one step.
        """
        return self.stepper(time, state, **params)


def build(config: dict[str, Any] | SystemProtocol) -> SystemABC:
    """
    Build a `SystemABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a SystemProtocol. In dict mode, it contains
            a 'module' key, it will be used to lookup the System module path. The module
            will have "flepimop2.system." prepended.

    Returns:
        The constructed system.

    Raises:
        TypeError: If the built system is not an instance of SystemABC.
    """
    if isinstance(config, SystemProtocol):
        return SystemABC(config)
    builder = _load_builder(f"flepimop2.system.{config.pop('module', 'wrapper')}")
    system = builder.build(**config)
    if not isinstance(system, SystemABC):
        msg = "The built system is not an instance of SystemABC."
        raise TypeError(msg)
    return system
