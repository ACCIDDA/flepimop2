"""
Gempyor specific Pydantic extensions.

This module contains functions that are useful for working with and creating Pydantic
models.
"""

__all__ = ()


from keyword import iskeyword
from typing import Annotated, TypeVar

import numpy as np
from pydantic import Field, StringConstraints

from flepimop2.typing import Float64NDArray

T = TypeVar("T")

"""A string specifying a range in the format 'start:end' or 'start:step:end'."""
RangeSpec = (
    Annotated[
        str,
        StringConstraints(
            pattern=r"^[+-]?\d+(\.\d+)?(:[+-]?\d+(\.\d+)?){1,2}$", strip_whitespace=True
        ),
    ]
    | Annotated[list[float], Field(min_length=2)]
)


def _ensure_list(value: list[T] | tuple[T] | T | None) -> list[T] | None:
    """
    Ensure that a list, tuple, or single value is returned as a list.

    Args:
        value: A value to ensure is a list.

    Returns:
        A list of the value(s), if the `value` is not None.
    """
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _to_default_dict(value: dict[str, T] | list[T]) -> dict[str, T]:
    """
    Ensure that an argument is a dict by converting a list to { default = list[0]}.

    Args:
        value: A dictionary or single element list of a dictionary to convert.

    Returns:
        A dictionary representation of the input OR the value if not a dict or list,
        in which case any type issues must be triaged elsewhere e.g. by Pydantic
        validation.
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        element = value[0]
        return {"default": element}
    return value


def _to_np_array(value: RangeSpec) -> Float64NDArray:
    """
    Convert a list of floats or a range specification string to a NumPy array.

    Args:
        value: A list of floats or a range specification string.

    Returns:
        A NumPy array of floats.
    """
    if isinstance(value, str):
        parts = [np.float64(part.strip()) for part in value.split(":")]
        start, end = parts[0], parts[-1]
        step = parts[1] if len(parts) == 3 else 1.0
        return np.arange(start, end + step / 2.0, step, dtype=np.float64)
    return np.asarray(value, dtype=np.float64)


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
        >>> from flepimop2._utils._pydantic import _identifier_string
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
