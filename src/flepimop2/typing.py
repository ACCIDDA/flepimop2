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

from enum import StrEnum
from typing import Final, Literal

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
