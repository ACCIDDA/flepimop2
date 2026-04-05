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

__all__ = [
    "EngineProtocol",
    "Float64NDArray",
    "IdentifierString",
    "RaiseOnMissing",
    "RaiseOnMissingType",
    "StateChangeEnum",
    "SystemProtocol",
]

from collections.abc import Callable
from enum import StrEnum
from keyword import iskeyword
from typing import (
    Annotated,
    Any,
    Concatenate,
    Final,
    Literal,
    ParamSpec,
    Protocol,
    cast,
    runtime_checkable,
)

import numpy as np
import numpy.typing as npt
from pydantic import AfterValidator, Field

Float64NDArray = npt.NDArray[np.float64]
"""Alias for a NumPy ndarray with float64 data type."""


def _identifier_string(value: str) -> str:
    """
    Validate that a string is a valid identifier string.

    Args:
        value: The string to validate.

    Returns:
        The validated identifier string.

    Raises:
        ValueError: If the string is not a valid identifier.

    Examples:
        >>> from flepimop2.typing import _identifier_string
        >>> _identifier_string("valid_name_123")
        'valid_name_123'
        >>> _identifier_string("A")
        'A'
        >>> _identifier_string("nameWithCaps")
        'nameWithCaps'
        >>> _identifier_string("1invalidStart")
        Traceback (most recent call last):
            ...
        ValueError: '1invalidStart' is not a valid identifier string or is a keyword.
        >>> _identifier_string("invalid char!")
        Traceback (most recent call last):
            ...
        ValueError: 'invalid char!' is not a valid identifier string or is a keyword.
        >>> _identifier_string("")
        Traceback (most recent call last):
            ...
        ValueError: '' is not a valid identifier string or is a keyword.
        >>> _identifier_string("def")
        Traceback (most recent call last):
            ...
        ValueError: 'def' is not a valid identifier string or is a keyword.

    """
    if not value.isidentifier() or iskeyword(value):
        msg = f"'{value}' is not a valid identifier string or is a keyword."
        raise ValueError(msg)
    return value


IdentifierString = Annotated[
    str,
    Field(min_length=1, max_length=255, pattern=r"^[a-z]([a-z0-9\_]*[a-z0-9])?$"),
    AfterValidator(_identifier_string),
]
"""A string type representing a valid identifier for named configuration elements."""


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

    ERROR = "error"
    """
    The state change is mis-specified.
    """


@runtime_checkable
class SystemProtocol(Protocol):
    """Type-definition (Protocol) for system stepper functions."""

    def __call__(
        self, time: np.float64, state: Float64NDArray, **kwargs: Any
    ) -> Float64NDArray:
        """Protocol for system stepper functions."""
        ...


_P = ParamSpec("_P")

_SystemCallable = Callable[Concatenate[np.float64, Float64NDArray, _P], Float64NDArray]


def as_system_protocol(func: _SystemCallable[_P]) -> SystemProtocol:
    """
    Decorator to mark a function as a SystemProtocol.

    Args:
        func: A callable matching the SystemProtocol signature.

    Returns:
        The function cast as SystemProtocol.
    """
    return cast("SystemProtocol", func)


@runtime_checkable
class EngineProtocol(Protocol):
    """Type-definition (Protocol) for engine runner functions."""

    def __call__(
        self,
        stepper: SystemProtocol,
        times: Float64NDArray,
        state: Float64NDArray,
        params: dict[IdentifierString, Any],
        **kwargs: Any,
    ) -> Float64NDArray:
        """Protocol for engine runner functions."""
        ...
