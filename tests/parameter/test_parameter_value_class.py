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
    """NumPy string arrays nominally satisfy `Array` but are not numeric."""
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


def test_parameter_value_construct_broadcasts_and_preserves_shape() -> None:
    """Construct should create a new ParameterValue with matching backend and shape."""
    template = ParameterValue(
        value=np.array([1.0, 2.0, 3.0]),
        shape=ResolvedShape(axis_names=("age",), sizes=(3,)),
    )
    from_scalar = template.construct(4.5)
    assert isinstance(from_scalar.value, np.ndarray)
    assert from_scalar.shape == template.shape
    np.testing.assert_array_equal(from_scalar.value, [4.5, 4.5, 4.5])

    from_seq = template.construct([10.0, 20.0, 30.0])
    assert isinstance(from_seq.value, np.ndarray)
    np.testing.assert_array_equal(from_seq.value, [10.0, 20.0, 30.0])

    with pytest.raises(ValueError, match="does not match template shape"):
        template.construct([1.0, 2.0])


def test_parameter_value_construct_preserves_jax_backend() -> None:
    """Construct on a JAX-backed template should produce a JAX array."""
    jax = pytest.importorskip("jax", reason="JAX is optional for these tests.")
    template = ParameterValue(
        value=jax.numpy.array([1.0, 2.0]),
        shape=ResolvedShape(axis_names=("group",), sizes=(2,)),
    )
    new_pv = template.construct(7.0)
    assert isinstance(new_pv.value, jax.Array)
    assert new_pv.shape == template.shape
    np.testing.assert_array_equal(np.asarray(new_pv.value), [7.0, 7.0])


def test_parameter_value_from_scalar() -> None:
    """From_scalar should produce a scalar ParameterValue."""
    pv = ParameterValue.from_scalar(3.5)
    assert pv.shape == ResolvedShape()
    assert pv.item() == pytest.approx(3.5)

    jax = pytest.importorskip("jax", reason="JAX is optional for these tests.")
    jax_pv = ParameterValue.from_scalar(2.5, target_type=jax.Array)
    assert isinstance(jax_pv.value, jax.Array)
    assert jax_pv.shape == ResolvedShape()
    assert jax_pv.item() == pytest.approx(2.5)


def test_parameter_value_from_scalar_concrete_jax_type() -> None:
    """Scalar construction honors the concrete type of an existing JAX array."""
    jax = pytest.importorskip("jax")
    target_type = type(jax.numpy.asarray(0.5))
    value = ParameterValue.from_scalar(0.5, target_type=target_type)
    assert isinstance(value.value, target_type)
    assert value.shape == ResolvedShape()
    assert value.item() == pytest.approx(0.5)
