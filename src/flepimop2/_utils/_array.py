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
"""Array-backend detection and conversion helpers."""

__all__ = ["array_backend", "coerce_to"]

from importlib import import_module
from typing import Any

from flepimop2.typing import Array, ArrayBackend


def array_backend(value: Array) -> ArrayBackend:
    """Identify the advertised backend of an Array-API value.

    Args:
        value: Array whose namespace should be inspected.

    Returns:
        The recognized backend, or `ArrayBackend.ANY` when the namespace is
        valid but is not one of the explicitly supported backends.
    """
    namespace: Any = value.__array_namespace__()
    namespace_name = getattr(namespace, "__name__", "")
    root_name = namespace_name.partition(".")[0]
    try:
        return ArrayBackend(root_name)
    except ValueError:
        return ArrayBackend.ANY


def _target_namespace(target: ArrayBackend) -> Any:  # noqa: ANN401
    """Import the namespace module for a concrete target backend.

    Returns:
        The imported array namespace module.

    Raises:
        RuntimeError: If the requested optional backend is not installed.
        ValueError: If `ArrayBackend.ANY` is supplied as a concrete target.
    """
    if target is ArrayBackend.ANY:
        msg = "ArrayBackend.ANY does not identify a concrete array namespace."
        raise ValueError(msg)

    module_name = {
        ArrayBackend.NUMPY: "numpy",
        ArrayBackend.JAX: "jax.numpy",
        ArrayBackend.TORCH: "torch",
    }[target]
    try:
        return import_module(module_name)
    except ModuleNotFoundError as exc:
        msg = (
            f"Array backend {target.value!r} is required by the consumer but "
            f"{module_name!r} is not installed."
        )
        raise RuntimeError(msg) from exc


def coerce_to(value: Array, target: ArrayBackend) -> Array:
    """Convert an array to a consumer's advertised backend at one seam.

    Identity is preserved when the consumer accepts any backend or the value is
    already in the requested namespace. This avoids copies and, importantly,
    avoids attempting to materialize tracer-bearing arrays on the host.

    Args:
        value: Array supplied by a producer.
        target: Backend advertised by the consumer.

    Returns:
        The original value or an array created by the target namespace.

    Raises:
        TypeError: If the target namespace does not produce an `Array`.
    """
    if target is ArrayBackend.ANY or array_backend(value) is target:
        return value

    namespace: Any = _target_namespace(target)
    converted = namespace.asarray(value)
    if not isinstance(converted, Array):
        msg = (
            f"The {target.value!r} namespace returned an object that does not "
            "satisfy flepimop2.typing.Array."
        )
        raise TypeError(msg)
    return converted
