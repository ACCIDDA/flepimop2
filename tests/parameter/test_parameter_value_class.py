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
"""Tests for the `ParameterValue` Array-API contract."""

import numpy as np
import pytest

from flepimop2.axis import ResolvedShape
from flepimop2.parameter.abc import ParameterValue
from flepimop2.typing import Array


def test_parameter_value_accepts_numpy_arrays() -> None:
    """A NumPy ndarray should round-trip without coercion or copying."""
    arr = np.array([1.0, 2.0, 3.0])
    pv = ParameterValue(value=arr, shape=ResolvedShape(axis_names=("x",), sizes=(3,)))
    assert pv.value is arr  # no implicit np.asarray copy
    assert isinstance(pv.value, Array)


def test_parameter_value_shape_mismatch_raises() -> None:
    """Mismatched shape should raise ``ValueError`` (existing behaviour)."""
    with pytest.raises(ValueError, match="ParameterValue shape mismatch"):
        ParameterValue(
            value=np.array([1.0, 2.0]),
            shape=ResolvedShape(axis_names=("x",), sizes=(3,)),
        )


def test_parameter_value_accepts_jax_arrays() -> None:
    """JAX arrays should be accepted verbatim, without a host round-trip."""
    jax = pytest.importorskip("jax", reason="JAX is optional for these tests.")
    arr = jax.numpy.array([1.0, 2.0, 3.0])
    pv = ParameterValue(value=arr, shape=ResolvedShape(axis_names=("x",), sizes=(3,)))
    assert type(pv.value).__module__.startswith(("jax", "jaxlib"))
    assert isinstance(pv.value, Array)


def test_parameter_value_under_jax_vmap() -> None:
    """``ParameterValue`` must survive being constructed inside ``jax.vmap``.

    Regression test for the implicit ``np.asarray`` cast in
    ``__post_init__`` that used to raise
    ``TracerArrayConversionError`` when called on a JAX tracer.
    """
    jax = pytest.importorskip("jax", reason="JAX is optional for these tests.")
    jnp = jax.numpy
    shape = ResolvedShape(axis_names=("x",), sizes=(3,))

    def make(arr: Array) -> Array:
        return ParameterValue(value=arr, shape=shape).value

    batched = jnp.stack([jnp.array([1.0, 2.0, 3.0]), jnp.array([4.0, 5.0, 6.0])])
    out = jax.vmap(make)(batched)
    np.testing.assert_array_equal(np.asarray(out), np.asarray(batched))


def test_parameter_value_rejects_string_dtype() -> None:
    """NumPy string arrays satisfy the `Array` protocol nominally but are not numeric."""
    arr = np.array(["a", "b", "c"])
    with pytest.raises(TypeError, match="non-numeric dtype"):
        ParameterValue(
            value=arr,
            shape=ResolvedShape(axis_names=("x",), sizes=(3,)),
        )


def test_parameter_value_rejects_object_dtype() -> None:
    """NumPy object arrays should also be rejected at construction time."""
    arr = np.array([1, 2, 3], dtype=object)
    with pytest.raises(TypeError, match="non-numeric dtype"):
        ParameterValue(
            value=arr,
            shape=ResolvedShape(axis_names=("x",), sizes=(3,)),
        )
