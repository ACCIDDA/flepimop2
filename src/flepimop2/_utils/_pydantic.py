"""
Gempyor specific Pydantic extensions.

This module contains functions that are useful for working with and creating Pydantic
models.
"""

__all__ = ()


from typing import Annotated, TypeVar

import numpy as np
from numpy.typing import NDArray
from pydantic import Field, StringConstraints

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


def _to_np_array(value: RangeSpec) -> NDArray[np.float64]:
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
