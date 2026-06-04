# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
Custom Typing Helpers.

This module centralizes type aliases used throughout the project and makes
it easy to keep runtime imports lightweight while still providing precise
type information. The goal is to express common shapes and dtypes once,
so internal modules can share consistent, readable annotations without
repeating NumPy typing boilerplate.

Examples:
    >>> from flepimop2.typing import Float64NDArray
    >>> Float64NDArray  # doctest: +ELLIPSIS
    numpy.ndarray[tuple[...], numpy.dtype[numpy.float64]]
"""

__all__ = [
    "Array",
    "ExitCode",
    "Float64NDArray",
    "IdentifierString",
    "PatchConflictMode",
    "RaiseOnMissing",
    "RaiseOnMissingType",
    "StateChangeEnum",
    "SystemProtocol",
]

from collections.abc import Callable
from enum import IntEnum, StrEnum
from keyword import iskeyword
from typing import (
    Annotated,
    Any,
    Concatenate,
    Final,
    Literal,
    ParamSpec,
    Protocol,
    Self,
    cast,
    runtime_checkable,
)

import numpy as np
import numpy.typing as npt
from pydantic import AfterValidator, Field

Float64NDArray = npt.NDArray[np.float64]
"""Alias for a NumPy ndarray with float64 data type."""


@runtime_checkable
class Array(Protocol):
    """
    Minimal Array-API duck type.

    Captures only the surface that `flepimop2` itself touches at
    cross-plugin boundaries: a ``shape`` tuple, a ``dtype``, and the
    ``__array_namespace__`` marker that identifies a value as belonging to
    an `Array-API-compliant <https://data-apis.org/array-api/latest/>`_
    backend (NumPy >= 2.0, JAX >= 0.4.32, PyTorch >= 2.1, CuPy, dask,
    ...).

    Concrete consumers (e.g. an ODE engine) remain free to require a
    specific backend internally; using `Array` at module boundaries lets
    producers and consumers agree on shape without forcing dtype coercion
    or NumPy-only payloads.

    Examples:
        >>> import numpy as np
        >>> from flepimop2.typing import Array
        >>> isinstance(np.zeros((2, 3)), Array)
        True
    """

    @property
    def shape(self) -> tuple[int, ...]:
        """The array's shape."""

    @property
    def dtype(self) -> object:
        """The array's dtype (backend-defined)."""

    def __array_namespace__(self, *, api_version: Any = None) -> object:  # noqa: PLW3201, ANN401
        """Return the Array-API namespace for this array."""

    def item(self) -> Any:  # noqa: ANN401
        """Return a 0-d array as a Python scalar."""


class ExitCode(IntEnum):
    """
    Standard process exit codes used by CLI commands.

    Attributes:
        OKAY: Exit code 0, indicating successful execution.
        GENERAL: Exit code 1, indicating a general error.
        CONFIGURATION: Exit code 3, indicating a configuration related error.
    """

    OKAY = 0
    GENERAL = 1
    CONFIGURATION = 3


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


class PatchConflictMode(StrEnum):
    """
    Strategies for handling overlapping configuration keys during patching.

    Examples:
        >>> from flepimop2.typing import PatchConflictMode
        >>> PatchConflictMode.from_string("merge")
        <PatchConflictMode.MERGE: 'merge'>
        >>> PatchConflictMode.from_string("replace")
        <PatchConflictMode.REPLACE: 'replace'>
        >>> PatchConflictMode.from_string("override")
        Traceback (most recent call last):
            ...
        ValueError: Unknown patch conflict mode 'override'; expected one of: error, merge, replace.
    """  # noqa: E501

    ERROR = "error"
    MERGE = "merge"
    REPLACE = "replace"

    @classmethod
    def from_string(cls, value: str) -> Self:
        """
        Parse a patch conflict mode from its string form.

        Args:
            value: The conflict mode string.

        Returns:
            The parsed `PatchConflictMode`.

        Raises:
            ValueError: If `value` is not a valid patch conflict mode.
        """
        try:
            return cls(value)
        except ValueError as exc:
            modes = ", ".join(sorted(mode.value for mode in cls))
            msg = f"Unknown patch conflict mode {value!r}; expected one of: {modes}."
            raise ValueError(msg) from exc


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
