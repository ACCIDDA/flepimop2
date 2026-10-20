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
"""Array-backend detection, extensible registration, and conversion helpers."""

__all__ = [
    "array_backend",
    "array_namespace",
    "coerce_to",
    "coerce_to_host",
    "namespace_from_type",
    "register_array_backend",
]

import contextlib
from collections.abc import Callable
from importlib import import_module
from importlib.metadata import entry_points
from typing import Any, Final

import numpy as np
from array_api_compat import (  # type: ignore[import-untyped]
    array_namespace as _array_namespace,
)

from flepimop2.typing import Array, ArrayBackend, Float64NDArray

_DEFAULT_BACKENDS: Final[dict[str, str]] = {
    "numpy": "numpy",
    "jax": "jax.numpy",
    "torch": "torch",
}
_CUSTOM_BACKENDS: dict[str, str | Callable[[], Any]] = {}
_CUSTOM_COERCERS: dict[str, Callable[[Array], Array]] = {}
_ENTRY_POINTS_DISCOVERED: bool = False


def array_namespace(value: Array) -> Any:  # noqa: ANN401
    """Return the Array-API-compatible namespace for ``value``.

    ``array-api-compat`` recognizes standard-compliant arrays and native
    arrays such as ``torch.Tensor``. Optional backends remain unloaded until
    an array from that backend is supplied.

    Args:
        value: Numerical array whose namespace should be selected.

    Returns:
        The Array-API-compatible namespace for ``value``.

    Raises:
        TypeError: If ``value`` is not a supported array object.
    """
    try:
        return _array_namespace(value)
    except TypeError as error:
        msg = (
            "flepimop2 numerical inputs must be supported array objects; "
            f"got {type(value).__name__}."
        )
        raise TypeError(msg) from error


def register_array_backend(
    name: str,
    target: str | Callable[[], Any] | None = None,
    *,
    coerce: Callable[[Array], Array] | None = None,
) -> None:
    """Register a custom array backend for conversion and discovery.

    Args:
        name: The identifier for the array backend (e.g. 'cupy', 'mlx').
        target: Dotted module name (e.g. 'cupy.array_api') or a callable
            returning the array namespace module.
        coerce: Optional custom conversion callable that transforms an incoming
            `Array` into the target array representation.
    """
    key = name.strip().lower()
    if target is not None:
        _CUSTOM_BACKENDS[key] = target
    if coerce is not None:
        _CUSTOM_COERCERS[key] = coerce


def _discover_entry_points() -> None:
    """Discover array backend extensions registered via Python entry points."""
    global _ENTRY_POINTS_DISCOVERED  # noqa: PLW0603
    if _ENTRY_POINTS_DISCOVERED:
        return
    _ENTRY_POINTS_DISCOVERED = True
    with contextlib.suppress(Exception):
        eps = entry_points(group="flepimop2.array_backends")
        for ep in eps:
            name = ep.name.strip().lower()
            if name not in _CUSTOM_BACKENDS and name not in _DEFAULT_BACKENDS:
                _CUSTOM_BACKENDS[name] = ep.load


def array_backend(value: Array) -> ArrayBackend | str:
    """Identify the advertised backend of an Array-API value.

    Args:
        value: Array whose namespace should be inspected.

    Returns:
        The recognized backend enum member, custom backend string, or
        `ArrayBackend.ANY` when the namespace cannot be determined.
    """
    _discover_entry_points()
    try:
        namespace = array_namespace(value)
        namespace_parts = getattr(namespace, "__name__", "").split(".")
        root_name = (
            namespace_parts[1]
            if namespace_parts[:1] == ["array_api_compat"] and len(namespace_parts) > 1
            else namespace_parts[0]
        ).lower()
        try:
            return ArrayBackend(root_name)
        except ValueError:
            return root_name or ArrayBackend.ANY
    except (AttributeError, TypeError):
        return ArrayBackend.ANY


def _target_namespace(target: ArrayBackend | str) -> Any:  # noqa: ANN401
    """Import the namespace module for a concrete target backend.

    Args:
        target: The target array backend identifier.

    Returns:
        The imported array namespace module.

    Raises:
        RuntimeError: If the requested backend is not installed.
        ValueError: If `ArrayBackend.ANY` or `'any'` is supplied.
    """
    target_str = str(
        target.value if isinstance(target, ArrayBackend) else target
    ).lower()
    if target_str in {"any", "arraybackend.any"}:
        msg = "ArrayBackend.ANY does not identify a concrete array namespace."
        raise ValueError(msg)

    _discover_entry_points()

    if target_str in _CUSTOM_BACKENDS:
        resolver = _CUSTOM_BACKENDS[target_str]
        if callable(resolver):
            return resolver()
        module_name = resolver
    elif target_str in _DEFAULT_BACKENDS:
        module_name = _DEFAULT_BACKENDS[target_str]
    else:
        module_name = target_str

    try:
        return import_module(module_name)
    except ModuleNotFoundError as exc:
        msg = (
            f"Array backend {target_str!r} is required by the consumer but "
            f"{module_name!r} is not installed."
        )
        raise RuntimeError(msg) from exc


def coerce_to(value: Array, target: ArrayBackend | str) -> Array:
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
    target_str = str(
        target.value if isinstance(target, ArrayBackend) else target
    ).lower()
    if target_str in {"any", "arraybackend.any"}:
        return value

    current = array_backend(value)
    current_str = str(
        current.value if isinstance(current, ArrayBackend) else current
    ).lower()
    if current_str == target_str or current is target:
        return value

    if target_str in _CUSTOM_COERCERS:
        converted = _CUSTOM_COERCERS[target_str](value)
        if not isinstance(converted, Array):
            msg = (
                f"The custom coercer for {target_str!r} returned an object that "
                "does not satisfy flepimop2.typing.Array."
            )
            raise TypeError(msg)
        return converted

    namespace: Any = _target_namespace(target)
    converted = namespace.asarray(value)
    if not isinstance(converted, Array):
        msg = (
            f"The {target_str!r} namespace returned an object that does not "
            "satisfy flepimop2.typing.Array."
        )
        raise TypeError(msg)
    return converted


def coerce_to_host(value: Any) -> Float64NDArray:  # noqa: ANN401
    """Coerce an array or Array-API object to a host NumPy ndarray.

    This ensures that JAX arrays, PyTorch tensors, CuPy arrays, and general
    Array-API arrays are converted to host NumPy float64 arrays for storage
    backends (e.g. CSV or Parquet).

    Args:
        value: Array object returned by engine or process.

    Returns:
        A NumPy ndarray with float64 dtype.
    """
    if isinstance(value, np.ndarray):
        return np.asarray(value, dtype=np.float64)
    if hasattr(value, "detach") and hasattr(value, "cpu") and hasattr(value, "numpy"):
        return np.asarray(value.detach().cpu().numpy(), dtype=np.float64)
    if hasattr(value, "__array__"):
        return np.asarray(value, dtype=np.float64)
    return np.asarray(value, dtype=np.float64)


def namespace_from_type(target_type: type[Array] | None) -> Any:  # noqa: ANN401
    """Return the Array-API namespace module for a target array type.

    Args:
        target_type: Advisory array class (e.g. `numpy.ndarray`, `jax.Array`),
            or None.

    Returns:
        The Array-API namespace module, defaulting to `numpy` if target_type is
        None or unconstrained.
    """
    if target_type is None or target_type is Array:
        return np
    module_root = getattr(target_type, "__module__", "").split(".")[0].lower()
    if module_root in {"", "builtins", "typing", "flepimop2"}:
        return np
    try:
        return _target_namespace(module_root)
    except (ValueError, RuntimeError):
        return np
