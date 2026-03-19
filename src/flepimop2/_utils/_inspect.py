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

import numpy as np


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
    return annotation is np.ndarray or get_origin(annotation) is np.ndarray
