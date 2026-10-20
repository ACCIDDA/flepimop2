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
"""Tests for inspection utilities."""

from typing import Annotated

import numpy as np
import numpy.typing as npt
import pytest

from flepimop2._utils._inspect import (
    _is_array_annotation,
    _is_ndarray_annotation,
    _unwrap_annotation,
)
from flepimop2.typing import Array, Float64NDArray


def test_unwrap_annotation() -> None:
    """_unwrap_annotation peels Annotated wrappers."""
    assert _unwrap_annotation(float) is float
    assert _unwrap_annotation(Annotated[float, "units"]) is float
    assert _unwrap_annotation(Annotated[Annotated[int, "a"], "b"]) is int


def test_is_ndarray_annotation() -> None:
    """_is_ndarray_annotation recognizes numpy ndarray annotations."""
    assert _is_ndarray_annotation(np.ndarray) is True
    assert _is_ndarray_annotation(npt.NDArray) is True
    assert _is_ndarray_annotation(Float64NDArray) is True
    assert _is_ndarray_annotation(Annotated[np.ndarray, "note"]) is True
    assert _is_ndarray_annotation(float) is False
    assert _is_ndarray_annotation(Array) is False


def test_is_array_annotation() -> None:
    """_is_array_annotation recognizes Array, ndarray, and backend types."""
    assert _is_array_annotation(Array) is True
    assert _is_array_annotation(Annotated[Array, "note"]) is True
    assert _is_array_annotation(np.ndarray) is True
    assert _is_array_annotation(Float64NDArray) is True
    assert _is_array_annotation(float) is False
    assert _is_array_annotation(int) is False
    assert _is_array_annotation(list[float]) is False

    jax = pytest.importorskip("jax")
    assert _is_array_annotation(jax.Array) is True
