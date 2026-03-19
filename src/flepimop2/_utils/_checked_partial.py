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
import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

from flepimop2.typing import IdentifierString

T = TypeVar("T")


def _consolidate_args(
    forbidden: set[IdentifierString] | None = None,
    params: dict[IdentifierString, Any] | None = None,
    **kwargs: Any,
) -> dict[IdentifierString, Any]:
    """
    Bind static parameters to a callable, checking their validity.

    Args:
        forbidden: A set of parameter names that are not allowed to be bound.
        params: A dictionary of parameters to statically define for the System.
        **kwargs: Additional parameters to statically define for the System.

    Returns:
        A dictionary of consolidated arguments.

    Raises:
        TypeError: If offered forbidden keys.

    Examples:
        >>> _consolidate_args(forbidden={"b"}, params={"a": 1.0}, c=5.0)
        {'a': 1.0, 'c': 5.0}
        >>> _consolidate_args(forbidden={"b"}, a=1.0, c=5.0)
        {'a': 1.0, 'c': 5.0}
        >>> _consolidate_args(forbidden={"b"}, params={"a": 1.0, "c": 5.0})
        {'a': 1.0, 'c': 5.0}
        >>> _consolidate_args(forbidden={"b"}, params={"b": 2.0})
        Traceback (most recent call last):
            ...
        TypeError: Consolidating static parameters failed.
        Cannot bind forbidden keys: {'b'}; offered keys: {'b'}.
        >>> _consolidate_args(params={"a": 1.0}, c=5.0, a=2.0)
        Traceback (most recent call last):
            ...
        TypeError: Consolidating static parameters failed.
        Cannot offer overlapping keys in params and kwargs: {'a'}.
    """
    validation_errors: list[str] = []

    params = params or {}
    # confirm that kwargs and params do not have overlapping keys
    if overlapping_keys := set(params.keys()).intersection(kwargs.keys()):
        msg = f"Cannot offer overlapping keys in params and kwargs: {overlapping_keys}."
        validation_errors.append(msg)

    combined_params = {**params, **kwargs}

    offered_keys = set(combined_params.keys())
    if not offered_keys:
        return {}

    forbidden = forbidden or set()

    # Validate that forbidden keys are not offered
    if forbidden.intersection(offered_keys):
        msg = f"Cannot bind forbidden keys: {forbidden}; offered keys: {offered_keys}."
        validation_errors.append(msg)

    if validation_errors:
        validation_errors = [
            "Consolidating static parameters failed.",
            *validation_errors,
        ]
        raise TypeError("\n".join(validation_errors))

    return combined_params


def _checked_partial(
    func: Callable[..., T],
    params: dict[IdentifierString, Any] | None = None,
) -> Callable[..., T]:
    """
    Bind static parameters to a callable, checking their validity.

    Args:
        func: The callable to bind parameters to.
        params: A dictionary of parameters to statically define for the System.

    Returns:
        A partial function with static parameters bound.

    Raises:
        TypeError: If offered forbidden keys, keys not in `func` signature, or
            keys with values of incompatible types with `func` signature.

    Examples:
        >>> def example_func(a: float, b: list[float], c: float) -> float:
        ...     return sum([a, c, *b])
        >>> new_func = _checked_partial(example_func, {"c": 5.0})
        >>> new_func(a=1.0, b=[1.0, 2.0, 3.0])
        12.0
    """
    if params is None:
        return func

    offered_keys = set(params.keys())
    if not offered_keys:
        return func

    validation_errors: list[str] = []

    # Validate that offered keys are in the func signature
    signature = inspect.signature(func)
    signature_keys = set(signature.parameters.keys())
    if invalid_keys := offered_keys - signature_keys:
        msg = (
            "Offered keys are not in func signature: "
            f"{invalid_keys}. Signature parameters are: "
            f"{signature_keys}."
        )
        validation_errors.append(msg)

    # Validate parameter value types against signature annotations
    for key, value in signature.parameters.items():
        if key in offered_keys:
            expected_type = value.annotation
            if (
                expected_type is not inspect.Parameter.empty
                and expected_type is not Any
            ):
                try:
                    if isinstance(expected_type, type) and isinstance(
                        params[key], expected_type
                    ):
                        continue
                    casted_value = expected_type(params[key])
                    params[key] = casted_value
                except (ValueError, TypeError) as e:
                    offered_type = type(params[key])
                    msg = (
                        f"Parameter '{key}' (type {offered_type.__name__}) "
                        f"could not be cast to {expected_type.__name__}. Error: {e!s}"
                    )
                    validation_errors.append(msg)

    if validation_errors:
        validation_errors = [
            "Setting static parameters failed.",
            *validation_errors,
        ]
        raise TypeError("\n".join(validation_errors))

    return functools.partial(func, **params)
