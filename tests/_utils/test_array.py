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
"""Tests for array-backend detection and conversion."""

import jax.numpy as jnp
import numpy as np
import pytest

from flepimop2._utils._array import (
    array_backend,
    coerce_to,
    coerce_to_host,
    register_array_backend,
)
from flepimop2.typing import ArrayBackend


def test_numpy_backend_detection_and_identity() -> None:
    """NumPy arrays already accepted by a NumPy consumer must not be copied."""
    value = np.asarray([1.0, 2.0])

    assert array_backend(value) is ArrayBackend.NUMPY
    assert coerce_to(value, ArrayBackend.NUMPY) is value
    assert coerce_to(value, ArrayBackend.ANY) is value


def test_jax_backend_detection_and_identity() -> None:
    """JAX arrays already accepted by a JAX consumer must not be copied."""
    value = jnp.asarray([1.0, 2.0])

    assert array_backend(value) is ArrayBackend.JAX
    assert coerce_to(value, ArrayBackend.JAX) is value
    assert coerce_to(value, ArrayBackend.ANY) is value


def test_numpy_to_jax_conversion() -> None:
    """The target namespace should own cross-backend conversion."""
    converted = coerce_to(np.asarray([1.0, 2.0]), ArrayBackend.JAX)

    assert array_backend(converted) is ArrayBackend.JAX
    np.testing.assert_array_equal(np.asarray(converted), np.asarray([1.0, 2.0]))


def test_jax_to_numpy_conversion() -> None:
    """A NumPy consumer should receive a concrete NumPy array."""
    converted = coerce_to(jnp.asarray([1.0, 2.0]), ArrayBackend.NUMPY)

    assert array_backend(converted) is ArrayBackend.NUMPY
    np.testing.assert_array_equal(converted, np.asarray([1.0, 2.0]))


def test_torch_backend_when_available() -> None:
    """PyTorch participates when its Array-API marker is available."""
    torch = pytest.importorskip("torch")
    value = torch.asarray([1.0, 2.0])
    if not hasattr(value, "__array_namespace__"):
        pytest.skip("Installed PyTorch does not expose __array_namespace__.")

    assert array_backend(value) is ArrayBackend.TORCH
    assert coerce_to(value, ArrayBackend.TORCH) is value


def test_custom_backend_registration_and_coercion() -> None:
    """External packages can register custom backend namespaces and coercers."""
    register_array_backend(
        "custom_test_backend",
        coerce=lambda val: np.asarray(val) * 2.0,
    )

    input_arr = np.asarray([1.0, 2.0])
    coerced = coerce_to(input_arr, "custom_test_backend")
    np.testing.assert_array_equal(coerced, np.asarray([2.0, 4.0]))


def test_coerce_to_host_converts_jax_and_numpy_to_ndarray() -> None:
    """coerce_to_host converts arrays to NumPy float64 ndarrays."""
    np_val = np.asarray([1.0, 2.0], dtype=np.float32)
    host_np = coerce_to_host(np_val)
    assert isinstance(host_np, np.ndarray)
    assert host_np.dtype == np.float64
    np.testing.assert_array_equal(host_np, [1.0, 2.0])

    jax_val = jnp.asarray([3.0, 4.0])
    host_jax = coerce_to_host(jax_val)
    assert isinstance(host_jax, np.ndarray)
    assert host_jax.dtype == np.float64
    np.testing.assert_array_equal(host_jax, [3.0, 4.0])
