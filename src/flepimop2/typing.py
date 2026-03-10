"""
Custom Typing Helpers.

This module centralizes type aliases used throughout the project and makes
it easy to keep runtime imports lightweight while still providing precise
type information. The goal is to express common shapes and dtypes once,
so internal modules can share consistent, readable annotations without
repeating NumPy typing boilerplate.

Examples:
    >>> from flepimop2.typing import Float64NDArray
    >>> Float64NDArray
    numpy.ndarray[tuple[typing.Any, ...], numpy.dtype[numpy.float64]]
"""

__all__ = ["Float64NDArray", "RaiseOnMissing", "RaiseOnMissingType", "StateChangeEnum"]

from collections.abc import Callable
from enum import StrEnum
from typing import Any, Final, Literal, Protocol, runtime_checkable

import numpy as np
import numpy.typing as npt

Float64NDArray = npt.NDArray[np.float64]
"""Alias for a NumPy ndarray with float64 data type."""


class RaiseOnMissingType:
    """A sentinel type indicating an error should be raised if a value is missing."""

    __slots__ = ()

    def __repr__(self) -> Literal["RaiseOnMissing"]:
        """
        String representation of the `RaiseOnMissingType`.

        Returns:
            The string "RaiseOnMissing".
        """
        return "RaiseOnMissing"

    def __reduce__(self) -> Literal["RaiseOnMissing"]:
        """
        Helper for pickling the `RaiseOnMissingType` singleton.

        Returns:
            The string "RaiseOnMissing".
        """
        return "RaiseOnMissing"


RaiseOnMissing: Final[RaiseOnMissingType] = RaiseOnMissingType()
"""Sentinel value indicating an error should be raised if a value is missing."""


class StateChangeEnum(StrEnum):
    """
    Enumeration of types of state changes in a system.

    Examples:
        >>> from flepimop2.typing import StateChangeEnum
        >>> StateChangeEnum.DELTA
        <StateChangeEnum.DELTA: 'delta'>
        >>> StateChangeEnum.FLOW
        <StateChangeEnum.FLOW: 'flow'>

    """

    DELTA = "delta"
    """
    The state change is described directly by the changes in the state variables,
    i.e. \\( x(t + \\Delta t) = x(t) + \\Delta x \\).
    """

    FLOW = "flow"
    """
    The state change is described directly by the flow rates, or derivatives,
    of the state variables. I.e. \\( dx/dt = f(x, t) \\).
    """

    STATE = "state"
    """
    The state change is described directly by the new state values,
    i.e. \\( x(t + \\Delta t) = x_{new} \\).
    """


@runtime_checkable
class SystemProtocol(Protocol):
    """Type-definition (Protocol) for system stepper functions."""

    def __call__(
        self, time: np.float64, state: Float64NDArray, **kwargs: Any
    ) -> Float64NDArray:
        """Protocol for system stepper functions."""

    state_change: StateChangeEnum
    """The type of state change for this system, if provided."""


def with_flow(
    flow: str | StateChangeEnum,
) -> Callable[[SystemProtocol], SystemProtocol]:
    """
    Decorator to add a `state_change` attribute to a system stepper function.

    Args:
        flow: The type of state change to associate with the stepper function.

    Returns:
        A decorator that adds the `state_change` attribute to SystemProtocols.

    Examples:
        >>> from flepimop2.typing import with_flow, StateChangeEnum
        >>> @with_flow(StateChangeEnum.FLOW)
        ... def my_stepper(time, state, param1):
        ...     # stepper implementation
        ...     pass
        >>> my_stepper.state_change
        <StateChangeEnum.FLOW: 'flow'>
    """
    flow = StateChangeEnum(flow)  # cast to enum if given as string

    def decorator(func: SystemProtocol) -> SystemProtocol:
        func.state_change = flow
        return func

    return decorator
