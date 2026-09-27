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

import subprocess  # noqa: S404
import sys

import jax.numpy as jnp
import numpy as np
import pytest

from flepimop2._utils._array import array_backend, coerce_to
from flepimop2.typing import Array, ArrayBackend


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


def test_raw_torch_backend_when_available() -> None:
    """Raw Torch tensors participate through the compatibility namespace."""
    torch = pytest.importorskip("torch")
    value = torch.asarray([1.0, 2.0])

    assert isinstance(value, Array)
    assert array_backend(value) is ArrayBackend.TORCH
    assert coerce_to(value, ArrayBackend.TORCH) is value


def test_numpy_discovery_does_not_import_optional_backends() -> None:
    """Inspecting NumPy must not eagerly import JAX or Torch."""
    code = """
import sys
import numpy as np
from flepimop2._utils._array import array_backend
array_backend(np.asarray([1.0]))
print(int("jax" in sys.modules), int("torch" in sys.modules))
"""
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "0 0"
