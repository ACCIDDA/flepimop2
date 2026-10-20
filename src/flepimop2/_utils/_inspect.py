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
"""Small helpers for inspecting runtime type annotations."""

from typing import Annotated, get_args, get_origin

from flepimop2.typing import Array


def _unwrap_annotation(annotation: object) -> object:
    """
    Strip simple wrappers like `Annotated[...]` from runtime annotations.

    Returns:
        The innermost annotation after peeling supported typing wrappers.

    Examples:
        >>> from typing import Annotated
        >>> _unwrap_annotation(float)
        <class 'float'>
        >>> _unwrap_annotation(Annotated[float, "units"])
        <class 'float'>
        >>> _unwrap_annotation(Annotated[Annotated[int, "a"], "b"])
        <class 'int'>
    """
    while get_origin(annotation) is Annotated:
        annotation = get_args(annotation)[0]
    return annotation


def _is_ndarray_annotation(annotation: object) -> bool:
    """
    Return whether an annotation refers to a NumPy ndarray payload.

    Returns:
        `True` if the annotation is `np.ndarray` or an `Annotated` wrapper around it,
        `False` otherwise.

    Examples:
        >>> import numpy as np
        >>> from typing import Annotated
        >>> _is_ndarray_annotation(np.ndarray)
        True
        >>> import numpy.typing as npt
        >>> _is_ndarray_annotation(npt.NDArray)
        True
        >>> _is_ndarray_annotation(npt.NDArray[np.float64])
        True
        >>> _is_ndarray_annotation(Annotated[np.ndarray, "array payload"])
        True
        >>> _is_ndarray_annotation(
        ...     Annotated[npt.NDArray[np.float64], "array payload"]
        ... )
        True
        >>> _is_ndarray_annotation(list[float])
        False
        >>> _is_ndarray_annotation(float)
        False
    """
    annotation = _unwrap_annotation(annotation)
    candidate = get_origin(annotation) or annotation
    if (
        getattr(candidate, "__name__", "") == "ndarray"
        and getattr(candidate, "__module__", "") == "numpy"
    ):
        return True
    if isinstance(candidate, type):
        return any(
            getattr(b, "__name__", "") == "ndarray"
            and getattr(b, "__module__", "") == "numpy"
            for b in candidate.__mro__
        )
    return False


def _is_array_annotation(annotation: object) -> bool:
    """
    Return whether an annotation refers to an Array or ndarray payload.

    Returns:
        `True` if the annotation refers to `Array`, a concrete `np.ndarray`,
        or an array-protocol compatible payload, `False` otherwise.

    Examples:
        >>> import numpy as np
        >>> from flepimop2.typing import Array, Float64NDArray
        >>> _is_array_annotation(Array)
        True
        >>> _is_array_annotation(np.ndarray)
        True
        >>> _is_array_annotation(Float64NDArray)
        True
        >>> _is_array_annotation(float)
        False
    """
    annotation = _unwrap_annotation(annotation)
    if annotation is Array:
        return True
    if _is_ndarray_annotation(annotation):
        return True
    origin = get_origin(annotation)
    candidate = origin if origin is not None else annotation
    if isinstance(candidate, type):
        module = getattr(candidate, "__module__", "").split(".")[0].lower()
        if module in {"jax", "torch"}:
            return True
        return hasattr(candidate, "shape") and hasattr(candidate, "dtype")
    return False
